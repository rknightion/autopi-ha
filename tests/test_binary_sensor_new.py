"""Tests for AutoPi binary sensor platform."""

from __future__ import annotations

from unittest.mock import Mock

import pytest
from homeassistant.core import HomeAssistant

from custom_components.autopi.binary_sensor import async_setup_entry
from custom_components.autopi.const import DOMAIN
from datetime import UTC, datetime

from custom_components.autopi.types import AutoPiVehicle, DataFieldValue


class TestBinarySensorSetup:
    """Test the binary sensor platform setup."""

    async def test_async_setup_entry(self, hass: HomeAssistant):
        """Test that async_setup_entry completes without error."""
        mock_entry = Mock()
        mock_entry.entry_id = "test_entry"

        vehicle = AutoPiVehicle(
            id=123,
            name="Test Vehicle",
            license_plate="ABC123",
            vin="1234567890",
            year=2020,
            type="ICE",
            battery_voltage=12,
            devices=["device1"],
            make_id=1,
            model_id=1,
            position=None,
            data_fields={
                "obd.bat.state": DataFieldValue(
                    field_prefix="obd.bat",
                    field_name="state",
                    frequency=1.0,
                    value_type="string",
                    title="Battery Charging State",
                    last_seen=datetime.now(UTC),
                    last_value="charging",
                    description="",
                    last_update=datetime.now(UTC),
                ),
                "std.ignition.value": DataFieldValue(
                    field_prefix="std.ignition",
                    field_name="value",
                    frequency=1.0,
                    value_type="int",
                    title="Ignition",
                    last_seen=datetime.now(UTC),
                    last_value=1,
                    description="",
                    last_update=datetime.now(UTC),
                ),
            },
        )

        base_coordinator = Mock()
        base_coordinator.data = {"123": vehicle}
        base_coordinator.config_entry = mock_entry
        base_coordinator.is_endpoint_supported = Mock(return_value=True)

        position_coordinator = Mock()
        position_coordinator.data = {"123": vehicle}
        position_coordinator.config_entry = mock_entry
        position_coordinator.is_endpoint_supported = Mock(return_value=True)

        hass.data[DOMAIN] = {
            mock_entry.entry_id: {
                "coordinator": base_coordinator,
                "position_coordinator": position_coordinator,
            }
        }

        added_entities = []

        def mock_add_entities(entities):
            added_entities.extend(entities)

        await async_setup_entry(hass, mock_entry, mock_add_entities)

        assert len(added_entities) == 5

    async def test_async_setup_entry_logs_debug_message(self, hass: HomeAssistant, caplog):
        """Test that async_setup_entry logs appropriate debug message."""
        import logging

        caplog.set_level(logging.DEBUG)

        mock_entry = Mock()
        mock_entry.entry_id = "test_entry"

        def mock_add_entities(entities):
            pass

        base_coordinator = Mock()
        base_coordinator.data = {}
        base_coordinator.config_entry = mock_entry
        base_coordinator.is_endpoint_supported = Mock(return_value=True)

        position_coordinator = Mock()
        position_coordinator.data = {}
        position_coordinator.config_entry = mock_entry
        position_coordinator.is_endpoint_supported = Mock(return_value=True)

        hass.data[DOMAIN] = {
            mock_entry.entry_id: {
                "coordinator": base_coordinator,
                "position_coordinator": position_coordinator,
            }
        }

        await async_setup_entry(hass, mock_entry, mock_add_entities)

        assert any(
            "Adding" in record.message and "binary sensor" in record.message
            for record in caplog.records
        )
