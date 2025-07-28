"""Data update coordinator for AutoPi integration."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .client import AutoPiClient
from .const import (
    CONF_API_KEY,
    CONF_BASE_URL,
    CONF_SELECTED_VEHICLES,
    CONF_UPDATE_INTERVAL_FAST,
    CONF_UPDATE_INTERVAL_MEDIUM,
    CONF_UPDATE_INTERVAL_SLOW,
    DEFAULT_BASE_URL,
    DEFAULT_UPDATE_INTERVAL_FAST_MINUTES,
    DEFAULT_UPDATE_INTERVAL_MEDIUM_MINUTES,
    DEFAULT_UPDATE_INTERVAL_SLOW_MINUTES,
    DOMAIN,
    UPDATE_RING_FAST,
    UPDATE_RING_MEDIUM,
    UPDATE_RING_SLOW,
)
from .exceptions import (
    AutoPiAPIError,
    AutoPiAuthenticationError,
    AutoPiConnectionError,
)
from .types import AutoPiVehicle, CoordinatorData

_LOGGER = logging.getLogger(__name__)


class AutoPiDataUpdateCoordinator(DataUpdateCoordinator[CoordinatorData]):
    """Class to manage fetching AutoPi data from the API."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        update_ring: str = UPDATE_RING_MEDIUM,
    ) -> None:
        """Initialize the coordinator.

        Args:
            hass: Home Assistant instance
            config_entry: Configuration entry for this integration
            update_ring: Update ring type (fast, medium, slow)
        """
        self.config_entry = config_entry
        self._client: AutoPiClient | None = None
        self._selected_vehicles = set(config_entry.data.get(CONF_SELECTED_VEHICLES, []))
        self._update_ring = update_ring

        # Performance tracking
        self._update_count = 0
        self._total_api_calls = 0
        self._failed_api_calls = 0
        self._last_update_duration: float | None = None
        self._last_api_call_time: float | None = None

        # Get configured intervals from options or use defaults
        options = config_entry.options
        if update_ring == UPDATE_RING_FAST:
            interval_minutes = options.get(
                CONF_UPDATE_INTERVAL_FAST, DEFAULT_UPDATE_INTERVAL_FAST_MINUTES
            )
        elif update_ring == UPDATE_RING_SLOW:
            interval_minutes = options.get(
                CONF_UPDATE_INTERVAL_SLOW, DEFAULT_UPDATE_INTERVAL_SLOW_MINUTES
            )
        else:
            interval_minutes = options.get(
                CONF_UPDATE_INTERVAL_MEDIUM, DEFAULT_UPDATE_INTERVAL_MEDIUM_MINUTES
            )

        update_interval = timedelta(minutes=interval_minutes)

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{config_entry.entry_id}_{update_ring}",
            update_interval=update_interval,
            config_entry=config_entry,
        )

        _LOGGER.debug(
            "AutoPi %s coordinator initialized with %s update interval",
            update_ring,
            update_interval,
        )

    async def _async_update_data(self) -> CoordinatorData:
        """Fetch data from AutoPi API.

        Returns:
            Dictionary mapping vehicle IDs to AutoPiVehicle objects

        Raises:
            UpdateFailed: If data fetching fails
        """
        start_time = self.hass.loop.time()
        self._total_api_calls += 1

        try:
            # Create client if not exists
            if self._client is None:
                session = async_get_clientsession(self.hass)
                self._client = AutoPiClient(
                    session=session,
                    api_key=self.config_entry.data[CONF_API_KEY],
                    base_url=self.config_entry.data.get(
                        CONF_BASE_URL, DEFAULT_BASE_URL
                    ),
                )

            _LOGGER.debug("Fetching vehicle data from AutoPi API")

            # Get all vehicles
            vehicles = await self._client.get_vehicles()

            _LOGGER.info("Received %d vehicles from AutoPi API", len(vehicles))

            # Filter to selected vehicles if specified
            if self._selected_vehicles:
                vehicles = [v for v in vehicles if str(v.id) in self._selected_vehicles]
                _LOGGER.debug("Filtered to %d selected vehicles", len(vehicles))

            # Convert to coordinator data format
            data: CoordinatorData = {str(vehicle.id): vehicle for vehicle in vehicles}

            _LOGGER.debug("Successfully updated data for %d vehicles", len(data))

            # Track successful update
            self._last_update_duration = self.hass.loop.time() - start_time
            self._last_api_call_time = self.hass.loop.time()

            return data

        except AutoPiAuthenticationError as err:
            self._failed_api_calls += 1
            self._last_update_duration = self.hass.loop.time() - start_time
            _LOGGER.error("Authentication error: %s", err)
            # Mark config entry for reauth
            self.config_entry.async_start_reauth(self.hass)
            raise UpdateFailed(f"Authentication failed: {err}") from err

        except AutoPiConnectionError as err:
            self._failed_api_calls += 1
            self._last_update_duration = self.hass.loop.time() - start_time
            _LOGGER.error("Connection error: %s", err)
            raise UpdateFailed(f"Failed to connect to AutoPi API: {err}") from err

        except AutoPiAPIError as err:
            self._failed_api_calls += 1
            self._last_update_duration = self.hass.loop.time() - start_time
            _LOGGER.error("API error: %s", err)
            raise UpdateFailed(f"AutoPi API error: {err}") from err

        except Exception as err:
            self._failed_api_calls += 1
            self._last_update_duration = self.hass.loop.time() - start_time
            _LOGGER.exception("Unexpected error fetching AutoPi data")
            raise UpdateFailed(f"Unexpected error: {err}") from err

    async def async_refresh_with_selected_vehicles(
        self, selected_vehicles: list[str]
    ) -> None:
        """Update selected vehicles and refresh data.

        Args:
            selected_vehicles: List of vehicle IDs to monitor
        """
        _LOGGER.debug(
            "Updating selected vehicles from %s to %s",
            self._selected_vehicles,
            selected_vehicles,
        )

        self._selected_vehicles = set(selected_vehicles)
        await self.async_refresh()

    def get_vehicle_count(self) -> int:
        """Get the total number of vehicles.

        Returns:
            Number of vehicles
        """
        return len(self.data) if self.data else 0

    def get_vehicle(self, vehicle_id: str) -> AutoPiVehicle | None:
        """Get a specific vehicle by ID.

        Args:
            vehicle_id: The vehicle ID

        Returns:
            AutoPiVehicle object or None if not found
        """
        return self.data.get(vehicle_id) if self.data else None

    @property
    def update_ring(self) -> str:
        """Get the update ring type."""
        return self._update_ring

    @property
    def api_call_count(self) -> int:
        """Get the total number of API calls made."""
        return self._total_api_calls

    @property
    def failed_api_call_count(self) -> int:
        """Get the number of failed API calls."""
        return self._failed_api_calls

    @property
    def success_rate(self) -> float:
        """Get the API call success rate as a percentage."""
        if self._total_api_calls == 0:
            return 100.0
        return ((self._total_api_calls - self._failed_api_calls) / self._total_api_calls) * 100

    @property
    def last_update_duration(self) -> float | None:
        """Get the duration of the last update in seconds."""
        return self._last_update_duration


class AutoPiPositionCoordinator(AutoPiDataUpdateCoordinator):
    """Coordinator specifically for fetching vehicle position data."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        base_coordinator: AutoPiDataUpdateCoordinator,
    ) -> None:
        """Initialize the position coordinator.

        Args:
            hass: Home Assistant instance
            config_entry: Configuration entry for this integration
            base_coordinator: Base coordinator to get vehicle data from
        """
        super().__init__(hass, config_entry, UPDATE_RING_FAST)
        self._base_coordinator = base_coordinator

    async def _async_update_data(self) -> CoordinatorData:
        """Fetch position data from AutoPi API.

        Returns:
            Dictionary mapping vehicle IDs to AutoPiVehicle objects with position

        Raises:
            UpdateFailed: If data fetching fails
        """
        start_time = self.hass.loop.time()
        self._total_api_calls += 1
        self._update_count += 1

        try:
            # Get vehicles from base coordinator
            if not self._base_coordinator.data:
                _LOGGER.debug("No vehicle data available from base coordinator")
                return {}

            # Create client if not exists
            if self._client is None:
                session = async_get_clientsession(self.hass)
                self._client = AutoPiClient(
                    session=session,
                    api_key=self.config_entry.data[CONF_API_KEY],
                    base_url=self.config_entry.data.get(
                        CONF_BASE_URL, DEFAULT_BASE_URL
                    ),
                )

            _LOGGER.debug(
                "[%s] Fetching position data for all devices",
                self._update_ring,
            )

            # Fetch all positions in one API call
            all_positions = await self._client.get_all_positions()

            _LOGGER.debug(
                "[%s] Received positions for %d devices",
                self._update_ring,
                len(all_positions),
            )

            # Copy vehicle data from base coordinator and match with positions
            data: CoordinatorData = {}
            position_count = 0

            for vehicle_id, vehicle in self._base_coordinator.data.items():
                # Create a copy of the vehicle data
                vehicle_copy = AutoPiVehicle(
                    id=vehicle.id,
                    name=vehicle.name,
                    license_plate=vehicle.license_plate,
                    vin=vehicle.vin,
                    year=vehicle.year,
                    type=vehicle.type,
                    battery_voltage=vehicle.battery_voltage,
                    devices=vehicle.devices,
                    make_id=vehicle.make_id,
                    model_id=vehicle.model_id,
                    position=None,  # Will be updated below
                )

                # Match position data by device ID
                if vehicle.devices:
                    for device_id in vehicle.devices:
                        if device_id in all_positions:
                            vehicle_copy.position = all_positions[device_id]
                            position_count += 1
                            _LOGGER.debug(
                                "[%s] Got position for vehicle %s (device %s): lat=%.6f, lon=%.6f, alt=%.1fm, %d satellites",
                                self._update_ring,
                                vehicle.name,
                                device_id,
                                vehicle_copy.position.latitude,
                                vehicle_copy.position.longitude,
                                vehicle_copy.position.altitude,
                                vehicle_copy.position.num_satellites,
                            )
                            break  # Use first device with position data
                    else:
                        _LOGGER.debug(
                            "[%s] No position data available for vehicle %s (devices: %s)",
                            self._update_ring,
                            vehicle.name,
                            vehicle.devices,
                        )
                else:
                    _LOGGER.debug(
                        "[%s] Vehicle %s has no devices",
                        self._update_ring,
                        vehicle.name,
                    )

                data[vehicle_id] = vehicle_copy

            # Track successful update
            self._last_update_duration = self.hass.loop.time() - start_time
            self._last_api_call_time = self.hass.loop.time()

            _LOGGER.info(
                "[%s] Successfully updated position data for %d/%d vehicles in %.2fs (update #%d, %.1f%% success rate)",
                self._update_ring,
                position_count,
                len(data),
                self._last_update_duration,
                self._update_count,
                self.success_rate,
            )

            return data

        except Exception as err:
            self._failed_api_calls += 1
            self._last_update_duration = self.hass.loop.time() - start_time
            _LOGGER.error(
                "[%s] Unexpected error fetching position data (update #%d, %.1f%% success rate): %s",
                self._update_ring,
                self._update_count,
                self.success_rate,
                err,
                exc_info=True,
            )
            raise UpdateFailed(f"Failed to fetch position data: {err}") from err
