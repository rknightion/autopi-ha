"""The AutoPi integration for Home Assistant."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import UpdateFailed

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

from .auto_zero import get_auto_zero_manager
from .const import (
    CONF_UPDATE_INTERVAL_FAST,
    DEFAULT_UPDATE_INTERVAL_FAST_MINUTES,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import (
    AutoPiDataUpdateCoordinator,
    AutoPiPositionCoordinator,
    AutoPiTripCoordinator,
)

_LOGGER = logging.getLogger(__name__)


# Suppress verbose logging from third-party libraries
def _setup_logging() -> None:
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

    # Create the base coordinator for vehicle data
    _LOGGER.info("Creating base vehicle data coordinator")
    coordinator = AutoPiDataUpdateCoordinator(hass, entry)
    coordinators["base"] = coordinator

    # Perform initial data fetch
    try:
        _LOGGER.debug("Performing initial data fetch for base vehicle data")
        await coordinator.async_config_entry_first_refresh()
        _LOGGER.info(
            "Initial data fetch successful, found %d vehicles",
            coordinator.get_vehicle_count(),
        )
    except UpdateFailed as err:
        _LOGGER.exception("Failed to fetch initial data")
        raise ConfigEntryNotReady(f"Unable to connect to AutoPi API: {err}") from err

    # Create position coordinator (independent of base coordinator)
    _LOGGER.info("Creating position data coordinator")
    position_coordinator = AutoPiPositionCoordinator(hass, entry, coordinator)
    coordinators["position"] = position_coordinator

    # Perform initial position data fetch in parallel
    try:
        _LOGGER.debug("Performing initial position data fetch")
        await position_coordinator.async_config_entry_first_refresh()
        _LOGGER.info("Initial position data fetch successful")
    except UpdateFailed:
        # Position fetch failures are not critical
        _LOGGER.warning("Failed to fetch initial position data")

    # Create trip coordinator
    _LOGGER.info("Creating trip data coordinator")
    trip_coordinator = AutoPiTripCoordinator(hass, entry, coordinator)
    coordinators["trip"] = trip_coordinator

    # Perform initial trip data fetch
    try:
        _LOGGER.debug("Performing initial trip data fetch")
        await trip_coordinator.async_config_entry_first_refresh()
        _LOGGER.info("Initial trip data fetch successful")
    except UpdateFailed:
        # Trip fetch failures are not critical
        _LOGGER.warning("Failed to fetch initial trip data")

    # Log coordinator status
    _LOGGER.info("Coordinator setup complete")
    for coord_name, coord in coordinators.items():
        if coord:
            _LOGGER.debug(
                "Coordinator %s: interval=%s, last_update_success=%s",
                coord_name,
                coord.update_interval,
                coord.last_update_success,
            )

    # Initialize auto-zero manager with storage
    _LOGGER.info("[AUTO-ZERO INIT] Initializing auto-zero manager")
    auto_zero_manager = get_auto_zero_manager()
    await auto_zero_manager.async_initialize(hass)
    _LOGGER.info(
        "[AUTO-ZERO INIT] Auto-zero manager initialized, auto_zero_enabled=%s",
        entry.options.get("auto_zero_enabled", False),
    )

    # Log current options for debugging
    _LOGGER.info(
        "AutoPi integration options: %s",
        entry.options,
    )

    # Store coordinators
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinators": coordinators,
        # Keep these for backward compatibility
        "coordinator": coordinator,
        "position_coordinator": position_coordinator,
        "trip_coordinator": trip_coordinator,
    }

    _LOGGER.info(
        "Successfully set up AutoPi integration with update interval: %d min",
        entry.options.get(
            CONF_UPDATE_INTERVAL_FAST, DEFAULT_UPDATE_INTERVAL_FAST_MINUTES
        ),
    )

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register update listener for options
    entry.async_on_unload(entry.add_update_listener(async_update_options))

    _LOGGER.info(
        "AutoPi integration setup completed successfully for entry %s", entry.entry_id
    )

    # Schedule first update for all coordinators after setup is complete
    # This ensures the update cycle continues after the initial refresh
    for coord_name, coord in coordinators.items():
        if coord and coord.update_interval:
            _LOGGER.debug(
                "Requesting refresh for %s coordinator to ensure update cycle continues",
                coord_name,
            )
            await coord.async_request_refresh()

    return True


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update options.

    Args:
        hass: Home Assistant instance
        entry: Configuration entry with updated options
    """
    _LOGGER.debug("Updating options for entry %s", entry.entry_id)

    # Get the data
    data = hass.data[DOMAIN][entry.entry_id]

    # Check if any intervals have changed
    intervals_changed = False

    # Check fast interval for all coordinators
    new_fast_interval = entry.options.get(
        CONF_UPDATE_INTERVAL_FAST, DEFAULT_UPDATE_INTERVAL_FAST_MINUTES
    )

    # Check all coordinators for interval changes
    for coord_name, coordinator in data.get("coordinators", {}).items():
        if coordinator:
            current_interval_minutes = (
                coordinator.update_interval.total_seconds() / 60
                if coordinator.update_interval
                else DEFAULT_UPDATE_INTERVAL_FAST_MINUTES
            )
            if new_fast_interval != current_interval_minutes:
                intervals_changed = True
                _LOGGER.info(
                    "Update interval for %s changed from %d to %d minutes",
                    coord_name,
                    current_interval_minutes,
                    new_fast_interval,
                )

    if intervals_changed:
        _LOGGER.warning(
            "Update interval change requires integration reload to take effect"
        )
        # Schedule a reload
        await hass.config_entries.async_reload(entry.entry_id)
    else:
        # Just trigger a refresh on all coordinators
        for coord in data.get("coordinators", {}).values():
            await coord.async_request_refresh()


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
