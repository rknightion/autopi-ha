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