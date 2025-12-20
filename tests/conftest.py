"""Shared test fixtures for AutoPi integration tests.

This module provides centralized test fixtures using pytest-homeassistant-custom-component
to ensure consistency across all tests and reduce boilerplate.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest
from homeassistant.core import HomeAssistant

from custom_components.autopi.types import AutoPiVehicle, DataFieldValue

# Enable custom integrations for all tests
pytest_plugins = "pytest_homeassistant_custom_component"


def create_mock_aiohttp_response(status: int, json_data: dict | None = None, text: str = ""):
    """Create a mock aiohttp response for testing.

    Args:
        status: HTTP status code
        json_data: JSON data to return (if any)
        text: Text to return (if any)

    Returns:
        Mock response configured as async context manager
    """
    mock_response = AsyncMock()
    mock_response.status = status
    if json_data is not None:
        mock_response.json = AsyncMock(return_value=json_data)
    mock_response.text = AsyncMock(return_value=text)
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)
    return mock_response


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Automatically enable custom integrations for all tests."""
    return


@pytest.fixture
def load_fixture():
    """Load a fixture file.

    Returns a function that can be called with a filename to load JSON fixtures.
    """
    def _load_fixture(filename: str) -> str:
        """Load a fixture file from the fixtures directory."""
        path = Path(__file__).parent / "fixtures" / filename
        return path.read_text()

    return _load_fixture


@pytest.fixture
def mock_autopi_client():
    """Create a mock AutoPi API client.

    Provides a fully configured mock client with common methods stubbed.
    Tests can override specific methods as needed.
    """
    client = Mock()
    client.get_vehicles = AsyncMock(return_value={})
    client.get_data_fields = AsyncMock(return_value={})
    client.get_fleet_alerts = AsyncMock(return_value=(0, []))
    client.get_fleet_alerts_summary = AsyncMock(return_value=None)
    client.get_vehicle_alerts = AsyncMock(return_value={"count": 0, "results": []})
    client.get_charging_sessions = AsyncMock(return_value=[])
    client.get_diagnostics = AsyncMock(return_value={"count": 0, "results": []})
    client.get_obd_dtcs = AsyncMock(return_value=[])
    client.get_geofence_summary = AsyncMock(return_value={"counts": {"locations": 0, "geofences": 0}, "results": []})
    client.get_fleet_vehicle_summary = AsyncMock(return_value=None)
    client.get_events_histogram = AsyncMock(return_value=[])
    client.get_simplified_events = AsyncMock(return_value=[])
    client.get_rfid_events = AsyncMock(return_value=[])
    client.get_recent_stats = AsyncMock(return_value=[])
    client.get_most_recent_positions = AsyncMock(return_value=[])
    client.get_device_events = AsyncMock(return_value=[])
    client.get_trips = AsyncMock(return_value=[])
    client.close = AsyncMock()
    return client


@pytest.fixture
def mock_vehicle():
    """Create a mock AutoPi vehicle.

    Returns a standard test vehicle with common attributes populated.
    Tests can override attributes as needed.
    """
    return AutoPiVehicle(
        id=123,
        name="Test Vehicle",
        license_plate="ABC123",
        vin="1234567890ABCDEF",
        year=2020,
        type="ICE",
        battery_voltage=12,
        devices=["device-123"],
        make_id=1,
        model_id=1,
        position=None,
        data_fields={},
    )


@pytest.fixture
def mock_vehicle_2():
    """Create a second mock vehicle for multi-vehicle tests."""
    return AutoPiVehicle(
        id=456,
        name="Second Vehicle",
        license_plate="XYZ789",
        vin="FEDCBA0987654321",
        year=2021,
        type="EV",
        battery_voltage=48,
        devices=["device-456"],
        make_id=2,
        model_id=2,
        position=None,
        data_fields={},
    )


@pytest.fixture
def mock_data_field():
    """Create a mock data field value."""
    return DataFieldValue(
        field_id="obd.rpm.value",
        last_value=2500.0,
        last_seen="2025-10-19T10:00:00Z",
    )


@pytest.fixture
def mock_config_entry_data():
    """Create mock config entry data.

    Returns the data dictionary structure used in config entries.
    """
    return {
        "api_key": "test_api_key_12345",
        "base_url": "https://api.autopi.io",
        "selected_vehicles": ["123", "456"],
        "scan_interval": 5,
    }


@pytest.fixture
def mock_config_entry_options():
    """Create mock config entry options.

    Returns the options dictionary structure used in config entries.
    """
    return {
        "update_interval_fast": 1,
        "update_interval_medium": 5,
        "update_interval_slow": 15,
        "discovery_enabled": True,
        "auto_zero_enabled": False,
    }


@pytest.fixture
def mock_api_vehicle_response():
    """Create a mock API response for vehicle profile endpoint.

    Returns the JSON structure returned by /vehicle/v2/profile.
    """
    return {
        "count": 2,
        "results": [
            {
                "id": 123,
                "callName": "Test Vehicle",
                "licensePlate": "ABC123",
                "vin": "1234567890ABCDEF",
                "year": 2020,
                "type": "ICE",
                "battery_nominal_voltage": 12,
                "devices": ["device-123"],
                "make": 1,
                "model": 1,
            },
            {
                "id": 456,
                "callName": "Second Vehicle",
                "licensePlate": "XYZ789",
                "vin": "FEDCBA0987654321",
                "year": 2021,
                "type": "EV",
                "battery_nominal_voltage": 48,
                "devices": ["device-456"],
                "make": 2,
                "model": 2,
            },
        ],
    }


@pytest.fixture
def mock_api_position_response():
    """Create a mock API response for position endpoint.

    Returns the JSON structure returned by bulk position endpoint.
    """
    return {
        "123": {
            "utc_position_timestamp": "2025-10-19T10:00:00Z",
            "track.pos.loc": [-1.085937, 51.264327],
            "track.pos.alt": 125.5,
            "track.pos.sog": 16.67,  # m/s
            "track.pos.cog": 45.0,
            "track.pos.nsat": 12,
        },
        "456": {
            "utc_position_timestamp": "2025-10-19T10:05:00Z",
            "track.pos.loc": [-0.118092, 51.509865],
            "track.pos.alt": 15.2,
            "track.pos.sog": 8.33,
            "track.pos.cog": 90.0,
            "track.pos.nsat": 10,
        },
    }


@pytest.fixture
def mock_api_trips_response():
    """Create a mock API response for trips endpoint."""
    return {
        "count": 1,
        "results": [
            {
                "id": "trip-123",
                "vehicle": 123,
                "start_time_utc": "2025-10-19T09:00:00Z",
                "end_time_utc": "2025-10-19T09:30:00Z",
                "duration": 1800.0,
                "distance": 15.5,
                "start_address": "123 Start St, City",
                "end_address": "456 End Ave, City",
                "start_position": [-1.085937, 51.264327],
                "end_position": [-1.090000, 51.270000],
            }
        ],
    }


@pytest.fixture
def mock_api_alerts_response():
    """Create a mock API response for fleet alerts endpoint."""
    return {
        "total": 2,
        "alerts": [
            {
                "id": "alert-1",
                "severity": "high",
                "message": "Battery voltage low",
                "vehicle_id": 123,
                "timestamp": "2025-10-19T10:00:00Z",
            },
            {
                "id": "alert-2",
                "severity": "medium",
                "message": "Service due soon",
                "vehicle_id": 456,
                "timestamp": "2025-10-19T09:30:00Z",
            },
        ],
    }


@pytest.fixture
async def mock_coordinator(hass: HomeAssistant, mock_autopi_client, mock_vehicle):
    """Create a mock coordinator with basic data.

    This fixture uses the real Home Assistant instance but mocks the client.
    Tests can further customize the coordinator data as needed.
    """
    from custom_components.autopi.coordinator import AutoPiDataUpdateCoordinator
    from unittest.mock import Mock

    # Create a mock config entry
    mock_entry = Mock()
    mock_entry.entry_id = "test_entry_123"
    mock_entry.data = {
        "api_key": "test_key",
        "base_url": "https://api.autopi.io",
        "selected_vehicles": ["123"],
    }
    mock_entry.options = {}

    # Create coordinator
    coordinator = AutoPiDataUpdateCoordinator(hass, mock_entry)
    coordinator._client = mock_autopi_client
    coordinator.data = {str(mock_vehicle.id): mock_vehicle}

    return coordinator
