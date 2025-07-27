"""Support for AutoPi binary sensors."""

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
    """Set up AutoPi binary sensors from a config entry."""
    _LOGGER.debug(
        "Binary sensor platform loaded for AutoPi, but no binary sensors implemented yet"
    )
    # Future implementation will add binary sensors for:
    # - Engine running status
    # - Door open/closed status
    # - Vehicle connected/disconnected status
    # - etc. 