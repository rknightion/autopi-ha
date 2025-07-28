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
    UPDATE_RING_SLOW,
)
from .exceptions import (
    AutoPiAPIError,
    AutoPiAuthenticationError,
    AutoPiConnectionError,
)
from .types import AutoPiVehicle, CoordinatorData, DataFieldValue, VehiclePosition

_LOGGER = logging.getLogger(__name__)


class AutoPiDataUpdateCoordinator(DataUpdateCoordinator[CoordinatorData]):
    """Class to manage fetching AutoPi data from the API."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        update_ring: str = UPDATE_RING_FAST,
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
    """Coordinator specifically for fetching vehicle position and data field data."""

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
        """Fetch position and data field data from AutoPi API.

        Returns:
            Dictionary mapping vehicle IDs to AutoPiVehicle objects with position and data fields

        Raises:
            UpdateFailed: If data fetching fails
        """
        start_time = self.hass.loop.time()
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
                "[%s] Fetching data fields for all vehicles",
                self._update_ring,
            )

            # Copy vehicle data from base coordinator
            data: CoordinatorData = {}
            data_field_count = 0

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
                    position=None,
                    data_fields={},
                )

                # Fetch data fields for each device
                if vehicle.devices:
                    for device_id in vehicle.devices:
                        try:
                            # Count API calls for each request
                            self._total_api_calls += 1

                            # Fetch data fields
                            fields = await self._client.get_data_fields(device_id, vehicle.id)

                            if fields:
                                # Merge fields from all devices (later devices override earlier ones)
                                vehicle_copy.data_fields = vehicle_copy.data_fields or {}
                                vehicle_copy.data_fields.update(fields)
                                data_field_count += len(fields)

                                # Extract position data from fields if available
                                if "track.pos.loc" in fields and "track.pos.alt" in fields:
                                    try:
                                        loc_field = fields["track.pos.loc"]
                                        if isinstance(loc_field.last_value, dict):
                                            # Construct position from data fields
                                            vehicle_copy.position = VehiclePosition(
                                                timestamp=loc_field.last_seen,
                                                latitude=loc_field.last_value.get("lat", 0),
                                                longitude=loc_field.last_value.get("lon", 0),
                                                altitude=fields.get("track.pos.alt", DataFieldValue(
                                                    field_prefix="", field_name="", frequency=0,
                                                    value_type="", title="", last_seen=loc_field.last_seen,
                                                    last_value=0, description="", last_update=loc_field.last_update
                                                )).last_value,
                                                speed=fields.get("track.pos.sog", DataFieldValue(
                                                    field_prefix="", field_name="", frequency=0,
                                                    value_type="", title="", last_seen=loc_field.last_seen,
                                                    last_value=0, description="", last_update=loc_field.last_update
                                                )).last_value,
                                                course=fields.get("track.pos.cog", DataFieldValue(
                                                    field_prefix="", field_name="", frequency=0,
                                                    value_type="", title="", last_seen=loc_field.last_seen,
                                                    last_value=0, description="", last_update=loc_field.last_update
                                                )).last_value,
                                                num_satellites=fields.get("track.pos.nsat", DataFieldValue(
                                                    field_prefix="", field_name="", frequency=0,
                                                    value_type="", title="", last_seen=loc_field.last_seen,
                                                    last_value=0, description="", last_update=loc_field.last_update
                                                )).last_value,
                                            )
                                            _LOGGER.debug(
                                                "[%s] Extracted position from data fields for vehicle %s",
                                                self._update_ring,
                                                vehicle.name,
                                            )
                                    except Exception as err:
                                        _LOGGER.warning(
                                            "[%s] Failed to extract position from data fields: %s",
                                            self._update_ring,
                                            err,
                                        )

                                _LOGGER.debug(
                                    "[%s] Got %d data fields for vehicle %s (device %s)",
                                    self._update_ring,
                                    len(fields),
                                    vehicle.name,
                                    device_id,
                                )
                            else:
                                _LOGGER.debug(
                                    "[%s] No data fields for vehicle %s (device %s)",
                                    self._update_ring,
                                    vehicle.name,
                                    device_id,
                                )

                        except Exception as err:
                            self._failed_api_calls += 1
                            _LOGGER.warning(
                                "[%s] Failed to fetch data fields for device %s: %s",
                                self._update_ring,
                                device_id,
                                err,
                            )
                            continue
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
                "[%s] Successfully updated data with %d fields for %d vehicles in %.2fs (update #%d, %.1f%% success rate)",
                self._update_ring,
                data_field_count,
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
                "[%s] Unexpected error fetching data fields (update #%d, %.1f%% success rate): %s",
                self._update_ring,
                self._update_count,
                self.success_rate,
                err,
                exc_info=True,
            )
            raise UpdateFailed(f"Failed to fetch data fields: {err}") from err
