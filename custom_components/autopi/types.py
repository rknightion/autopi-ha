"""Type definitions for the AutoPi integration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
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
        now = datetime.now()
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
        duration_parts = data["duration"].split(":")
        duration_seconds = int(duration_parts[0]) * 3600 + int(duration_parts[1]) * 60 + int(duration_parts[2])

        # Extract addresses from display data
        start_address = None
        start_display = data.get("start_position_display")
        if start_display:
            start_address = start_display.get("address")

        end_address = None
        end_display = data.get("end_position_display")
        if end_display:
            end_address = end_display.get("address")

        return cls(
            trip_id=data["id"],
            start_time=datetime.fromisoformat(data["start_time_utc"].replace("Z", "+00:00")),
            end_time=datetime.fromisoformat(data["end_time_utc"].replace("Z", "+00:00")),
            start_lat=float(data["start_position_lat"]),
            start_lng=float(data["start_position_lng"]),
            start_address=start_address,
            end_lat=float(data["end_position_lat"]),
            end_lng=float(data["end_position_lng"]),
            end_address=end_address,
            vehicle_id=data["vehicle"],
            duration_seconds=duration_seconds,
            distance_km=data["distanceKm"],
            state=data["state"],
        )
