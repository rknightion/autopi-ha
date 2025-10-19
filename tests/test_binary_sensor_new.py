"""Tests for AutoPi binary sensor platform."""

from __future__ import annotations

from unittest.mock import Mock

import pytest
from homeassistant.core import HomeAssistant

from custom_components.autopi.binary_sensor import async_setup_entry
from custom_components.autopi.const import DOMAIN


class TestBinarySensorSetup:
    """Test the binary sensor platform setup."""

    async def test_async_setup_entry(self, hass: HomeAssistant):
        """Test that async_setup_entry completes without error."""
        # Create mock config entry
        mock_entry = Mock()
        mock_entry.entry_id = "test_entry"

        # Mock entity callback
        added_entities = []

        def mock_add_entities(entities):
            added_entities.extend(entities)

        # Call async_setup_entry
        await async_setup_entry(hass, mock_entry, mock_add_entities)

        # Currently no binary sensors are implemented, so no entities should be added
        assert len(added_entities) == 0

    async def test_async_setup_entry_logs_debug_message(self, hass: HomeAssistant, caplog):
        """Test that async_setup_entry logs appropriate debug message."""
        import logging

        caplog.set_level(logging.DEBUG)

        mock_entry = Mock()
        mock_entry.entry_id = "test_entry"

        def mock_add_entities(entities):
            pass

        await async_setup_entry(hass, mock_entry, mock_add_entities)

        # Check that debug message was logged
        assert any(
            "Binary sensor platform loaded" in record.message
            for record in caplog.records
        )
