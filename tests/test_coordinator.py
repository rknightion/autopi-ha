"""Tests for AutoPi data update coordinators."""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.autopi.coordinator import (
    AutoPiDataUpdateCoordinator,
    AutoPiPositionCoordinator,
)
from custom_components.autopi.exceptions import (
    AutoPiAuthenticationError,
    AutoPiConnectionError,
)
from custom_components.autopi.types import AutoPiVehicle, DataFieldValue


@pytest.fixture
def mock_hass():
    """Create a mock Home Assistant instance."""
    hass = Mock()
    hass.config_entries = Mock()
    hass.config_entries.async_reload = AsyncMock()
    hass.loop = Mock()
    hass.loop.time = Mock(return_value=0)
    return hass


@pytest.fixture
def mock_config_entry():
    """Create a mock config entry."""
    entry = Mock()
    entry.entry_id = "test_entry"
    entry.data = {
        "api_key": "test_key",
        "base_url": "https://api.autopi.io",
        "selected_vehicles": ["123", "456"],
    }
    entry.options = {}
    return entry


@pytest.fixture
def mock_client():
    """Create a mock AutoPi client."""
    client = Mock()
    client.get_vehicles = AsyncMock()
    client.get_data_fields = AsyncMock()
    client.close = AsyncMock()
    return client


@pytest.fixture
def mock_vehicle():
    """Create a mock vehicle."""
    return AutoPiVehicle(
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
        data_fields={},
    )


@pytest.fixture
def mock_base_coordinator(mock_hass, mock_config_entry, mock_client):
    """Create a mock base coordinator."""
    coordinator = Mock()
    coordinator.data = {}
    coordinator._client = mock_client
    coordinator._selected_vehicles = {"123", "456"}
    return coordinator


class TestAutoPiDataUpdateCoordinator:
    """Test the main data update coordinator."""

    @pytest.mark.asyncio
    async def test_coordinator_initialization(self, mock_hass, mock_config_entry):
        """Test coordinator initialization."""
        coordinator = AutoPiDataUpdateCoordinator(
            mock_hass, mock_config_entry
        )

        assert coordinator.name == f"autopi_{mock_config_entry.entry_id}_medium"
        assert coordinator.update_interval == timedelta(seconds=300)
        assert coordinator._client is None  # Client not created yet
        assert coordinator._selected_vehicles == {"123", "456"}

    @pytest.mark.asyncio
    async def test_fetch_data_success(self, mock_hass, mock_config_entry, mock_client, mock_vehicle):
        """Test successful data fetching."""
        with patch("custom_components.autopi.coordinator.AutoPiClient", return_value=mock_client):
            mock_client.get_vehicles.return_value = [mock_vehicle]

            coordinator = AutoPiDataUpdateCoordinator(
                mock_hass, mock_config_entry
            )

            data = await coordinator._async_update_data()

            assert "123" in data
            assert data["123"] == mock_vehicle
            mock_client.get_vehicles.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_data_filters_vehicles(self, mock_hass, mock_config_entry, mock_client):
        """Test that only selected vehicles are included."""
        with patch("custom_components.autopi.coordinator.AutoPiClient", return_value=mock_client):
            vehicle1 = Mock(id=123)
            vehicle2 = Mock(id=456)
            vehicle3 = Mock(id=789)  # Not selected

            mock_client.get_vehicles.return_value = [vehicle1, vehicle2, vehicle3]

            coordinator = AutoPiDataUpdateCoordinator(
                mock_hass, mock_config_entry
            )

            data = await coordinator._async_update_data()

            assert "123" in data
            assert "456" in data
            assert "789" not in data

    @pytest.mark.asyncio
    async def test_fetch_data_auth_error(self, mock_hass, mock_config_entry, mock_client):
        """Test authentication error handling."""
        with patch("custom_components.autopi.coordinator.AutoPiClient", return_value=mock_client):
            mock_client.get_vehicles.side_effect = AutoPiAuthenticationError("Invalid API key")

            coordinator = AutoPiDataUpdateCoordinator(
                mock_hass, mock_config_entry
            )

            with pytest.raises(ConfigEntryAuthFailed):
                await coordinator._async_update_data()

    @pytest.mark.asyncio
    async def test_fetch_data_connection_error(self, mock_hass, mock_config_entry, mock_client):
        """Test connection error handling."""
        with patch("custom_components.autopi.coordinator.AutoPiClient", return_value=mock_client):
            mock_client.get_vehicles.side_effect = AutoPiConnectionError("Connection failed")

            coordinator = AutoPiDataUpdateCoordinator(
                mock_hass, mock_config_entry
            )

            with pytest.raises(UpdateFailed) as exc_info:
                await coordinator._async_update_data()

            assert "Failed to connect" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_interval_from_options(self, mock_hass, mock_config_entry):
        """Test update interval from options."""
        mock_config_entry.options = {"update_interval_medium": 10}

        coordinator = AutoPiDataUpdateCoordinator(
            mock_hass, mock_config_entry
        )

        assert coordinator.update_interval == timedelta(seconds=600)  # 10 minutes


class TestAutoPiPositionCoordinator:
    """Test the position data update coordinator."""

    @pytest.mark.asyncio
    async def test_position_coordinator_initialization(self, mock_hass, mock_config_entry, mock_client, mock_base_coordinator):
        """Test position coordinator initialization."""
        coordinator = AutoPiPositionCoordinator(
            mock_hass, mock_config_entry, mock_base_coordinator
        )

        assert coordinator.name == f"autopi_{mock_config_entry.entry_id}_fast"
        assert coordinator.update_interval == timedelta(seconds=60)  # Default 1 minute

    @pytest.mark.asyncio
    async def test_fetch_position_data_success(self, mock_hass, mock_config_entry, mock_client, mock_vehicle, mock_base_coordinator):
        """Test successful position data fetching."""
        mock_base_coordinator.data = {"123": mock_vehicle}

        # Mock data fields response
        data_fields = {
            "track.pos.loc": DataFieldValue(
                field_prefix="track.pos",
                field_name="loc",
                frequency=1.0,
                value_type="dict",
                title="Location",
                last_seen=datetime.now(),
                last_value={"lat": 51.264327, "lon": -1.085937},
                description="GPS location",
                last_update=datetime.now(),
            ),
            "track.pos.alt": DataFieldValue(
                field_prefix="track.pos",
                field_name="alt",
                frequency=1.0,
                value_type="int",
                title="Altitude",
                last_seen=datetime.now(),
                last_value=150,
                description="GPS altitude",
                last_update=datetime.now(),
            ),
        }
        mock_client.get_data_fields.return_value = data_fields

        coordinator = AutoPiPositionCoordinator(
            mock_hass, mock_config_entry, mock_base_coordinator
        )

        data = await coordinator._async_update_data()

        assert "123" in data
        vehicle = data["123"]
        assert vehicle.data_fields == data_fields

        # Verify position was extracted from data fields
        assert vehicle.position is not None
        assert vehicle.position.latitude == 51.264327
        assert vehicle.position.longitude == -1.085937
        assert vehicle.position.altitude == 150

    @pytest.mark.asyncio
    async def test_fetch_position_data_partial_fields(self, mock_hass, mock_config_entry, mock_client, mock_vehicle, mock_base_coordinator):
        """Test handling partial position data fields."""
        mock_base_coordinator.data = {"123": mock_vehicle}

        # Only location field available
        data_fields = {
            "track.pos.loc": DataFieldValue(
                field_prefix="track.pos",
                field_name="loc",
                frequency=1.0,
                value_type="dict",
                title="Location",
                last_seen=datetime.now(),
                last_value={"lat": 51.264327, "lon": -1.085937},
                description="GPS location",
                last_update=datetime.now(),
            ),
        }
        mock_client.get_data_fields.return_value = data_fields

        coordinator = AutoPiPositionCoordinator(
            mock_hass, mock_config_entry, mock_base_coordinator
        )

        data = await coordinator._async_update_data()

        vehicle = data["123"]
        assert vehicle.position is not None
        assert vehicle.position.latitude == 51.264327
        assert vehicle.position.longitude == -1.085937
        assert vehicle.position.altitude is None  # Not available

    @pytest.mark.asyncio
    async def test_fetch_position_data_no_devices(self, mock_hass, mock_config_entry, mock_client, mock_base_coordinator):
        """Test handling vehicles with no devices."""
        vehicle_no_devices = AutoPiVehicle(
            id=123,
            name="Test Vehicle",
            license_plate="ABC123",
            vin="1234567890",
            year=2020,
            type="ICE",
            battery_voltage=12,
            devices=[],  # No devices
            make_id=1,
            model_id=1,
            position=None,
            data_fields={},
        )

        mock_base_coordinator.data = {"123": vehicle_no_devices}

        coordinator = AutoPiPositionCoordinator(
            mock_hass, mock_config_entry, mock_base_coordinator
        )

        data = await coordinator._async_update_data()

        # Vehicle should still be in data but without data fields
        assert "123" in data
        assert data["123"].data_fields == {}
        mock_client.get_data_fields.assert_not_called()

    @pytest.mark.asyncio
    async def test_fetch_position_data_api_error(self, mock_hass, mock_config_entry, mock_client, mock_vehicle, mock_base_coordinator):
        """Test handling API errors when fetching data fields."""
        mock_base_coordinator.data = {"123": mock_vehicle}
        mock_client.get_data_fields.side_effect = Exception("API error")

        coordinator = AutoPiPositionCoordinator(
            mock_hass, mock_config_entry, mock_base_coordinator
        )

        data = await coordinator._async_update_data()

        # Should still return vehicle but without data fields
        assert "123" in data
        assert data["123"].data_fields == {}

    @pytest.mark.asyncio
    async def test_position_update_interval_from_options(self, mock_hass, mock_config_entry, mock_client, mock_base_coordinator):
        """Test position update interval from options."""
        mock_config_entry.options = {"update_interval_fast": 5}

        coordinator = AutoPiPositionCoordinator(
            mock_hass, mock_config_entry, mock_base_coordinator
        )

        assert coordinator.update_interval == timedelta(seconds=300)  # 5 minutes

    @pytest.mark.asyncio
    async def test_position_data_timestamp_parsing(self, mock_hass, mock_config_entry, mock_client, mock_vehicle, mock_base_coordinator):
        """Test parsing of timestamp from position data."""
        mock_base_coordinator.data = {"123": mock_vehicle}

        data_fields = {
            "track.pos.loc": DataFieldValue(
                field_prefix="track.pos",
                field_name="loc",
                frequency=1.0,
                value_type="dict",
                title="Location",
                last_seen=datetime.now(),
                last_value={"lat": 51.264327, "lon": -1.085937},
                description="GPS location",
                last_update=datetime.now(),
            ),
            "track.pos.utc": DataFieldValue(
                field_prefix="track.pos",
                field_name="utc",
                frequency=1.0,
                value_type="str",
                title="UTC Time",
                last_seen=datetime.now(),
                last_value="2024-01-20T10:30:00.000000+00:00",
                description="GPS UTC time",
                last_update=datetime.now(),
            ),
        }
        mock_client.get_data_fields.return_value = data_fields

        coordinator = AutoPiPositionCoordinator(
            mock_hass, mock_config_entry, mock_base_coordinator
        )

        data = await coordinator._async_update_data()

        vehicle = data["123"]
        assert vehicle.position is not None
        assert vehicle.position.timestamp is not None
        assert vehicle.position.timestamp.year == 2024
        assert vehicle.position.timestamp.month == 1
        assert vehicle.position.timestamp.day == 20
