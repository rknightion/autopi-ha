"""The AutoPi integration for Home Assistant."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import (
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL_MINUTES,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import AutoPiDataUpdateCoordinator

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

    # Create the data update coordinator
    coordinator = AutoPiDataUpdateCoordinator(hass, entry)

    # Perform initial data fetch
    try:
        _LOGGER.debug("Performing initial data fetch")
        await coordinator.async_config_entry_first_refresh()
        _LOGGER.info(
            "Initial data fetch successful, found %d vehicles",
            coordinator.get_vehicle_count(),
        )
    except Exception as err:
        _LOGGER.error("Failed to fetch initial data: %s", err)
        raise ConfigEntryNotReady(f"Unable to connect to AutoPi API: {err}") from err

    # Store coordinator
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

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

    # Get the coordinator
    coordinator: AutoPiDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Update scan interval if changed
    new_interval = entry.options.get(
        CONF_SCAN_INTERVAL,
        entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_MINUTES),
    )

    current_interval_minutes = (
        coordinator.update_interval.total_seconds() / 60
        if coordinator.update_interval
        else DEFAULT_SCAN_INTERVAL_MINUTES
    )

    if new_interval != current_interval_minutes:
        _LOGGER.info(
            "Updating scan interval from %d to %d minutes",
            current_interval_minutes,
            new_interval,
        )
        # Note: update_interval is read-only in DataUpdateCoordinator
        # We need to recreate the coordinator or use another approach
        _LOGGER.warning(
            "Update interval change requires integration reload to take effect"
        )

    # Trigger a refresh with new settings
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
        # Remove coordinator
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
