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

        # Fleet-wide data
        self._fleet_alerts: list[FleetAlert] = []
        self._fleet_alerts_total: int = 0
        self._last_alert_ids: set[str] = set()

        # Device events tracking
        self._device_events: dict[str, list[AutoPiEvent]] = {}
        self._last_event_timestamps: dict[str, str] = {}

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

            # Fetch fleet alerts (only for base coordinator in fast ring)
            if self._update_ring == UPDATE_RING_FAST:
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
                                    new_events = events

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
        # Trip data updates less frequently (slow update ring - 15 min default)
        super().__init__(hass, config_entry, UPDATE_RING_SLOW)
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
                "[%s] Fetching trip data for all vehicles",
                self._update_ring,
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
                            "[%s] Vehicle %s has %d trips, last trip: %s km",
                            self._update_ring,
                            vehicle.name,
                            trip_count,
                            trips[0].distance_km,
                        )
                    else:
                        _LOGGER.debug(
                            "[%s] Vehicle %s has %d trips but no trip data returned",
                            self._update_ring,
                            vehicle.name,
                            trip_count,
                        )

                    # TODO: Calculate total distance from all trips (requires paginating through all trips)
                    # For now, we'll track this separately in the sensor

                except Exception as err:
                    self._failed_api_calls += 1
                    _LOGGER.warning(
                        "[%s] Failed to fetch trips for vehicle %s: %s",
                        self._update_ring,
                        vehicle.name,
                        err,
                    )

                data[vehicle_id] = vehicle_copy

            # Track successful update
            self._last_update_duration = self.hass.loop.time() - start_time
            self._last_api_call_time = self.hass.loop.time()

            _LOGGER.info(
                "[%s] Successfully updated trip data for %d vehicles with %d total trips in %.2fs",
                self._update_ring,
                len(data),
                total_trips,
                self._last_update_duration,
            )

            return data

        except Exception as err:
            self._failed_api_calls += 1
            self._last_update_duration = self.hass.loop.time() - start_time
            _LOGGER.error(
                "[%s] Unexpected error fetching trip data: %s",
                self._update_ring,
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
