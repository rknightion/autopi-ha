"""Support for AutoPi device tracking."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.device_tracker import SourceType
from homeassistant.components.device_tracker.config_entry import TrackerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
)
from .coordinator import AutoPiDataUpdateCoordinator
from .entities.base import AutoPiVehicleEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up AutoPi device tracker from a config entry."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    position_coordinator: AutoPiDataUpdateCoordinator = data["position_coordinator"]

    # Create device tracker entities for all vehicles with position data
    entities = [
        AutoPiDeviceTracker(position_coordinator, vehicle_id)
        for vehicle_id in position_coordinator.data
        if position_coordinator.data  # Ensure data exists
    ]

    async_add_entities(entities)
    _LOGGER.debug("Added %d AutoPi device tracker entities", len(entities))


class AutoPiDeviceTracker(AutoPiVehicleEntity, TrackerEntity):
    """Representation of an AutoPi vehicle tracker."""

    def __init__(
        self,
        coordinator: AutoPiDataUpdateCoordinator,
        vehicle_id: str,
    ) -> None:
        """Initialize the device tracker.

        Args:
            coordinator: The data coordinator
            vehicle_id: The vehicle ID
        """
        super().__init__(coordinator, vehicle_id, "tracker")
        self._attr_icon = "mdi:car"

    @property
    def source_type(self) -> SourceType:
        """Return the source type, eg gps or router, of the device."""
        return SourceType.GPS

    @property
    def latitude(self) -> float | None:
        """Return latitude value of the device."""
        if self.vehicle and self.vehicle.position:
            return self.vehicle.position.latitude
        return None

    @property
    def longitude(self) -> float | None:
        """Return longitude value of the device."""
        if self.vehicle and self.vehicle.position:
            return self.vehicle.position.longitude
        return None

    @property
    def location_accuracy(self) -> int:
        """Return the location accuracy of the device.

        Value in meters.
        """
        if self.vehicle and self.vehicle.position:
            return int(self.vehicle.position.location_accuracy)
        return 0

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes of the device."""
        # Only return static vehicle attributes from parent class
        # Don't include frequently changing position data to avoid database bloat
        return super().extra_state_attributes
