"""The AutoPi integration for Home Assistant."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import (
    CONF_UPDATE_INTERVAL_FAST,
    CONF_UPDATE_INTERVAL_MEDIUM,
    CONF_UPDATE_INTERVAL_SLOW,
    DEFAULT_UPDATE_INTERVAL_FAST_MINUTES,
    DEFAULT_UPDATE_INTERVAL_MEDIUM_MINUTES,
    DEFAULT_UPDATE_INTERVAL_SLOW_MINUTES,
    DOMAIN,
    PLATFORMS,
    UPDATE_RING_FAST,
    UPDATE_RING_MEDIUM,
    UPDATE_RING_SLOW,
)
from .coordinator import AutoPiDataUpdateCoordinator, AutoPiPositionCoordinator

_LOGGER = logging.getLogger(__name__)


# Suppress verbose logging from third-party libraries
def _setup_logging():
    """Configure logging to suppress verbose third-party output."""
    third_party_loggers = [
        "aiohttp",
    ]

    if _LOGGER.getEffectiveLevel() > logging.DEBUG:
        for logger_name in third_party_loggers:
            logger = logging.getLogger(logger_name)
            logger.setLevel(logging.ERROR)
            logger.propagate = False

    _LOGGER.debug(
        "Configured logging for %d third-party libraries", len(third_party_loggers)
    )


# Initialize logging configuration
_setup_logging()


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up AutoPi from a config entry.

    Args:
        hass: Home Assistant instance
        entry: Configuration entry to set up

    Returns:
        bool: True if setup successful

    Raises:
        ConfigEntryNotReady: If unable to connect to AutoPi API
    """
    _LOGGER.info("Setting up AutoPi integration (entry_id: %s)", entry.entry_id)

    _LOGGER.debug(
        "Integration setup started - Entry ID: %s, Title: %s, Domain: %s",
        entry.entry_id,
        entry.title,
        entry.domain,
    )

    # Create coordinators dictionary
    coordinators = {}

    # Create the medium update coordinator (base vehicle data)
    _LOGGER.info("Creating base vehicle data coordinator")
    coordinator = AutoPiDataUpdateCoordinator(hass, entry, UPDATE_RING_MEDIUM)
    coordinators[UPDATE_RING_MEDIUM] = coordinator

    # Perform initial data fetch
    try:
        _LOGGER.debug("Performing initial data fetch for base vehicle data")
        await coordinator.async_config_entry_first_refresh()
        _LOGGER.info(
            "Initial data fetch successful, found %d vehicles",
            coordinator.get_vehicle_count(),
        )
    except Exception as err:
        _LOGGER.error("Failed to fetch initial data: %s", err)
        raise ConfigEntryNotReady(f"Unable to connect to AutoPi API: {err}") from err

    # Create position coordinator for fast updates (independent of base coordinator)
    _LOGGER.info("Creating position data coordinator")
    position_coordinator = AutoPiPositionCoordinator(hass, entry, coordinator)
    coordinators[UPDATE_RING_FAST] = position_coordinator

    # Perform initial position data fetch in parallel
    try:
        _LOGGER.debug("Performing initial position data fetch")
        await position_coordinator.async_config_entry_first_refresh()
        _LOGGER.info("Initial position data fetch successful")
    except Exception as err:
        # Position fetch failures are not critical
        _LOGGER.warning("Failed to fetch initial position data: %s", err)

    # Store coordinators
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinators": coordinators,
        # Keep these for backward compatibility
        "coordinator": coordinators[UPDATE_RING_MEDIUM],
        "position_coordinator": coordinators[UPDATE_RING_FAST],
    }

    _LOGGER.info(
        "Successfully set up AutoPi integration with %d coordinators: fast=%d min, medium=%d min",
        len(coordinators),
        entry.options.get(CONF_UPDATE_INTERVAL_FAST, DEFAULT_UPDATE_INTERVAL_FAST_MINUTES),
        entry.options.get(CONF_UPDATE_INTERVAL_MEDIUM, DEFAULT_UPDATE_INTERVAL_MEDIUM_MINUTES),
    )

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register update listener for options
    entry.async_on_unload(entry.add_update_listener(async_update_options))

    _LOGGER.info(
        "AutoPi integration setup completed successfully for entry %s", entry.entry_id
    )

    return True


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update options.

    Args:
        hass: Home Assistant instance
        entry: Configuration entry with updated options
    """
    _LOGGER.debug("Updating options for entry %s", entry.entry_id)

    # Get the coordinators
    data = hass.data[DOMAIN][entry.entry_id]
    coordinators = data["coordinators"]

    # Check if any intervals have changed
    intervals_changed = False
    for ring_type, conf_key, default_val in [
        (UPDATE_RING_FAST, CONF_UPDATE_INTERVAL_FAST, DEFAULT_UPDATE_INTERVAL_FAST_MINUTES),
        (UPDATE_RING_MEDIUM, CONF_UPDATE_INTERVAL_MEDIUM, DEFAULT_UPDATE_INTERVAL_MEDIUM_MINUTES),
        (UPDATE_RING_SLOW, CONF_UPDATE_INTERVAL_SLOW, DEFAULT_UPDATE_INTERVAL_SLOW_MINUTES),
    ]:
        if ring_type in coordinators:
            coordinator = coordinators[ring_type]
            new_interval = entry.options.get(conf_key, default_val)
            current_interval_minutes = (
                coordinator.update_interval.total_seconds() / 60
                if coordinator.update_interval
                else default_val
            )

            if new_interval != current_interval_minutes:
                intervals_changed = True
                _LOGGER.info(
                    "Update interval for %s ring changed from %d to %d minutes",
                    ring_type,
                    current_interval_minutes,
                    new_interval,
                )

    if intervals_changed:
        _LOGGER.warning(
            "Update interval change requires integration reload to take effect"
        )
        # Schedule a reload
        await hass.config_entries.async_reload(entry.entry_id)
    else:
        # Just trigger a refresh on all coordinators
        for coordinator in coordinators.values():
            await coordinator.async_request_refresh()


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry.

    Args:
        hass: Home Assistant instance
        entry: Configuration entry to unload

    Returns:
        bool: True if unload successful
    """
    _LOGGER.info("Unloading AutoPi integration for entry %s", entry.entry_id)

    # Unload platforms
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        # Remove coordinators
        hass.data[DOMAIN].pop(entry.entry_id)

        _LOGGER.info(
            "Successfully unloaded AutoPi integration for entry %s", entry.entry_id
        )

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry.

    Args:
        hass: Home Assistant instance
        entry: Configuration entry to reload
    """
    _LOGGER.debug("Reloading AutoPi integration for entry %s", entry.entry_id)
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
