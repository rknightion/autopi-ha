"""Data update coordinator for AutoPi integration."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .client import AutoPiClient
from .const import (
    CONF_API_KEY,
    CONF_BASE_URL,
    CONF_DISCOVERY_ENABLED,
    CONF_SELECTED_VEHICLES,
    CONF_UPDATE_INTERVAL_FAST,
    DEFAULT_BASE_URL,
    DEFAULT_UPDATE_INTERVAL_FAST_MINUTES,
    DOMAIN,
)
from .exceptions import (
    AutoPiAPIError,
    AutoPiAuthenticationError,
    AutoPiConnectionError,
)
from .types import (
    AutoPiEvent,
    AutoPiTrip,
    AutoPiVehicle,
    CoordinatorData,
    DataFieldValue,
    FleetAlert,
    VehiclePosition,
)

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
        self._update_count = 0
        self._total_api_calls = 0
        self._failed_api_calls = 0
        self._last_update_duration: float | None = None
        self._last_api_call_time: float | None = None

        # Fleet-wide data
        self._fleet_alerts: list[FleetAlert] = []
        self._fleet_alerts_total: int = 0
        self._last_alert_ids: set[str] = set()

        # Device events tracking
        self._device_events: dict[str, list[AutoPiEvent]] = {}
        self._last_event_timestamps: dict[str, str] = {}

        # Discovery tracking
        self._all_vehicles: list[AutoPiVehicle] = []
        # Initialize discovered vehicles with already selected vehicles
        self._discovered_vehicles: set[str] = set(self._selected_vehicles)

        # Get configured interval from options or use default
        options = config_entry.options
        interval_minutes = options.get(
            CONF_UPDATE_INTERVAL_FAST, DEFAULT_UPDATE_INTERVAL_FAST_MINUTES
        )

        update_interval = timedelta(minutes=interval_minutes)

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{config_entry.entry_id}",
            update_interval=update_interval,
            config_entry=config_entry,
        )

        _LOGGER.debug(
            "AutoPi coordinator initialized with %s update interval",
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
        self._update_count += 1

        _LOGGER.info(
            "Base coordinator update #%d starting (interval: %s)",
            self._update_count,
            self.update_interval,
        )

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

            self._total_api_calls += 1

            _LOGGER.debug(
                "Starting API update %d (total calls: %d, failed: %d)",
                self._update_count,
                self._total_api_calls,
                self._failed_api_calls,
            )

            # Get all vehicles
            vehicles = await self._client.get_vehicles()

            _LOGGER.debug(
                "Received %d vehicles from API",
                len(vehicles),
            )

            # Store all vehicles for discovery
            self._all_vehicles = vehicles

            # Check for new vehicles not in selected list
            await self._check_for_new_vehicles(vehicles)

            # Check for removed vehicles
            await self._check_for_removed_vehicles(vehicles)

            # Filter to selected vehicles if specified
            if self._selected_vehicles:
                filtered_vehicles = [v for v in vehicles if str(v.id) in self._selected_vehicles]
                _LOGGER.debug(
                    "Filtered to %d selected vehicles (from %d total)",
                    len(filtered_vehicles),
                    len(vehicles),
                )
            else:
                filtered_vehicles = vehicles
                _LOGGER.debug(
                    "No vehicle filter applied, using all %d vehicles",
                    len(vehicles),
                )

            # Convert to coordinator data format
            data: CoordinatorData = {str(vehicle.id): vehicle for vehicle in filtered_vehicles}

            _LOGGER.debug("Successfully updated data for %d vehicles", len(data))

            # Fetch fleet alerts for base coordinator
            try:
                self._total_api_calls += 1
                total_alerts, alerts = await self._client.get_fleet_alerts()
                self._fleet_alerts_total = total_alerts
                self._fleet_alerts = alerts

                # Check for new alerts
                current_alert_ids = {alert.alert_id for alert in alerts}
                new_alert_ids = current_alert_ids - self._last_alert_ids

                if new_alert_ids:
                    # Fire events for new alerts
                    for alert in alerts:
                        if alert.alert_id in new_alert_ids:
                            self._fire_alert_event(alert)

                self._last_alert_ids = current_alert_ids

                _LOGGER.debug("Successfully fetched %d fleet alerts", total_alerts)
            except Exception as err:
                self._failed_api_calls += 1
                _LOGGER.warning("Failed to fetch fleet alerts: %s", err)
                # Continue even if alerts fail

            # Fetch events for each device
            for vehicle in data.values():
                for device_id in vehicle.devices:
                    try:
                        self._total_api_calls += 1
                        events = await self._client.get_device_events(device_id)

                        # Store all events for this device
                        self._device_events[device_id] = events

                        # Check for new events based on timestamp
                        last_timestamp = self._last_event_timestamps.get(device_id)
                        new_events = []

                        if events:
                            # Update last timestamp to the most recent event
                            self._last_event_timestamps[device_id] = events[
                                0
                            ].timestamp.isoformat()

                            # Find new events
                            if last_timestamp:
                                for event in events:
                                    if event.timestamp.isoformat() > last_timestamp:
                                        new_events.append(event)
                            else:
                                # First time fetching events for this device
                                # Don't fire events on startup to avoid old events
                                new_events = []
                                _LOGGER.info(
                                    "Initial event fetch for device %s: found %d events, skipping startup events to avoid replaying old events",
                                    device_id,
                                    len(events),
                                )

                        # Fire events for new events
                        for event in new_events:
                            self._fire_device_event(event, str(vehicle.id))

                        if new_events:
                            _LOGGER.info(
                                "Found %d new events for device %s",
                                len(new_events),
                                device_id,
                            )

                    except Exception as err:
                        self._failed_api_calls += 1
                        _LOGGER.warning(
                            "Failed to fetch events for device %s: %s",
                            device_id,
                            err,
                        )
                        # Continue even if events fail for one device

            # Track successful update
            self._last_update_duration = self.hass.loop.time() - start_time
            self._last_api_call_time = self.hass.loop.time()

            _LOGGER.info(
                "Base coordinator update #%d completed successfully in %.2fs (next update in %s)",
                self._update_count,
                self._last_update_duration,
                self.update_interval,
            )

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

        # Update selected vehicles
        old_selected = self._selected_vehicles
        self._selected_vehicles = set(selected_vehicles)

        # Remove deselected vehicles from discovered set so they can be re-discovered
        deselected = old_selected - self._selected_vehicles
        if deselected:
            self._discovered_vehicles -= deselected
            _LOGGER.debug(
                "Removed %d deselected vehicles from discovered set: %s",
                len(deselected),
                deselected
            )

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
        return (
            (self._total_api_calls - self._failed_api_calls) / self._total_api_calls
        ) * 100

    @property
    def last_update_duration(self) -> float | None:
        """Get the duration of the last update in seconds."""
        return self._last_update_duration

    @property
    def fleet_alerts(self) -> list[FleetAlert]:
        """Get the current fleet alerts."""
        return self._fleet_alerts

    @property
    def fleet_alerts_total(self) -> int:
        """Get the total number of fleet alerts."""
        return self._fleet_alerts_total

    def _fire_alert_event(self, alert: FleetAlert) -> None:
        """Fire an event for a new fleet alert.

        Args:
            alert: The alert data
        """
        event_data = {
            "alert_id": alert.alert_id,
            "title": alert.title,
            "severity": alert.severity,
            "vehicle_count": alert.vehicle_count,
        }

        self.hass.bus.async_fire(
            f"{DOMAIN}_fleet_alert",
            event_data,
        )

        _LOGGER.info(
            "Fired fleet_alert event: %s (severity: %s, affecting %d vehicles)",
            alert.title,
            alert.severity,
            alert.vehicle_count,
        )

    def _fire_device_event(self, event: AutoPiEvent, vehicle_id: str) -> None:
        """Fire an event for a new device event.

        Args:
            event: The event data
            vehicle_id: The vehicle ID associated with the device
        """
        event_data = {
            "device_id": event.device_id,
            "vehicle_id": vehicle_id,
            "timestamp": event.timestamp.isoformat(),
            "tag": event.tag,
            "area": event.area,
            "event_type": event.event_type,
            "data": event.data,
        }

        self.hass.bus.async_fire(
            f"{DOMAIN}_device_event",
            event_data,
        )

        _LOGGER.debug(
            "Fired device_event: %s/%s for device %s",
            event.area,
            event.event_type,
            event.device_id,
        )

    @property
    def device_events(self) -> dict[str, list[AutoPiEvent]]:
        """Get device events."""
        return self._device_events

    def get_device_events(self, device_id: str) -> list[AutoPiEvent]:
        """Get events for a specific device.

        Args:
            device_id: The device ID

        Returns:
            List of events for the device
        """
        return self._device_events.get(device_id, [])

    async def _check_for_new_vehicles(self, vehicles: list[AutoPiVehicle]) -> None:
        """Check for new vehicles and initiate discovery flows.

        Args:
            vehicles: List of all vehicles from the API
        """
        # Check if discovery is enabled
        if not self.config_entry.options.get(CONF_DISCOVERY_ENABLED, True):
            _LOGGER.debug("Vehicle discovery is disabled")
            return

        # Get current selected vehicle IDs
        current_selected = self._selected_vehicles

        # Get all known vehicle IDs (selected + previously discovered)
        known_vehicles = current_selected | self._discovered_vehicles

        # Find new vehicles
        all_vehicle_ids = {str(v.id) for v in vehicles}
        new_vehicle_ids = all_vehicle_ids - known_vehicles

        if new_vehicle_ids:
            _LOGGER.info(
                "Found %d new vehicles: %s",
                len(new_vehicle_ids),
                new_vehicle_ids
            )

            # Add to discovered set
            self._discovered_vehicles.update(new_vehicle_ids)

            # Initiate discovery flow for each new vehicle
            for vehicle_id in new_vehicle_ids:
                vehicle = next((v for v in vehicles if str(v.id) == vehicle_id), None)
                if vehicle:
                    _LOGGER.debug(
                        "Initiating discovery flow for vehicle %s (%s)",
                        vehicle.name,
                        vehicle.license_plate or "No plate"
                    )

                    # Create discovery context
                    discovery_data = {
                        "vehicle_id": str(vehicle.id),
                        "vehicle_name": vehicle.name,
                        "license_plate": vehicle.license_plate,
                        "vin": vehicle.vin,
                        "api_key": self.config_entry.data[CONF_API_KEY],
                        "base_url": self.config_entry.data.get(CONF_BASE_URL, DEFAULT_BASE_URL),
                    }

                    # Initiate discovery flow
                    await self.hass.config_entries.flow.async_init(
                        DOMAIN,
                        context={"source": "discovery"},
                        data=discovery_data,
                    )
        else:
            _LOGGER.debug(
                "No new vehicles found. Total: %d, Selected: %d, Discovered: %d",
                len(vehicles),
                len(current_selected),
                len(self._discovered_vehicles)
            )

    @property
    def all_vehicles(self) -> list[AutoPiVehicle]:
        """Get all vehicles from the API."""
        return self._all_vehicles

    async def _check_for_removed_vehicles(self, vehicles: list[AutoPiVehicle]) -> None:
        """Check for vehicles that have been removed from the API.

        Args:
            vehicles: List of all vehicles from the API
        """
        # Get all vehicle IDs from API
        current_api_vehicle_ids = {str(v.id) for v in vehicles}

        # Find vehicles that are selected but no longer exist in API
        removed_vehicle_ids = self._selected_vehicles - current_api_vehicle_ids

        if removed_vehicle_ids:
            _LOGGER.warning(
                "Found %d vehicles that no longer exist in API: %s",
                len(removed_vehicle_ids),
                removed_vehicle_ids
            )

            # Get device registry
            device_registry = dr.async_get(self.hass)

            # Get entity registry
            entity_registry = er.async_get(self.hass)

            for vehicle_id in removed_vehicle_ids:
                _LOGGER.info(
                    "Removing vehicle %s from selected vehicles as it no longer exists in API",
                    vehicle_id
                )

                # Remove the device and all its entities
                device_entry = device_registry.async_get_device(
                    identifiers={(DOMAIN, f"vehicle_{vehicle_id}")}
                )

                if device_entry:
                    _LOGGER.info(
                        "Removing device %s for vehicle %s",
                        device_entry.name,
                        vehicle_id
                    )

                    # Remove all entities associated with this device
                    entities = entity_registry.entities.get_entries_for_device_id(
                        device_entry.id,
                        include_disabled_entities=True
                    )
                    for entity in entities:
                        _LOGGER.debug(
                            "Removing entity %s for vehicle %s",
                            entity.entity_id,
                            vehicle_id
                        )
                        entity_registry.async_remove(entity.entity_id)

                    # Remove the device
                    device_registry.async_remove_device(device_entry.id)

            # Update selected vehicles to remove the deleted ones
            self._selected_vehicles -= removed_vehicle_ids

            # Also remove from discovered vehicles
            self._discovered_vehicles -= removed_vehicle_ids

            # Update config entry with new selected vehicles
            updated_data = {
                **self.config_entry.data,
                CONF_SELECTED_VEHICLES: list(self._selected_vehicles)
            }
            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data=updated_data
            )

            _LOGGER.info(
                "Updated config entry to remove %d deleted vehicles",
                len(removed_vehicle_ids)
            )


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
        super().__init__(hass, config_entry)
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

        _LOGGER.info(
            "Position coordinator update #%d starting (interval: %s)",
            self._update_count,
            self.update_interval,
        )

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
                "Fetching data fields for all vehicles",
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
                            fields = await self._client.get_data_fields(
                                device_id, vehicle.id
                            )

                            if fields:
                                # Merge fields from all devices (later devices override earlier ones)
                                vehicle_copy.data_fields = (
                                    vehicle_copy.data_fields or {}
                                )
                                vehicle_copy.data_fields.update(fields)
                                data_field_count += len(fields)

                                # Extract position data from fields if available
                                if (
                                    "track.pos.loc" in fields
                                    and "track.pos.alt" in fields
                                ):
                                    try:
                                        loc_field = fields["track.pos.loc"]
                                        if isinstance(loc_field.last_value, dict):
                                            # Construct position from data fields
                                            vehicle_copy.position = VehiclePosition(
                                                timestamp=loc_field.last_seen,
                                                latitude=loc_field.last_value.get(
                                                    "lat", 0
                                                ),
                                                longitude=loc_field.last_value.get(
                                                    "lon", 0
                                                ),
                                                altitude=fields.get(
                                                    "track.pos.alt",
                                                    DataFieldValue(
                                                        field_prefix="",
                                                        field_name="",
                                                        frequency=0,
                                                        value_type="",
                                                        title="",
                                                        last_seen=loc_field.last_seen,
                                                        last_value=0,
                                                        description="",
                                                        last_update=loc_field.last_update,
                                                    ),
                                                ).last_value,
                                                speed=fields.get(
                                                    "track.pos.sog",
                                                    DataFieldValue(
                                                        field_prefix="",
                                                        field_name="",
                                                        frequency=0,
                                                        value_type="",
                                                        title="",
                                                        last_seen=loc_field.last_seen,
                                                        last_value=0,
                                                        description="",
                                                        last_update=loc_field.last_update,
                                                    ),
                                                ).last_value,
                                                course=fields.get(
                                                    "track.pos.cog",
                                                    DataFieldValue(
                                                        field_prefix="",
                                                        field_name="",
                                                        frequency=0,
                                                        value_type="",
                                                        title="",
                                                        last_seen=loc_field.last_seen,
                                                        last_value=0,
                                                        description="",
                                                        last_update=loc_field.last_update,
                                                    ),
                                                ).last_value,
                                                num_satellites=fields.get(
                                                    "track.pos.nsat",
                                                    DataFieldValue(
                                                        field_prefix="",
                                                        field_name="",
                                                        frequency=0,
                                                        value_type="",
                                                        title="",
                                                        last_seen=loc_field.last_seen,
                                                        last_value=0,
                                                        description="",
                                                        last_update=loc_field.last_update,
                                                    ),
                                                ).last_value,
                                            )
                                            _LOGGER.debug(
                                                "Extracted position from data fields for vehicle %s",
                                                vehicle.name,
                                            )
                                    except Exception as err:
                                        _LOGGER.warning(
                                            "Failed to extract position from data fields: %s",
                                            err,
                                        )

                                _LOGGER.debug(
                                    "Got %d data fields for vehicle %s (device %s)",
                                    len(fields),
                                    vehicle.name,
                                    device_id,
                                )
                            else:
                                _LOGGER.debug(
                                    "No data fields for vehicle %s (device %s)",
                                    vehicle.name,
                                    device_id,
                                )

                        except Exception as err:
                            self._failed_api_calls += 1
                            _LOGGER.warning(
                                "Failed to fetch data fields for device %s: %s",
                                device_id,
                                err,
                            )
                            continue
                else:
                    _LOGGER.debug(
                        "Vehicle %s has no devices",
                        vehicle.name,
                    )

                data[vehicle_id] = vehicle_copy

            # Track successful update
            self._last_update_duration = self.hass.loop.time() - start_time
            self._last_api_call_time = self.hass.loop.time()

            _LOGGER.info(
                "Successfully updated data with %d fields for %d vehicles in %.2fs (update #%d, %.1f%% success rate)",
                data_field_count,
                len(data),
                self._last_update_duration,
                self._update_count,
                self.success_rate,
            )

            _LOGGER.info(
                "Position coordinator update #%d completed successfully (next update in %s)",
                self._update_count,
                self.update_interval,
            )

            return data

        except Exception as err:
            self._failed_api_calls += 1
            self._last_update_duration = self.hass.loop.time() - start_time
            _LOGGER.error(
                "Unexpected error fetching data fields (update #%d, %.1f%% success rate): %s",
                self._update_count,
                self.success_rate,
                err,
                exc_info=True,
            )
            raise UpdateFailed(f"Failed to fetch data fields: {err}") from err


class AutoPiTripCoordinator(AutoPiDataUpdateCoordinator):
    """Coordinator specifically for fetching vehicle trip data."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        base_coordinator: AutoPiDataUpdateCoordinator,
    ) -> None:
        """Initialize the trip coordinator.

        Args:
            hass: Home Assistant instance
            config_entry: Configuration entry for this integration
            base_coordinator: Base coordinator to get vehicle data from
        """
        # Trip data updates frequently (1 min default) for auto-zero functionality
        super().__init__(hass, config_entry)
        self._base_coordinator = base_coordinator
        # Store trip history for event detection
        self._last_trip_ids: dict[str, str] = {}

    async def _async_update_data(self) -> CoordinatorData:
        """Fetch trip data from AutoPi API.

        Returns:
            Dictionary mapping vehicle IDs to AutoPiVehicle objects with trip data

        Raises:
            UpdateFailed: If data fetching fails
        """
        start_time = self.hass.loop.time()
        self._update_count += 1

        _LOGGER.info(
            "Trip coordinator update #%d starting (interval: %s)",
            self._update_count,
            self.update_interval,
        )

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
                "Fetching trip data for all vehicles",
            )

            # Copy vehicle data from base coordinator
            data: CoordinatorData = {}
            total_trips = 0

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
                    position=vehicle.position,
                    data_fields=vehicle.data_fields,
                    trip_count=0,
                    last_trip=None,
                    total_distance_km=0.0,
                )

                # Fetch trip data
                try:
                    self._total_api_calls += 1

                    # Use the first device if available for better filtering
                    device_id = vehicle.devices[0] if vehicle.devices else None

                    # Get last trip and total count
                    trip_count, trips = await self._client.get_trips(
                        vehicle.id, device_id, page_size=1
                    )

                    vehicle_copy.trip_count = trip_count
                    total_trips += trip_count

                    if trips:
                        vehicle_copy.last_trip = trips[0]

                        # Check if this is a new trip
                        last_trip_id = self._last_trip_ids.get(vehicle_id)
                        if last_trip_id and last_trip_id != trips[0].trip_id:
                            # Fire event for new trip
                            self._fire_trip_event(vehicle_copy, trips[0])

                        # Update last trip ID
                        self._last_trip_ids[vehicle_id] = trips[0].trip_id

                        _LOGGER.debug(
                            "Vehicle %s has %d trips, last trip: %s km",
                            vehicle.name,
                            trip_count,
                            trips[0].distance_km,
                        )
                    else:
                        _LOGGER.debug(
                            "Vehicle %s has %d trips but no trip data returned",
                            vehicle.name,
                            trip_count,
                        )

                    # TODO: Calculate total distance from all trips (requires paginating through all trips)
                    # For now, we'll track this separately in the sensor

                except Exception as err:
                    self._failed_api_calls += 1
                    _LOGGER.warning(
                        "Failed to fetch trips for vehicle %s: %s",
                        vehicle.name,
                        err,
                    )

                data[vehicle_id] = vehicle_copy

            # Track successful update
            self._last_update_duration = self.hass.loop.time() - start_time
            self._last_api_call_time = self.hass.loop.time()

            _LOGGER.info(
                "Successfully updated trip data for %d vehicles with %d total trips in %.2fs",
                len(data),
                total_trips,
                self._last_update_duration,
            )

            # Periodically clean up old trip data from auto-zero manager
            if self._update_count % 60 == 0:  # Every 60 updates (60 minutes)
                from .auto_zero import get_auto_zero_manager

                auto_zero_manager = get_auto_zero_manager()
                auto_zero_manager.cleanup_old_data()

            _LOGGER.info(
                "Trip coordinator update #%d completed successfully (next update in %s)",
                self._update_count,
                self.update_interval,
            )

            return data

        except Exception as err:
            self._failed_api_calls += 1
            self._last_update_duration = self.hass.loop.time() - start_time
            _LOGGER.error(
                "Unexpected error fetching trip data: %s",
                err,
                exc_info=True,
            )
            raise UpdateFailed(f"Failed to fetch trip data: {err}") from err

    def _fire_trip_event(self, vehicle: AutoPiVehicle, trip: AutoPiTrip) -> None:
        """Fire an event for a new trip.

        Args:
            vehicle: The vehicle that took the trip
            trip: The trip data
        """
        event_data = {
            "vehicle_id": vehicle.id,
            "vehicle_name": vehicle.name,
            "vehicle_license_plate": vehicle.license_plate,
            "trip_id": trip.trip_id,
            "start_time": trip.start_time.isoformat(),
            "end_time": trip.end_time.isoformat(),
            "duration_seconds": trip.duration_seconds,
            "distance_km": trip.distance_km,
            "start_location": {
                "latitude": trip.start_lat,
                "longitude": trip.start_lng,
                "address": trip.start_address,
            },
            "end_location": {
                "latitude": trip.end_lat,
                "longitude": trip.end_lng,
                "address": trip.end_address,
            },
        }

        self.hass.bus.async_fire(
            f"{DOMAIN}_trip_completed",
            event_data,
        )

        _LOGGER.info(
            "Fired trip_completed event for vehicle %s: %.1f km in %d minutes",
            vehicle.name,
            trip.distance_km,
            trip.duration_seconds // 60,
        )
