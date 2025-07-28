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
