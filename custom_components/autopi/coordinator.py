"""Data update coordinator for AutoPi integration."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .client import AutoPiClient

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
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
    AutoPiTimeoutError,
)
from .types import (
    AutoPiEvent,
    AutoPiTrip,
    AutoPiVehicle,
    ChargingSession,
    CoordinatorData,
    DataFieldValue,
    DtcEntry,
    FleetAlert,
    FleetAlertSummary,
    FleetVehicleSummary,
    GeofenceSummary,
    RecentStatEvent,
    RfidEvent,
    SimplifiedEvent,
    VehiclePosition,
)

_LOGGER = logging.getLogger(__name__)


def _format_utc(dt: datetime) -> str:
    """Format a datetime as ISO 8601 UTC string."""
    return dt.astimezone(UTC).isoformat().replace("+00:00", "Z")


# Optional API endpoint feature keys (used for support tracking)
ENDPOINT_KEY_CHARGING_SESSIONS = "charging_sessions"
ENDPOINT_KEY_DIAGNOSTICS = "diagnostics"
ENDPOINT_KEY_EVENTS_HISTOGRAM = "events_histogram"
ENDPOINT_KEY_FLEET_ALERTS = "fleet_alerts"
ENDPOINT_KEY_FLEET_ALERTS_SUMMARY = "fleet_alerts_summary"
ENDPOINT_KEY_FLEET_VEHICLE_SUMMARY = "fleet_vehicle_summary"
ENDPOINT_KEY_GEOFENCE_SUMMARY = "geofence_summary"
ENDPOINT_KEY_MOST_RECENT_POSITIONS = "most_recent_positions"
ENDPOINT_KEY_OBD_DTCS = "obd_dtcs"
ENDPOINT_KEY_RECENT_STATS = "recent_stats"
ENDPOINT_KEY_RFID_EVENTS = "rfid_events"
ENDPOINT_KEY_SIMPLIFIED_EVENTS = "simplified_events"
ENDPOINT_KEY_TRIPS = "trips"
ENDPOINT_KEY_VEHICLE_ALERTS = "vehicle_alerts"


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

        # Fleet alerts summary and per-vehicle alerts
        self._fleet_alert_summary: FleetAlertSummary | None = None
        self._vehicle_alerts: dict[str, dict[str, Any]] = {}

        # Charging sessions per vehicle
        self._charging_sessions: dict[str, ChargingSession | None] = {}

        # Diagnostic data
        self._vehicle_diagnostics: dict[str, dict[str, Any]] = {}
        self._vehicle_dtcs: dict[str, list[DtcEntry]] = {}
        self._last_dtc_ids: dict[str, str] = {}

        # Geofence summary per vehicle
        self._geofence_summary: dict[str, GeofenceSummary] = {}

        # Fleet vehicle summary
        self._fleet_vehicle_summary: FleetVehicleSummary | None = None

        # Event histogram counts per vehicle/tag
        self._event_histogram_counts: dict[str, dict[str, dict[str, int]]] = {}

        # Simplified events per vehicle
        self._simplified_events: dict[str, SimplifiedEvent] = {}
        self._last_simplified_event_ids: dict[str, str] = {}

        # RFID events
        self._rfid_events: list[RfidEvent] = []
        self._last_rfid_event_ts: datetime | None = None

        # Movement and last communication (populated by position coordinator)
        self._last_communications: dict[str, datetime] = {}
        self._movement_state: dict[str, bool] = {}
        self._movement_info: dict[str, dict[str, Any]] = {}

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

        _LOGGER.debug(
            "Base coordinator update #%d starting (interval: %s)",
            self._update_count,
            self.update_interval,
        )
        now_utc = datetime.now(UTC)

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
                filtered_vehicles = [
                    v for v in vehicles if str(v.id) in self._selected_vehicles
                ]
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
            data: CoordinatorData = {
                str(vehicle.id): vehicle for vehicle in filtered_vehicles
            }

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
            except (AutoPiConnectionError, AutoPiAPIError, AutoPiTimeoutError) as err:
                self._failed_api_calls += 1
                _LOGGER.warning("Failed to fetch fleet alerts: %s", err)
                # Continue even if alerts fail

            # Fetch fleet alert summary
            try:
                self._total_api_calls += 1
                self._fleet_alert_summary = await self._client.get_fleet_alerts_summary()
            except (AutoPiConnectionError, AutoPiAPIError, AutoPiTimeoutError) as err:
                self._failed_api_calls += 1
                _LOGGER.warning("Failed to fetch fleet alerts summary: %s", err)

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
                                _LOGGER.debug(
                                    "Initial event fetch for device %s: found %d events, skipping startup events to avoid replaying old events",
                                    device_id,
                                    len(events),
                                )

                        # Fire events for new events
                        for event in new_events:
                            self._fire_device_event(event, str(vehicle.id))

                        if new_events:
                            _LOGGER.debug(
                                "Found %d new events for device %s",
                                len(new_events),
                                device_id,
                            )

                    except (
                        AutoPiConnectionError,
                        AutoPiAPIError,
                        AutoPiTimeoutError,
                    ) as err:
                        self._failed_api_calls += 1
                        _LOGGER.warning(
                            "Failed to fetch events for device %s: %s",
                            device_id,
                            err,
                        )
                        # Continue even if events fail for one device

            # Fetch fleet vehicle summary
            try:
                self._total_api_calls += 1
                self._fleet_vehicle_summary = (
                    await self._client.get_fleet_vehicle_summary()
                )
            except (AutoPiConnectionError, AutoPiAPIError, AutoPiTimeoutError) as err:
                self._failed_api_calls += 1
                _LOGGER.warning("Failed to fetch fleet vehicle summary: %s", err)

            # Fetch RFID events (last 7 days or since last event)
            try:
                self._total_api_calls += 1
                rfid_start = self._last_rfid_event_ts or (
                    now_utc - timedelta(days=7)
                )
                rfid_events = await self._client.get_rfid_events(
                    _format_utc(rfid_start),
                    _format_utc(now_utc),
                )
                self._rfid_events = rfid_events
                if rfid_events:
                    newest_ts = rfid_events[0].timestamp
                    if self._last_rfid_event_ts:
                        for event in reversed(rfid_events):
                            if event.timestamp > self._last_rfid_event_ts:
                                self._fire_rfid_event(event)
                    self._last_rfid_event_ts = newest_ts
            except (AutoPiConnectionError, AutoPiAPIError, AutoPiTimeoutError) as err:
                self._failed_api_calls += 1
                _LOGGER.warning("Failed to fetch RFID events: %s", err)

            # Fetch per-vehicle data
            for vehicle_id, vehicle in data.items():
                # Vehicle alerts
                try:
                    self._total_api_calls += 1
                    alerts_response = await self._client.get_vehicle_alerts(vehicle.id)
                    count = int(alerts_response.get("count", 0))
                    results = alerts_response.get("results", [])
                    severity_counts: dict[str, int] = {}
                    for alert in results:
                        if not isinstance(alert, dict):
                            continue
                        severity = str(
                            alert.get("severity")
                            or alert.get("level")
                            or alert.get("priority")
                            or "unknown"
                        )
                        severity_counts[severity] = severity_counts.get(severity, 0) + 1
                    self._vehicle_alerts[vehicle_id] = {
                        "count": count,
                        "severity_counts": severity_counts,
                        "alerts": results,
                    }
                except (AutoPiConnectionError, AutoPiAPIError, AutoPiTimeoutError) as err:
                    self._failed_api_calls += 1
                    _LOGGER.warning(
                        "Failed to fetch alerts for vehicle %s: %s",
                        vehicle.name,
                        err,
                    )

                # Charging sessions
                try:
                    self._total_api_calls += 1
                    year_start = datetime(
                        now_utc.year, 1, 1, tzinfo=UTC
                    )
                    sessions = await self._client.get_charging_sessions(
                        vehicle.id,
                        ["vehicle/battery/charging"],
                        ["vehicle/battery/discharging"],
                        _format_utc(year_start),
                        _format_utc(now_utc),
                    )
                    latest_session = None
                    if sessions:
                        latest_session = max(
                            sessions,
                            key=lambda session: session.start
                            or datetime.min.replace(tzinfo=UTC),
                        )
                    self._charging_sessions[vehicle_id] = latest_session
                except (AutoPiConnectionError, AutoPiAPIError, AutoPiTimeoutError) as err:
                    self._failed_api_calls += 1
                    _LOGGER.warning(
                        "Failed to fetch charging sessions for vehicle %s: %s",
                        vehicle.name,
                        err,
                    )

                # Diagnostics and DTCs
                device_id = vehicle.devices[0] if vehicle.devices else None
                if device_id:
                    try:
                        self._total_api_calls += 1
                        diagnostics = await self._client.get_diagnostics(device_id)
                        self._vehicle_diagnostics[vehicle_id] = diagnostics
                    except (
                        AutoPiConnectionError,
                        AutoPiAPIError,
                        AutoPiTimeoutError,
                    ) as err:
                        self._failed_api_calls += 1
                        _LOGGER.warning(
                            "Failed to fetch diagnostics for vehicle %s: %s",
                            vehicle.name,
                            err,
                        )

                try:
                    self._total_api_calls += 1
                    dtcs = await self._client.get_obd_dtcs(vehicle.id)
                    self._vehicle_dtcs[vehicle_id] = dtcs
                    self._process_new_dtc_events(vehicle_id, dtcs)
                except (AutoPiConnectionError, AutoPiTimeoutError) as err:
                    self._failed_api_calls += 1
                    _LOGGER.warning(
                        "Failed to fetch DTCs for vehicle %s: %s",
                        vehicle.name,
                        err,
                    )
                except AutoPiAPIError as err:
                    self._failed_api_calls += 1
                    _LOGGER.debug(
                        "DTC endpoint unavailable for vehicle %s: %s",
                        vehicle.name,
                        err,
                    )

                # Geofence summary
                try:
                    self._total_api_calls += 1
                    geofence_response = await self._client.get_geofence_summary(
                        vehicle.id
                    )
                    self._geofence_summary[vehicle_id] = self._parse_geofence_summary(
                        geofence_response
                    )
                except (AutoPiConnectionError, AutoPiAPIError, AutoPiTimeoutError) as err:
                    self._failed_api_calls += 1
                    _LOGGER.warning(
                        "Failed to fetch geofence summary for vehicle %s: %s",
                        vehicle.name,
                        err,
                    )

                # Simplified events
                try:
                    self._total_api_calls += 1
                    simplified_events = await self._client.get_simplified_events(
                        vehicle.id, page_hits=1, ordering="-ts"
                    )
                    if simplified_events:
                        latest = simplified_events[0]
                        self._simplified_events[vehicle_id] = latest
                        self._process_new_simplified_event(vehicle_id, latest)
                except (AutoPiConnectionError, AutoPiAPIError, AutoPiTimeoutError) as err:
                    self._failed_api_calls += 1
                    _LOGGER.warning(
                        "Failed to fetch simplified events for vehicle %s: %s",
                        vehicle.name,
                        err,
                    )

                # Event histogram counts
                if device_id:
                    for tag in ("harsh", "speeding"):
                        try:
                            self._total_api_calls += 1
                            buckets = await self._client.get_events_histogram(
                                device_id,
                                _format_utc(now_utc - timedelta(days=7)),
                                _format_utc(now_utc),
                                "1h",
                                tag,
                                event_type="event",
                            )
                            count_24h, count_7d = self._summarize_histogram(
                                buckets, now_utc
                            )
                            self._event_histogram_counts.setdefault(vehicle_id, {})[
                                tag
                            ] = {"24h": count_24h, "7d": count_7d}
                        except (
                            AutoPiConnectionError,
                            AutoPiAPIError,
                            AutoPiTimeoutError,
                        ) as err:
                            self._failed_api_calls += 1
                            _LOGGER.warning(
                                "Failed to fetch event histogram for vehicle %s: %s",
                                vehicle.name,
                                err,
                            )

            # Track successful update
            self._last_update_duration = self.hass.loop.time() - start_time
            self._last_api_call_time = self.hass.loop.time()

            _LOGGER.debug(
                "Base coordinator update #%d completed successfully in %.2fs (next update in %s)",
                self._update_count,
                self._last_update_duration,
                self.update_interval,
            )

            return data

        except AutoPiAuthenticationError as err:
            self._failed_api_calls += 1
            self._last_update_duration = self.hass.loop.time() - start_time
            _LOGGER.exception("Authentication error")
            # Mark config entry for reauth
            self.config_entry.async_start_reauth(self.hass)
            raise UpdateFailed(f"Authentication failed: {err}") from err

        except AutoPiConnectionError as err:
            self._failed_api_calls += 1
            self._last_update_duration = self.hass.loop.time() - start_time
            _LOGGER.exception("Connection error")
            raise UpdateFailed(f"Failed to connect to AutoPi API: {err}") from err

        except AutoPiAPIError as err:
            self._failed_api_calls += 1
            self._last_update_duration = self.hass.loop.time() - start_time
            _LOGGER.exception("API error")
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
                deselected,
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

        _LOGGER.debug(
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

    def _fire_dtc_event(self, vehicle_id: str, dtc: DtcEntry) -> None:
        """Fire an event for a new DTC entry."""
        event_data = {
            "vehicle_id": vehicle_id,
            "dtc_code": dtc.code,
            "description": dtc.description,
            "occurred_at": dtc.occurred_at.isoformat() if dtc.occurred_at else None,
        }

        self.hass.bus.async_fire(
            f"{DOMAIN}_dtc_event",
            event_data,
        )

        _LOGGER.debug(
            "Fired DTC event for vehicle %s: %s", vehicle_id, dtc.code
        )

    def _fire_simplified_event(
        self, vehicle_id: str, event: SimplifiedEvent
    ) -> None:
        """Fire an event for a simplified event."""
        event_data = {
            "vehicle_id": vehicle_id,
            "timestamp": event.timestamp.isoformat(),
            "event": event.event_type,
            "tag": event.tag,
            "area": event.area,
            "name": event.name,
        }

        self.hass.bus.async_fire(
            f"{DOMAIN}_simplified_event",
            event_data,
        )

        _LOGGER.debug(
            "Fired simplified event for vehicle %s: %s", vehicle_id, event.event_type
        )

    def _fire_rfid_event(self, event: RfidEvent) -> None:
        """Fire an event for an RFID entry."""
        event_data = {
            "timestamp": event.timestamp.isoformat(),
            "status": event.status,
            "token": event.token,
            "user_email": event.user_email,
            "vehicle_id": event.vehicle_id,
        }

        self.hass.bus.async_fire(
            f"{DOMAIN}_rfid_event",
            event_data,
        )

        _LOGGER.debug(
            "Fired RFID event for vehicle %s",
            event.vehicle_id,
        )

    def _process_new_dtc_events(
        self, vehicle_id: str, dtcs: list[DtcEntry]
    ) -> None:
        """Process new DTC entries and fire events."""
        if not dtcs:
            return

        latest = max(
            dtcs,
            key=lambda entry: entry.occurred_at or datetime.min.replace(tzinfo=UTC),
        )
        dtc_id = f"{latest.code}:{latest.occurred_at}"

        last_dtc_id = self._last_dtc_ids.get(vehicle_id)
        if last_dtc_id is None:
            self._last_dtc_ids[vehicle_id] = dtc_id
            _LOGGER.debug(
                "Initial DTC fetch for vehicle %s: skipping event firing",
                vehicle_id,
            )
            return

        if dtc_id != last_dtc_id:
            self._fire_dtc_event(vehicle_id, latest)
            self._last_dtc_ids[vehicle_id] = dtc_id

    def _process_new_simplified_event(
        self, vehicle_id: str, event: SimplifiedEvent
    ) -> None:
        """Process simplified event and fire when new."""
        event_id = f"{event.event_type}:{event.timestamp.isoformat()}"
        last_id = self._last_simplified_event_ids.get(vehicle_id)

        if last_id is None:
            self._last_simplified_event_ids[vehicle_id] = event_id
            _LOGGER.debug(
                "Initial simplified event fetch for vehicle %s: skipping event firing",
                vehicle_id,
            )
            return

        if event_id != last_id:
            self._fire_simplified_event(vehicle_id, event)
            self._last_simplified_event_ids[vehicle_id] = event_id

    def _parse_geofence_summary(self, response: dict[str, Any]) -> GeofenceSummary:
        """Parse geofence summary response."""
        counts = response.get("counts", {}) if isinstance(response, dict) else {}
        location_count = int(counts.get("locations", 0))
        geofence_count = int(counts.get("geofences", 0))

        last_entered: datetime | None = None
        last_exited: datetime | None = None
        for entry in response.get("results", []) if isinstance(response, dict) else []:
            if not isinstance(entry, dict):
                continue
            for key, value in entry.items():
                if not isinstance(value, str):
                    continue
                if "enter" in key and last_entered is None:
                    try:
                        last_entered = datetime.fromisoformat(
                            value.replace("Z", "+00:00")
                        )
                    except ValueError:
                        continue
                if "exit" in key and last_exited is None:
                    try:
                        last_exited = datetime.fromisoformat(
                            value.replace("Z", "+00:00")
                        )
                    except ValueError:
                        continue

        return GeofenceSummary(
            location_count=location_count,
            geofence_count=geofence_count,
            last_entered=last_entered,
            last_exited=last_exited,
        )

    def _summarize_histogram(
        self, buckets: list[dict[str, Any]], now: datetime
    ) -> tuple[int, int]:
        """Summarize histogram buckets into 24h and 7d counts."""
        total_7d = 0
        total_24h = 0
        cutoff = now - timedelta(days=1)

        for bucket in buckets:
            count = int(bucket.get("count", 0) or 0)
            total_7d += count

            ts_value = bucket.get("ts") or bucket.get("start") or bucket.get("timestamp")
            if ts_value:
                try:
                    ts = datetime.fromisoformat(str(ts_value).replace("Z", "+00:00"))
                except ValueError:
                    continue
                if ts >= cutoff:
                    total_24h += count

        return total_24h, total_7d

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

    def get_vehicle_alert_summary(self, vehicle_id: str) -> dict[str, Any]:
        """Return alert summary for a vehicle."""
        return self._vehicle_alerts.get(
            vehicle_id, {"count": 0, "severity_counts": {}, "alerts": []}
        )

    def get_vehicle_alert_count(self, vehicle_id: str) -> int:
        """Return alert count for a vehicle."""
        return int(self.get_vehicle_alert_summary(vehicle_id).get("count", 0))

    def get_vehicle_charging_state(self, vehicle_id: str) -> bool | None:
        """Return charging state for a vehicle."""
        session = self._charging_sessions.get(vehicle_id)
        if session is None:
            return None
        if session.end is None:
            return True
        if session.state and session.state.lower() in {"charging", "active"}:
            return True
        return False

    def get_vehicle_charging_info(self, vehicle_id: str) -> dict[str, Any]:
        """Return charging info for a vehicle."""
        session = self._charging_sessions.get(vehicle_id)
        if session is None:
            return {}
        return {
            "last_charge_start": session.start.isoformat() if session.start else None,
            "last_charge_end": session.end.isoformat() if session.end else None,
            "last_charge_duration_seconds": session.duration_seconds,
            "last_charge_state": session.state,
            "start_tag": session.start_tag,
            "end_tag": session.end_tag,
        }

    def get_vehicle_dtc_entries(self, vehicle_id: str) -> list[DtcEntry]:
        """Return DTC entries for a vehicle."""
        return self._vehicle_dtcs.get(vehicle_id, [])

    def get_vehicle_dtc_count(self, vehicle_id: str) -> int:
        """Return DTC count for a vehicle."""
        dtcs = self._vehicle_dtcs.get(vehicle_id, [])
        if dtcs:
            return len(dtcs)
        diagnostics = self._vehicle_diagnostics.get(vehicle_id, {})
        return int(diagnostics.get("count", 0))

    def get_vehicle_last_dtc(self, vehicle_id: str) -> DtcEntry | None:
        """Return last DTC entry for a vehicle."""
        dtcs = self._vehicle_dtcs.get(vehicle_id, [])
        if not dtcs:
            return None
        return max(
            dtcs,
            key=lambda entry: entry.occurred_at or datetime.min.replace(tzinfo=UTC),
        )

    def get_geofence_summary(self, vehicle_id: str) -> GeofenceSummary | None:
        """Return geofence summary for a vehicle."""
        return self._geofence_summary.get(vehicle_id)

    def get_fleet_vehicle_summary(self) -> FleetVehicleSummary | None:
        """Return fleet vehicle summary."""
        return self._fleet_vehicle_summary

    def get_event_volume(
        self, vehicle_id: str, tag: str, window: str
    ) -> int | None:
        """Return event volume for a tag/window."""
        vehicle_data = self._event_histogram_counts.get(vehicle_id)
        if not vehicle_data:
            return None
        tag_data = vehicle_data.get(tag)
        if not tag_data:
            return None
        return tag_data.get(window)

    def get_simplified_event(self, vehicle_id: str) -> SimplifiedEvent | None:
        """Return latest simplified event for a vehicle."""
        return self._simplified_events.get(vehicle_id)

    def get_last_communication(self, vehicle_id: str) -> datetime | None:
        """Return last communication timestamp for a vehicle."""
        return self._last_communications.get(vehicle_id)

    def get_online_threshold(self) -> timedelta:
        """Return online threshold based on update interval."""
        return max(self.update_interval * 2, timedelta(minutes=5))

    def get_vehicle_movement(self, vehicle_id: str) -> bool | None:
        """Return movement state for a vehicle."""
        return self._movement_state.get(vehicle_id)

    def get_vehicle_movement_info(self, vehicle_id: str) -> dict[str, Any]:
        """Return movement info for a vehicle."""
        return self._movement_info.get(vehicle_id, {})

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
            _LOGGER.debug(
                "Found %d new vehicles: %s", len(new_vehicle_ids), new_vehicle_ids
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
                        vehicle.license_plate or "No plate",
                    )

                    # Create discovery context
                    discovery_data = {
                        "vehicle_id": str(vehicle.id),
                        "vehicle_name": vehicle.name,
                        "license_plate": vehicle.license_plate,
                        "vin": vehicle.vin,
                        "api_key": self.config_entry.data[CONF_API_KEY],
                        "base_url": self.config_entry.data.get(
                            CONF_BASE_URL, DEFAULT_BASE_URL
                        ),
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
                len(self._discovered_vehicles),
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
                removed_vehicle_ids,
            )

            # Get device registry
            device_registry = dr.async_get(self.hass)

            # Get entity registry
            entity_registry = er.async_get(self.hass)

            for vehicle_id in removed_vehicle_ids:
                _LOGGER.debug(
                    "Removing vehicle %s from selected vehicles as it no longer exists in API",
                    vehicle_id,
                )

                # Remove the device and all its entities
                device_entry = device_registry.async_get_device(
                    identifiers={(DOMAIN, f"vehicle_{vehicle_id}")}
                )

                if device_entry:
                    _LOGGER.debug(
                        "Removing device %s for vehicle %s",
                        device_entry.name,
                        vehicle_id,
                    )

                    # Remove all entities associated with this device
                    entities = entity_registry.entities.get_entries_for_device_id(
                        device_entry.id, include_disabled_entities=True
                    )
                    for entity in entities:
                        _LOGGER.debug(
                            "Removing entity %s for vehicle %s",
                            entity.entity_id,
                            vehicle_id,
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
                CONF_SELECTED_VEHICLES: list(self._selected_vehicles),
            }
            self.hass.config_entries.async_update_entry(
                self.config_entry, data=updated_data
            )

            _LOGGER.debug(
                "Updated config entry to remove %d deleted vehicles",
                len(removed_vehicle_ids),
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

        _LOGGER.debug(
            "Position coordinator update #%d starting (interval: %s)",
            self._update_count,
            self.update_interval,
        )
        now_utc = datetime.now(UTC)

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

            # Fetch most recent positions for last communication/fallback location
            recent_position_map: dict[str, VehiclePosition] = {}
            last_comm_map: dict[str, datetime] = {}
            try:
                self._total_api_calls += 1
                positions = await self._client.get_most_recent_positions()
                device_to_vehicle: dict[str, str] = {}
                for vehicle_id, vehicle in self._base_coordinator.data.items():
                    for device_id in vehicle.devices:
                        device_to_vehicle[device_id] = vehicle_id

                for entry in positions:
                    vehicle_id = device_to_vehicle.get(entry.device_id)
                    if not vehicle_id:
                        continue
                    if entry.last_communication:
                        current_last = last_comm_map.get(vehicle_id)
                        if current_last is None or entry.last_communication > current_last:
                            last_comm_map[vehicle_id] = entry.last_communication
                            if entry.position:
                                recent_position_map[vehicle_id] = entry.position

                if last_comm_map:
                    self._last_communications = last_comm_map
            except (AutoPiConnectionError, AutoPiAPIError, AutoPiTimeoutError) as err:
                self._failed_api_calls += 1
                _LOGGER.warning("Failed to fetch most recent positions: %s", err)

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
                                    except (KeyError, ValueError, TypeError) as err:
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

                        except (
                            AutoPiConnectionError,
                            AutoPiAPIError,
                            AutoPiTimeoutError,
                        ) as err:
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

                # Fetch recent stats for movement detection
                latest_event: RecentStatEvent | None = None
                if vehicle.devices:
                    from_timestamp = _format_utc(now_utc - timedelta(days=1))
                    for device_id in vehicle.devices:
                        try:
                            self._total_api_calls += 1
                            events = await self._client.get_recent_stats(
                                device_id,
                                from_timestamp,
                                stat_type="event",
                            )
                            if events:
                                if (
                                    latest_event is None
                                    or events[0].timestamp > latest_event.timestamp
                                ):
                                    latest_event = events[0]
                        except (
                            AutoPiConnectionError,
                            AutoPiAPIError,
                            AutoPiTimeoutError,
                        ) as err:
                            self._failed_api_calls += 1
                            _LOGGER.warning(
                                "Failed to fetch recent stats for device %s: %s",
                                device_id,
                                err,
                            )

                movement_state: bool | None = None
                movement_info: dict[str, Any] = {}
                if latest_event and latest_event.tag:
                    movement_info.update(
                        {
                            "last_event_tag": latest_event.tag,
                            "last_event_time": latest_event.timestamp.isoformat(),
                            "event_type": latest_event.event_type,
                            "source": "recent_stats",
                        }
                    )
                    if "standstill" in latest_event.tag:
                        movement_state = False
                    else:
                        movement_state = True

                if movement_state is None and vehicle_copy.data_fields:
                    speed_value = None
                    for field_id in ("track.pos.sog", "std.speed.value", "obd.speed.value"):
                        field_data = vehicle_copy.data_fields.get(field_id)
                        if field_data and field_data.last_value is not None:
                            try:
                                speed_value = float(field_data.last_value)
                                break
                            except (TypeError, ValueError):
                                continue
                    if speed_value is not None:
                        movement_state = speed_value > 0
                        movement_info = {"source": "speed"}

                if movement_state is not None:
                    self._movement_state[vehicle_id] = movement_state
                    self._movement_info[vehicle_id] = movement_info

                # Attach last communication and fallback position
                if vehicle_id in last_comm_map:
                    vehicle_copy.last_communication = last_comm_map[vehicle_id]
                if vehicle_copy.position is None and vehicle_id in recent_position_map:
                    vehicle_copy.position = recent_position_map[vehicle_id]

                data[vehicle_id] = vehicle_copy

            # Track successful update
            self._last_update_duration = self.hass.loop.time() - start_time
            self._last_api_call_time = self.hass.loop.time()

            _LOGGER.debug(
                "Successfully updated data with %d fields for %d vehicles in %.2fs (update #%d, %.1f%% success rate)",
                data_field_count,
                len(data),
                self._last_update_duration,
                self._update_count,
                self.success_rate,
            )

            _LOGGER.debug(
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
        # Cache trip totals to avoid heavy pagination each update
        self._trip_totals_cache: dict[str, tuple[float, int, float | None]] = {}
        self._trip_totals_last_fetch: dict[str, datetime] = {}
        self._trip_totals_last_trip_id: dict[str, str] = {}

    async def _async_update_data(self) -> CoordinatorData:
        """Fetch trip data from AutoPi API.

        Returns:
            Dictionary mapping vehicle IDs to AutoPiVehicle objects with trip data

        Raises:
            UpdateFailed: If data fetching fails
        """
        start_time = self.hass.loop.time()
        self._update_count += 1

        _LOGGER.debug(
            "Trip coordinator update #%d starting (interval: %s)",
            self._update_count,
            self.update_interval,
        )
        now_utc = datetime.now(UTC)

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
                    total_duration_seconds=0,
                    average_speed_kmh=None,
                    last_communication=vehicle.last_communication,
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

                    # Calculate total distance and duration from all trips (paginated)
                    last_fetch = self._trip_totals_last_fetch.get(vehicle_id)
                    should_refresh = (
                        vehicle_id not in self._trip_totals_cache
                        or (
                            vehicle_copy.last_trip
                            and self._trip_totals_last_trip_id.get(vehicle_id)
                            != vehicle_copy.last_trip.trip_id
                        )
                        or (
                            last_fetch is not None
                            and now_utc - last_fetch > timedelta(hours=6)
                        )
                    )

                    if should_refresh:
                        total_distance, total_duration, avg_speed = (
                            await self._calculate_trip_totals(vehicle, device_id)
                        )
                        self._trip_totals_cache[vehicle_id] = (
                            total_distance,
                            total_duration,
                            avg_speed,
                        )
                        self._trip_totals_last_fetch[vehicle_id] = now_utc
                        if vehicle_copy.last_trip:
                            self._trip_totals_last_trip_id[vehicle_id] = (
                                vehicle_copy.last_trip.trip_id
                            )
                    else:
                        total_distance, total_duration, avg_speed = (
                            self._trip_totals_cache.get(vehicle_id, (0.0, 0, None))
                        )

                    vehicle_copy.total_distance_km = total_distance
                    vehicle_copy.total_duration_seconds = total_duration
                    vehicle_copy.average_speed_kmh = avg_speed

                except (
                    AutoPiConnectionError,
                    AutoPiAPIError,
                    AutoPiTimeoutError,
                ) as err:
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

            _LOGGER.debug(
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

            _LOGGER.debug(
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

    async def _calculate_trip_totals(
        self, vehicle: AutoPiVehicle, device_id: str | None
    ) -> tuple[float, int, float | None]:
        """Calculate total distance and duration across all trips."""
        if self._client is None:
            return 0.0, 0, None

        total_distance = 0.0
        total_duration = 0
        limit = 500
        offset = 0

        while True:
            self._total_api_calls += 1
            response = await self._client.get_trips_page(
                vehicle.id, device_id, limit=limit, offset=offset
            )
            results = response.get("results", [])
            if not results:
                break

            for trip_data in results:
                try:
                    trip = AutoPiTrip.from_api_data(trip_data)
                except (KeyError, ValueError, TypeError):
                    continue
                total_distance += trip.distance_km
                total_duration += trip.duration_seconds

            offset += limit
            if offset >= response.get("count", 0):
                break

        avg_speed = None
        if total_duration > 0:
            avg_speed = round(total_distance / (total_duration / 3600), 2)

        return total_distance, total_duration, avg_speed

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

        _LOGGER.debug(
            "Fired trip_completed event for vehicle %s: %.1f km in %d minutes",
            vehicle.name,
            trip.distance_km,
            trip.duration_seconds // 60,
        )
