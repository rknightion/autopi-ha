"""Base entity for AutoPi integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ..const import DOMAIN, MANUFACTURER
from ..coordinator import AutoPiDataUpdateCoordinator
from ..types import AutoPiVehicle

_LOGGER = logging.getLogger(__name__)


class AutoPiEntity(CoordinatorEntity[AutoPiDataUpdateCoordinator], Entity):
    """Base entity for AutoPi integration."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: AutoPiDataUpdateCoordinator,
        unique_id_suffix: str | None = None,
    ) -> None:
        """Initialize the entity.

        Args:
            coordinator: The data coordinator
            unique_id_suffix: Optional suffix for the unique ID
        """
        super().__init__(coordinator)

        # Set unique ID
        entry_id = coordinator.config_entry.entry_id
        if unique_id_suffix:
            self._attr_unique_id = f"{entry_id}_{unique_id_suffix}"
        else:
            self._attr_unique_id = entry_id

        _LOGGER.debug(
            "Initialized AutoPi entity with unique_id: %s",
            self._attr_unique_id
        )


class AutoPiVehicleEntity(AutoPiEntity):
    """Base entity for a specific AutoPi vehicle."""

    def __init__(
        self,
        coordinator: AutoPiDataUpdateCoordinator,
        vehicle_id: str,
        entity_suffix: str,
    ) -> None:
        """Initialize the vehicle entity.

        Args:
            coordinator: The data coordinator
            vehicle_id: The vehicle ID
            entity_suffix: Suffix for the entity unique ID
        """
        super().__init__(
            coordinator,
            unique_id_suffix=f"vehicle_{vehicle_id}_{entity_suffix}"
        )
        self._vehicle_id = vehicle_id

        _LOGGER.debug(
            "Initialized AutoPi vehicle entity for vehicle %s with suffix %s",
            vehicle_id,
            entity_suffix
        )

    @property
    def vehicle(self) -> AutoPiVehicle | None:
        """Get the vehicle data."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get(self._vehicle_id)

    @property
    def device_info(self) -> DeviceInfo | None:
        """Return device information."""
        vehicle = self.vehicle
        if not vehicle:
            return None

        return DeviceInfo(
            identifiers={(DOMAIN, f"vehicle_{vehicle.id}")},
            name=vehicle.name,
            manufacturer=MANUFACTURER,
            model=f"{vehicle.type} Vehicle",
            configuration_url="https://app.autopi.io",
            sw_version=None,  # Could be populated if API provides firmware version
        )

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return super().available and self.vehicle is not None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        vehicle = self.vehicle
        if not vehicle:
            return {}

        return {
            "vehicle_id": vehicle.id,
            "license_plate": vehicle.license_plate,
            "vin": vehicle.vin,
            "year": vehicle.year,
            "type": vehicle.type,
            "battery_voltage": vehicle.battery_voltage,
            "make_id": vehicle.make_id,
            "model_id": vehicle.model_id,
            "devices": vehicle.devices,
        }