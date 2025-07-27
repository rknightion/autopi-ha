"""Support for AutoPi binary sensors."""
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up AutoPi binary sensors from a config entry."""
    # This is a placeholder - actual implementation would create binary sensors
    # for vehicle status indicators like engine running, doors open, etc.
    pass


class AutoPiBinarySensor(BinarySensorEntity):
    """Representation of an AutoPi binary sensor."""

    def __init__(self, device_id: str, sensor_type: str) -> None:
        """Initialize the binary sensor."""
        self._device_id = device_id
        self._sensor_type = sensor_type
        self._attr_unique_id = f"{device_id}_{sensor_type}"
        self._attr_name = f"AutoPi {device_id} {sensor_type.replace('_', ' ').title()}"

    @property
    def device_info(self):
        """Return device information for this sensor."""
        return {
            "identifiers": {(DOMAIN, self._device_id)},
            "name": f"AutoPi {self._device_id}",
            "manufacturer": "AutoPi.io",
            "model": "AutoPi Device",
        } 