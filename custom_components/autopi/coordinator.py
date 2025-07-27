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
    CONF_SCAN_INTERVAL,
    CONF_SELECTED_VEHICLES,
    DEFAULT_BASE_URL,
    DEFAULT_SCAN_INTERVAL_MINUTES,
    DOMAIN,
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
    ) -> None:
        """Initialize the coordinator.

        Args:
            hass: Home Assistant instance
            config_entry: Configuration entry for this integration
        """
        self.config_entry = config_entry
        self._client: AutoPiClient | None = None
        self._selected_vehicles = set(config_entry.data.get(CONF_SELECTED_VEHICLES, []))

        # Performance tracking
        self._total_api_calls = 0
        self._failed_api_calls = 0
        self._last_update_duration: float | None = None
        self._last_api_call_time: float | None = None

        # Get scan interval from config or options
        scan_interval_minutes = (
            config_entry.options.get(CONF_SCAN_INTERVAL)
            or config_entry.data.get(CONF_SCAN_INTERVAL)
            or DEFAULT_SCAN_INTERVAL_MINUTES
        )

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{config_entry.entry_id}",
            update_interval=timedelta(minutes=scan_interval_minutes),
            config_entry=config_entry,
        )

        _LOGGER.debug(
            "AutoPi coordinator initialized with %d minute update interval",
            scan_interval_minutes,
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
