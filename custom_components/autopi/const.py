"""Constants for the AutoPi integration."""
from __future__ import annotations

from typing import Final

DOMAIN: Final = "autopi"

# Configuration keys
CONF_API_KEY: Final = "api_key"
CONF_UPDATE_INTERVAL: Final = "update_interval"
CONF_DEVICES: Final = "devices"

# Default values
DEFAULT_UPDATE_INTERVAL: Final = 300  # 5 minutes
DEFAULT_TIMEOUT: Final = 30  # 30 seconds

# API endpoints
API_BASE_URL: Final = "https://api.autopi.io"
API_VERSION: Final = "v1"

# Device types
DEVICE_TYPE_AUTOPI: Final = "autopi"

# Entity categories
ENTITY_CATEGORY_DIAGNOSTIC: Final = "diagnostic" 