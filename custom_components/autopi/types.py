"""Type definitions for the AutoPi integration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, TypedDict

from homeassistant.config_entries import ConfigEntry


class VehicleData(TypedDict):
    """TypedDict for vehicle data from API."""

    id: int
    vin: str
    callName: str
    licensePlate: str
    model: int
    make: int
    year: int
    busses: list[Any]
    type: str
    devices: list[str]
    battery_nominal_voltage: int


class VehicleProfileResponse(TypedDict):
    """TypedDict for vehicle profile API response."""

    count: int
    results: list[VehicleData]
    page_size: int


class LocationData(TypedDict):
    """TypedDict for location data."""

    lat: float
    lon: float


class PositionData(TypedDict):
    """TypedDict for position data from API."""

    ts: str
    utc: None | str
    course_over_ground: float
    speed_over_ground: float
    altitude: float
    nsat: int
    location: LocationData


class DevicePositionData(TypedDict):
    """Type definition for device position entry from bulk API."""

    ts: str
    unit_id: str
    id: str
    display: str
    last_communication: str
    positions: list[PositionData]


@dataclass
class VehiclePosition:
    """Represents a vehicle's position data."""

    timestamp: datetime
    latitude: float
    longitude: float
    altitude: float
    speed: float
    course: float
    num_satellites: int

    @property
    def location_accuracy(self) -> float:
        """Calculate location accuracy based on number of satellites."""
        if self.num_satellites < 4:
            return 100.0
        elif self.num_satellites == 4:
            return 30.0
        elif self.num_satellites == 5:
            return 20.0
        elif self.num_satellites == 6:
            return 15.0
        elif self.num_satellites == 7:
            return 11.0
        elif self.num_satellites in (8, 9):
            return 7.5
        elif self.num_satellites in (10, 11):
            return 5.0
        else:  # 12+
            return 3.0

    @classmethod
    def from_api_data(cls, data: PositionData) -> VehiclePosition:
        """Create VehiclePosition from API data."""
        return cls(
            timestamp=datetime.fromisoformat(data["ts"].replace("Z", "+00:00")),
            latitude=data["location"]["lat"],
            longitude=data["location"]["lon"],
            altitude=data["altitude"],
            speed=data["speed_over_ground"],
            course=data["course_over_ground"],
            num_satellites=data["nsat"],
        )


@dataclass
class AutoPiVehicle:
    """Represents an AutoPi vehicle."""

    id: int
    name: str
    license_plate: str
    vin: str
    year: int
    type: str
    battery_voltage: int
    devices: list[str]
    make_id: int
    model_id: int
    position: VehiclePosition | None = None
    data_fields: dict[str, DataFieldValue] | None = None
    trip_count: int = 0
    last_trip: AutoPiTrip | None = None
    total_distance_km: float = 0.0
    total_duration_seconds: int = 0
    average_speed_kmh: float | None = None
    last_communication: datetime | None = None

    @property
    def unique_id(self) -> str:
        """Return unique ID for this vehicle."""
        return f"autopi_vehicle_{self.id}"

    @classmethod
    def from_api_data(cls, data: VehicleData) -> AutoPiVehicle:
        """Create AutoPiVehicle from API data.

        Args:
            data: Vehicle data from API

        Returns:
            AutoPiVehicle instance
        """
        return cls(
            id=data["id"],
            name=data["callName"] or data["licensePlate"] or f"Vehicle {data['id']}",
            license_plate=data["licensePlate"],
            vin=data["vin"],
            year=data["year"],
            type=data["type"],
            battery_voltage=data["battery_nominal_voltage"],
            devices=data["devices"],
            make_id=data["make"],
            model_id=data["model"],
        )


CoordinatorData = dict[str, AutoPiVehicle]


class AutoPiData:
    """Data storage for the AutoPi integration."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize AutoPi data.

        Args:
            config_entry: The config entry for this integration
        """
        self.config_entry = config_entry
        self.vehicles: dict[str, AutoPiVehicle] = {}
        self.last_update: datetime | None = None


class DataFieldLocation(TypedDict):
    """Location data in data field response."""

    lat: float
    lon: float


class TripPositionDisplay(TypedDict):
    """Position display data for trip endpoints."""

    city: str | None
    county: str | None
    address: str | None
    country: str | None
    latitude: str | None
    provider: str | None
    longitude: str | None
    precision: str | None
    postal_code: str | None
    country_code: str | None


class TripData(TypedDict):
    """Trip data from API."""

    id: str
    start_time_utc: str
    end_time_utc: str
    start_position_lat: str
    start_position_lng: str
    start_position_display: TripPositionDisplay | None
    end_position_lat: str
    end_position_lng: str
    end_position_display: TripPositionDisplay | None
    vehicle: int
    duration: str
    distanceKm: float
    tag: str
    last_recalc: str
    state: str


class TripsResponse(TypedDict):
    """Trips API response."""

    count: int
    results: list[TripData]
    page_size: int


class DataFieldResponse(TypedDict):
    """Type definition for a single data field from the API."""

    field_prefix: str
    field_name: str
    frequency: float
    type: str
    title: str
    last_seen: str
    last_value: int | float | str | dict[str, Any] | DataFieldLocation
    description: str


@dataclass
class DataFieldValue:
    """Represents a single data field value with metadata."""

    field_prefix: str
    field_name: str
    frequency: float
    value_type: str
    title: str
    last_seen: datetime
    last_value: Any
    description: str
    last_update: datetime  # When we last received this data

    @property
    def field_id(self) -> str:
        """Get the unique field identifier."""
        return f"{self.field_prefix}.{self.field_name}"

    @classmethod
    def from_api_data(cls, data: DataFieldResponse) -> DataFieldValue:
        """Create DataFieldValue from API data."""
        now = datetime.now(UTC)
        return cls(
            field_prefix=data["field_prefix"],
            field_name=data["field_name"],
            frequency=data["frequency"],
            value_type=data["type"],
            title=data["title"],
            last_seen=datetime.fromisoformat(data["last_seen"].replace("Z", "+00:00")),
            last_value=data["last_value"],
            description=data["description"],
            last_update=now,
        )


@dataclass
class AutoPiTrip:
    """Represents a trip from the AutoPi system."""

    trip_id: str
    start_time: datetime
    end_time: datetime
    start_lat: float
    start_lng: float
    start_address: str | None
    end_lat: float
    end_lng: float
    end_address: str | None
    vehicle_id: int
    duration_seconds: int
    distance_km: float
    state: str

    @classmethod
    def from_api_data(cls, data: TripData) -> AutoPiTrip:
        """Create AutoPiTrip from API data."""
        # Parse duration string "HH:MM:SS" to seconds
        # Duration is None for in-progress trips
        duration_seconds = 0
        duration_str = data.get("duration")
        if duration_str and isinstance(duration_str, str) and ":" in duration_str:
            try:
                duration_parts = duration_str.split(":")
                if len(duration_parts) == 3:
                    duration_seconds = (
                        int(duration_parts[0]) * 3600
                        + int(duration_parts[1]) * 60
                        + int(duration_parts[2])
                    )
            except (ValueError, TypeError):
                # If parsing fails, leave duration as 0
                pass
        elif duration_str is None and data.get("state") in ("in_progress", "started"):
            # For in-progress trips, calculate duration from start time
            try:
                start_time = datetime.fromisoformat(
                    data["start_time_utc"].replace("Z", "+00:00")
                )
                duration_seconds = int(
                    (datetime.now(start_time.tzinfo) - start_time).total_seconds()
                )
            except (ValueError, TypeError):
                # If parsing fails, duration remains 0
                duration_seconds = 0

        # Extract addresses from display data
        start_address = None
        start_display = data.get("start_position_display")
        if start_display:
            start_address = start_display.get("address")

        end_address = None
        end_display = data.get("end_position_display")
        if end_display:
            end_address = end_display.get("address")

        # Handle end_time_utc - can be empty string for in-progress trips
        end_time = datetime.now(UTC)  # Default to now for in-progress trips
        end_time_str = data.get("end_time_utc", "")
        if end_time_str and end_time_str.strip():  # Check for non-empty string
            try:
                end_time = datetime.fromisoformat(end_time_str.replace("Z", "+00:00"))
            except ValueError:
                # If parsing fails, use start time as fallback
                end_time = datetime.fromisoformat(
                    data["start_time_utc"].replace("Z", "+00:00")
                )

        # Handle end position - can be None for in-progress trips
        end_lat = 0.0
        end_lng = 0.0
        end_lat_str = data.get("end_position_lat")
        end_lng_str = data.get("end_position_lng")

        if end_lat_str is not None and end_lat_str != "":
            try:
                end_lat = float(end_lat_str)
            except (ValueError, TypeError):
                # If parsing fails, use start position as fallback
                end_lat = float(data["start_position_lat"])

        if end_lng_str is not None and end_lng_str != "":
            try:
                end_lng = float(end_lng_str)
            except (ValueError, TypeError):
                # If parsing fails, use start position as fallback
                end_lng = float(data["start_position_lng"])

        return cls(
            trip_id=data["id"],
            start_time=datetime.fromisoformat(
                data["start_time_utc"].replace("Z", "+00:00")
            ),
            end_time=end_time,
            start_lat=float(data["start_position_lat"]),
            start_lng=float(data["start_position_lng"]),
            start_address=start_address,
            end_lat=end_lat,
            end_lng=end_lng,
            end_address=end_address,
            vehicle_id=data["vehicle"],
            duration_seconds=duration_seconds,
            distance_km=data["distanceKm"],
            state=data["state"],
        )


class AlertDict(TypedDict):
    """Alert information from fleet alerts API."""

    title: str
    uuid: str
    vehicle_count: int


class SeverityDict(TypedDict):
    """Severity grouping from fleet alerts API."""

    severity: str
    alerts: list[AlertDict]


class AlertsData(TypedDict):
    """Fleet alerts response from API."""

    total: int
    severities: list[SeverityDict]


@dataclass
class FleetAlert:
    """Represents a fleet-wide alert."""

    alert_id: str
    title: str
    severity: str
    vehicle_count: int

    @classmethod
    def from_api_data(cls, severity: str, alert_data: AlertDict) -> FleetAlert:
        """Create FleetAlert from API data."""
        return cls(
            alert_id=alert_data["uuid"],
            title=alert_data["title"],
            severity=severity,
            vehicle_count=alert_data["vehicle_count"],
        )


class EventDataDict(TypedDict):
    """Event data dictionary from API."""

    # This is a flexible dict that can contain various event-specific fields


class EventDict(TypedDict):
    """Event from AutoPi API."""

    ts: str
    data: list[EventDataDict]
    tag: str
    area: str
    event: str


class EventsResponse(TypedDict):
    """Events API response."""

    results: list[EventDict]
    count: int
    page_size: int


@dataclass
class AutoPiEvent:
    """Represents an AutoPi event."""

    timestamp: datetime
    tag: str
    area: str
    event_type: str
    data: dict[str, Any]
    device_id: str

    @property
    def unique_id(self) -> str:
        """Get unique identifier for this event."""
        return f"{self.device_id}_{self.timestamp.isoformat()}_{self.tag}"

    @classmethod
    def from_api_data(cls, data: EventDict, device_id: str) -> AutoPiEvent:
        """Create AutoPiEvent from API data."""
        # Merge all data dicts into one
        merged_data: dict[str, Any] = {}
        for data_item in data.get("data", []):
            merged_data.update(data_item)

        return cls(
            timestamp=datetime.fromisoformat(data["ts"].replace("Z", "+00:00")),
            tag=data["tag"],
            area=data["area"],
            event_type=data["event"],
            data=merged_data,
            device_id=device_id,
        )


@dataclass
class RecentStatEvent:
    """Parsed recent stats event."""

    timestamp: datetime
    tag: str | None
    event_type: str | None

    @classmethod
    def from_api_data(cls, data: dict[str, Any]) -> RecentStatEvent | None:
        """Create RecentStatEvent from API data."""
        timestamp = data.get("@ts") or data.get("ts")
        if not timestamp:
            return None
        try:
            parsed_ts = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except ValueError:
            return None
        return cls(
            timestamp=parsed_ts,
            tag=data.get("@tag") or data.get("tag"),
            event_type=data.get("@t") or data.get("type"),
        )


@dataclass
class DeviceMostRecentPosition:
    """Most recent position payload for a device."""

    device_id: str
    unit_id: str | None
    display_name: str | None
    last_communication: datetime | None
    position: VehiclePosition | None

    @classmethod
    def from_api_data(cls, data: DevicePositionData) -> DeviceMostRecentPosition:
        """Create DeviceMostRecentPosition from API data."""
        last_comm = None
        last_comm_raw = data.get("last_communication")
        if last_comm_raw:
            try:
                last_comm = datetime.fromisoformat(last_comm_raw.replace("Z", "+00:00"))
            except ValueError:
                last_comm = None

        position = None
        positions = data.get("positions", [])
        if positions:
            try:
                position = VehiclePosition.from_api_data(positions[0])
            except (KeyError, ValueError, TypeError):
                position = None

        return cls(
            device_id=data.get("id", ""),
            unit_id=data.get("unit_id"),
            display_name=data.get("display"),
            last_communication=last_comm,
            position=position,
        )


@dataclass
class ChargingSession:
    """Charging session information."""

    start: datetime | None
    end: datetime | None
    duration_seconds: int | None
    state: str | None
    start_tag: str | None
    end_tag: str | None

    @classmethod
    def from_api_data(cls, data: dict[str, Any]) -> ChargingSession:
        """Create ChargingSession from API data."""
        def _parse_dt(value: str | None) -> datetime | None:
            if not value:
                return None
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return None

        duration_seconds = None
        duration_raw = data.get("duration")
        if isinstance(duration_raw, str) and ":" in duration_raw:
            parts = duration_raw.split(":")
            if len(parts) == 3:
                try:
                    duration_seconds = (
                        int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                    )
                except ValueError:
                    duration_seconds = None

        return cls(
            start=_parse_dt(data.get("start")),
            end=_parse_dt(data.get("end")),
            duration_seconds=duration_seconds,
            state=data.get("state"),
            start_tag=data.get("start_tag"),
            end_tag=data.get("end_tag"),
        )


@dataclass
class FleetAlertSummary:
    """Fleet alerts summary."""

    open: int
    critical: int
    high: int
    medium: int
    low: int

    @classmethod
    def from_api_data(cls, data: dict[str, Any]) -> FleetAlertSummary:
        """Create FleetAlertSummary from API data."""
        return cls(
            open=int(data.get("open", 0)),
            critical=int(data.get("critical", 0)),
            high=int(data.get("high", 0)),
            medium=int(data.get("medium", 0)),
            low=int(data.get("low", 0)),
        )


@dataclass
class DtcEntry:
    """Diagnostic trouble code entry."""

    code: str
    description: str | None
    occurred_at: datetime | None

    @classmethod
    def from_api_data(cls, data: dict[str, Any]) -> DtcEntry:
        """Create DtcEntry from API data."""
        occurred = None
        occurred_raw = data.get("occurred_at_utc") or data.get("occurred_at")
        if occurred_raw:
            try:
                occurred = datetime.fromisoformat(occurred_raw.replace("Z", "+00:00"))
            except ValueError:
                occurred = None
        return cls(
            code=str(data.get("dtc_code") or data.get("code") or ""),
            description=data.get("description") or data.get("text"),
            occurred_at=occurred,
        )


@dataclass
class GeofenceSummary:
    """Geofence summary counts."""

    location_count: int
    geofence_count: int
    last_entered: datetime | None
    last_exited: datetime | None


@dataclass
class FleetVehicleSummary:
    """Fleet vehicle activity summary."""

    all_vehicles: int
    active_now: int
    driven_last_30_days: int
    on_location: int


@dataclass
class SimplifiedEvent:
    """Simplified event entry."""

    timestamp: datetime
    tag: str | None
    event_type: str | None
    area: str | None
    name: str | None

    @classmethod
    def from_api_data(cls, data: dict[str, Any]) -> SimplifiedEvent | None:
        """Create SimplifiedEvent from API data."""
        ts = data.get("ts")
        if not ts:
            return None
        try:
            timestamp = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except ValueError:
            return None
        return cls(
            timestamp=timestamp,
            tag=data.get("tag"),
            event_type=data.get("event"),
            area=data.get("area"),
            name=data.get("name"),
        )


@dataclass
class RfidEvent:
    """RFID event entry."""

    timestamp: datetime
    status: str | None
    token: str | None
    user_email: str | None
    vehicle_id: int | None

    @classmethod
    def from_api_data(cls, data: dict[str, Any]) -> RfidEvent | None:
        """Create RfidEvent from API data."""
        ts = data.get("ts")
        if not ts:
            return None
        try:
            timestamp = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except ValueError:
            return None
        user = data.get("user") or {}
        vehicle = data.get("vehicle") or {}
        vehicle_id = vehicle.get("id")
        return cls(
            timestamp=timestamp,
            status=data.get("status"),
            token=data.get("token"),
            user_email=user.get("email"),
            vehicle_id=vehicle_id if isinstance(vehicle_id, int) else None,
        )
