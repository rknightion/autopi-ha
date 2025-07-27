"""Support for AutoPi sensors."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, MANUFACTURER
from .coordinator import AutoPiDataUpdateCoordinator
from .entities.base import AutoPiEntity, AutoPiVehicleEntity
from .types import AutoPiVehicle

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up AutoPi sensors from a config entry."""
    coordinator: AutoPiDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    _LOGGER.debug(
        "Setting up AutoPi sensors for config entry %s",
        config_entry.entry_id
    )

    entities: list[SensorEntity] = []

    # Add vehicle count sensor
    entities.append(AutoPiVehicleCountSensor(coordinator))

    # Add individual vehicle sensors
    if coordinator.data:
        for vehicle_id, vehicle in coordinator.data.items():
            _LOGGER.debug(
                "Creating vehicle sensor for %s (%s)",
                vehicle.name,
                vehicle_id
            )
            entities.append(AutoPiVehicleSensor(coordinator, vehicle_id))

    _LOGGER.info(
        "Adding %d AutoPi sensor entities",
        len(entities)
    )

    async_add_entities(entities)


class AutoPiVehicleCountSensor(AutoPiEntity, SensorEntity):
    """Sensor showing the total number of vehicles."""

    _attr_device_class = SensorDeviceClass.MEASUREMENT
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "vehicles"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:car-multiple"

    def __init__(self, coordinator: AutoPiDataUpdateCoordinator) -> None:
        """Initialize the vehicle count sensor."""
        super().__init__(coordinator, "vehicle_count")
        self._attr_name = "Vehicle Count"

        _LOGGER.debug("Initialized AutoPi vehicle count sensor")

    @property
    def native_value(self) -> int:
        """Return the number of vehicles."""
        return self.coordinator.get_vehicle_count()

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.config_entry.entry_id)},
            name="AutoPi Integration",
            manufacturer=MANUFACTURER,
            configuration_url="https://app.autopi.io",
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        if not self.coordinator.data:
            return {}

        return {
            "vehicles": [
                {
                    "id": vehicle.id,
                    "name": vehicle.name,
                    "license_plate": vehicle.license_plate,
                }
                for vehicle in self.coordinator.data.values()
            ]
        }


class AutoPiVehicleSensor(AutoPiVehicleEntity, SensorEntity):
    """Sensor representing an individual vehicle."""

    _attr_icon = "mdi:car"

    def __init__(
        self,
        coordinator: AutoPiDataUpdateCoordinator,
        vehicle_id: str,
    ) -> None:
        """Initialize the vehicle sensor."""
        super().__init__(coordinator, vehicle_id, "vehicle")
        
        _LOGGER.debug(
            "Initialized AutoPi vehicle sensor for vehicle %s",
            vehicle_id
        )

    @property
    def name(self) -> str | None:
        """Return the name of the sensor."""
        if vehicle := self.vehicle:
            return vehicle.name
        return None

    @property
    def native_value(self) -> str | None:
        """Return the state of the sensor."""
        if vehicle := self.vehicle:
            return vehicle.license_plate or vehicle.name
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        attrs = super().extra_state_attributes
        
        if vehicle := self.vehicle:
            # Add any additional vehicle-specific attributes
            attrs.update({
                "name": vehicle.name,
            })
        
        return attrs 