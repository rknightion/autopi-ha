"""Test the AutoPi integration init."""
from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from custom_components.autopi.const import DOMAIN


async def test_setup_entry(hass: HomeAssistant) -> None:
    """Test setting up the integration."""
    # This is a placeholder test - actual implementation would test
    # the integration setup process
    assert await async_setup_component(hass, DOMAIN, {DOMAIN: {}}) 