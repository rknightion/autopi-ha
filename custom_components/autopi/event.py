"""Event entities for AutoPi integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.event import EventEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import AutoPiDataUpdateCoordinator
from .entities.base import AutoPiVehicleEntity

_LOGGER = logging.getLogger(__name__)


class AutoPiVehicleEvent(AutoPiVehicleEntity, EventEntity):
    """Event entity for AutoPi vehicle events."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: AutoPiDataUpdateCoordinator,
        vehicle_id: str,
    ) -> None:
        """Initialize the event entity.

        Args:
            coordinator: The data update coordinator
            vehicle_id: The vehicle ID
        """
        super().__init__(coordinator, vehicle_id, "events")
        self._attr_translation_key = "vehicle_events"

        # Get all device IDs for this vehicle
        self._device_ids = self.vehicle.devices if self.vehicle else []

        # Event types this entity will handle
        self._attr_event_types = [
            "charging",
            "charging_slow",
            "discharging",
            "engine_start",
            "engine_stop",
            "trip_start",
            "trip_end",
            "alert",
            "warning",
            "error",
        ]

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return "Events"

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.vehicle is not None and len(self._device_ids) > 0

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()

        # Listen for device events from our devices
        @callback
        def _handle_event(event_data: dict[str, Any]) -> None:
            """Handle device events."""
            device_id = event_data.get("device_id")
            vehicle_id = event_data.get("vehicle_id")

            # Only process events for our vehicle
            if vehicle_id == self._vehicle_id and device_id in self._device_ids:
                # Trigger the event entity
                self._trigger_event(
                    event_data.get("event_type", "unknown"),
                    {
                        "device_id": device_id,
                        "timestamp": event_data.get("timestamp"),
                        "tag": event_data.get("tag"),
                        "area": event_data.get("area"),
                        "data": event_data.get("data", {}),
                    }
                )
                self.async_write_ha_state()

        # Subscribe to device events
        self.hass.bus.async_listen(
            f"{DOMAIN}_device_event",
            lambda event: _handle_event(event.data),
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        attrs = dict(super().extra_state_attributes or {})

        # Add recent events from all devices
        recent_events = []
        for device_id in self._device_ids:
            events = self.coordinator.get_device_events(device_id)
            for event in events[:2]:  # Last 2 events per device
                recent_events.append({
                    "device_id": device_id,
                    "timestamp": event.timestamp.isoformat(),
                    "area": event.area,
                    "event": event.event_type,
                    "tag": event.tag,
                })

        # Sort by timestamp (newest first)
        recent_events.sort(key=lambda x: x["timestamp"], reverse=True)
        attrs["recent_events"] = recent_events[:10]  # Keep last 10 events total

        return attrs


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up AutoPi event entities from config entry.

    Args:
        hass: Home Assistant instance
        config_entry: Configuration entry
        async_add_entities: Callback to add entities
    """
    _LOGGER.debug("Setting up AutoPi event entities")

    # Get the coordinator from hass data
    coordinator: AutoPiDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id][
        "coordinator"
    ]

    # Create event entities for each vehicle
    entities = []
    if coordinator.data:
        for vehicle_id in coordinator.data:
            _LOGGER.debug("Creating event entity for vehicle %s", vehicle_id)
            entities.append(
                AutoPiVehicleEvent(
                    coordinator=coordinator,
                    vehicle_id=vehicle_id,
                )
            )

    if entities:
        _LOGGER.info("Adding %d AutoPi event entities", len(entities))
        async_add_entities(entities)
    else:
        _LOGGER.warning("No vehicles found for event entities")
