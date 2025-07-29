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
        # Include all possible AutoPi event types based on API analysis
        self._attr_event_types = [
            # Battery events
            "charging",
            "charging_slow",
            "discharging",
            "critical_level",  # Battery critical level
            # Engine/Trip events
            "start",  # Trip start (from API)
            "stop",  # Trip stop (from API)
            "engine_start",  # Keep for compatibility
            "engine_stop",  # Keep for compatibility
            "trip_start",  # Keep for compatibility
            "trip_end",  # Keep for compatibility
            # Movement events
            "standstill",
            "moving",
            # Alert events
            "alert",
            "warning",
            "error",
            # Generic fallback
            "unknown",
            "unkown",  # Typo in API data, but we handle it  # codespell:ignore
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
        def _handle_event(event: Any) -> None:
            """Handle device events."""
            try:
                event_data = event.data
                device_id = event_data.get("device_id")
                vehicle_id = event_data.get("vehicle_id")

                _LOGGER.debug(
                    "Received event for device %s, vehicle %s (our vehicle: %s)",
                    device_id,
                    vehicle_id,
                    self._vehicle_id,
                )

                # Only process events for our vehicle
                if vehicle_id == self._vehicle_id and device_id in self._device_ids:
                    # Map the event type or use the original if it's in our list
                    event_type = event_data.get("event_type", "unknown")
                    if event_type not in self._attr_event_types:
                        _LOGGER.warning(
                            "Unknown event type '%s' from device %s, mapping to 'unknown'",
                            event_type,
                            device_id,
                        )
                        event_type = "unknown"

                    _LOGGER.debug(
                        "Processing %s event from device %s for vehicle %s",
                        event_type,
                        device_id,
                        vehicle_id,
                    )

                    # Trigger the event entity
                    self._trigger_event(
                        event_type,
                        {
                            "device_id": device_id,
                            "timestamp": event_data.get("timestamp"),
                            "tag": event_data.get("tag"),
                            "area": event_data.get("area"),
                            "data": event_data.get("data", {}),
                            "original_event_type": event_data.get("event_type"),
                        },
                    )
                    self.async_write_ha_state()

                    _LOGGER.info(
                        "Triggered %s event for vehicle %s",
                        event_type,
                        self._vehicle_id,
                    )

            except Exception as e:
                _LOGGER.error(
                    "Error handling event for vehicle %s: %s",
                    self._vehicle_id,
                    str(e),
                    exc_info=True,
                )

        # Subscribe to device events
        self.async_on_remove(
            self.hass.bus.async_listen(
                f"{DOMAIN}_device_event",
                _handle_event,
            )
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
                recent_events.append(
                    {
                        "device_id": device_id,
                        "timestamp": event.timestamp.isoformat(),
                        "area": event.area,
                        "event": event.event_type,
                        "tag": event.tag,
                    }
                )

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
