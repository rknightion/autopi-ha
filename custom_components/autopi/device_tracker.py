"""Support for AutoPi device tracking."""
from __future__ import annotations

from homeassistant.components.device_tracker import TrackerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up AutoPi device trackers from a config entry."""
    # This is a placeholder - actual implementation would create trackers
    # based on discovered AutoPi devices with GPS capability
    pass


class AutoPiDeviceTracker(TrackerEntity):
    """Representation of an AutoPi device tracker."""

    def __init__(self, device_id: str) -> None:
        """Initialize the device tracker."""
        self._device_id = device_id
        self._attr_unique_id = f"{device_id}_tracker"
        self._attr_name = f"AutoPi {device_id}"

    @property
    def device_info(self):
        """Return device information for this tracker."""
        return {
            "identifiers": {(DOMAIN, self._device_id)},
            "name": f"AutoPi {self._device_id}",
            "manufacturer": "AutoPi.io",
            "model": "AutoPi Device",
        } 