"""Constants for the AutoPi integration."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Final

from homeassistant.const import Platform

_LOGGER = logging.getLogger(__name__)

DOMAIN: Final = "autopi"

CONF_API_KEY: Final = "api_key"
CONF_BASE_URL: Final = "base_url"
CONF_ORGANIZATION_ID: Final = "organization_id"
CONF_SCAN_INTERVAL: Final = "scan_interval"
CONF_SELECTED_VEHICLES: Final = "selected_vehicles"

# Update interval configuration keys
CONF_UPDATE_INTERVAL_FAST: Final = "update_interval_fast"
CONF_UPDATE_INTERVAL_MEDIUM: Final = "update_interval_medium"
CONF_UPDATE_INTERVAL_SLOW: Final = "update_interval_slow"

# Feature configuration
CONF_AUTO_ZERO_ENABLED: Final = "auto_zero_enabled"

DEFAULT_NAME: Final = "AutoPi"
DEFAULT_BASE_URL: Final = "https://api.autopi.io"
DEFAULT_SCAN_INTERVAL: Final = 300  # 5 minutes
DEFAULT_SCAN_INTERVAL_MINUTES: Final = 5

# Default update intervals (in minutes)
DEFAULT_UPDATE_INTERVAL_FAST_MINUTES: Final = 1
DEFAULT_UPDATE_INTERVAL_MEDIUM_MINUTES: Final = 5
DEFAULT_UPDATE_INTERVAL_SLOW_MINUTES: Final = 15

MIN_SCAN_INTERVAL_MINUTES: Final = 1
MAX_SCAN_INTERVAL_MINUTES: Final = 60

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.DEVICE_TRACKER, Platform.EVENT]

# Future platforms to be implemented:
# Platform.BINARY_SENSOR - for vehicle status indicators

ATTR_VEHICLE_NAME: Final = "vehicle_name"
ATTR_LICENSE_PLATE: Final = "license_plate"
ATTR_VIN: Final = "vin"
ATTR_VEHICLE_TYPE: Final = "vehicle_type"
ATTR_VEHICLE_YEAR: Final = "vehicle_year"
ATTR_VEHICLE_MAKE: Final = "vehicle_make"
ATTR_VEHICLE_MODEL: Final = "vehicle_model"
ATTR_BATTERY_VOLTAGE: Final = "battery_nominal_voltage"
ATTR_ALTITUDE: Final = "altitude"
ATTR_SPEED: Final = "speed"
ATTR_COURSE: Final = "course"
ATTR_NUM_SATELLITES: Final = "num_satellites"
ATTR_TIMESTAMP: Final = "timestamp"

USER_AGENT: Final = f"HomeAssistant-AutoPi/{_LOGGER.name}"

VEHICLE_PROFILE_ENDPOINT: Final = "/vehicle/v2/profile"
DATA_FIELDS_ENDPOINT: Final = "/logbook/storage/data_fields/"
TRIPS_ENDPOINT: Final = "/logbook/v2/trips/"
ALERTS_ENDPOINT: Final = "/logbook/fleet_summary/alerts/"
EVENTS_ENDPOINT: Final = "/logbook/events/"

MANUFACTURER: Final = "AutoPi"

UPDATE_INTERVAL = timedelta(seconds=DEFAULT_SCAN_INTERVAL)

# Update ring types
UPDATE_RING_FAST: Final = "fast"
UPDATE_RING_MEDIUM: Final = "medium"
UPDATE_RING_SLOW: Final = "slow"

# Data field timeout - how long to show stale data before marking unavailable
DATA_FIELD_TIMEOUT_MINUTES: Final = 30
