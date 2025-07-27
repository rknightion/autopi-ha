"""Support for AutoPi device tracking."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up AutoPi device trackers from a config entry."""
    _LOGGER.debug(
        "Device tracker platform loaded for AutoPi, but no trackers implemented yet"
    )
    # Future implementation will add device trackers for:
    # - Vehicle GPS location tracking
    # - Geofencing support
    # - Trip tracking
    # - etc.
