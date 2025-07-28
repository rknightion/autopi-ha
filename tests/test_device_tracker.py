"""Tests for AutoPi device tracker."""

from datetime import datetime
from typing import Any
from unittest.mock import Mock

import pytest
from homeassistant.components.device_tracker import SourceType

from custom_components.autopi.device_tracker import AutoPiDeviceTracker
from custom_components.autopi.types import (
    AutoPiVehicle,
    DataFieldValue,
    VehiclePosition,
)


@pytest.fixture
def mock_coordinator():
    """Create a mock coordinator."""
    coordinator = Mock()
    coordinator.data = {}
    coordinator.last_update_success = True
    coordinator.config_entry = Mock()
    coordinator.config_entry.entry_id = "test_entry"
    return coordinator


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


def create_data_field(
    field_prefix: str,
    field_name: str,
    value: Any,
) -> DataFieldValue:
    """Create a data field value for testing."""
    now = datetime.now()
    return DataFieldValue(
        field_prefix=field_prefix,
        field_name=field_name,
        frequency=1.0,
        value_type="dict" if isinstance(value, dict) else "int",
        title=f"{field_prefix}.{field_name}",
        last_seen=now,
        last_value=value,
        description="Test field",
        last_update=now,
    )


class TestAutoDeviceTracker:
    """Test the AutoPi device tracker."""

    def test_device_tracker_initialization(self, mock_coordinator):
        """Test device tracker initialization."""
        tracker = AutoPiDeviceTracker(mock_coordinator, "123")

        assert tracker._attr_icon == "mdi:car"
        assert tracker.source_type == SourceType.GPS

    def test_location_from_data_fields(self, mock_coordinator, mock_vehicle):
        """Test getting location from data fields."""
        # Add location data field
        loc_field = create_data_field("track.pos", "loc", {"lat": 51.264327, "lon": -1.085937})
        mock_vehicle.data_fields = {"track.pos.loc": loc_field}
        mock_coordinator.data = {"123": mock_vehicle}

        tracker = AutoPiDeviceTracker(mock_coordinator, "123")

        assert tracker.latitude == 51.264327
        assert tracker.longitude == -1.085937

    def test_location_fallback_to_position(self, mock_coordinator, mock_vehicle):
        """Test falling back to position when data fields not available."""
        # No data fields, but position available
        position = VehiclePosition(
            timestamp=datetime.now(),
            latitude=52.123456,
            longitude=-2.123456,
            altitude=100,
            speed=15.0,
            course=180,
            num_satellites=8,
        )
        mock_vehicle.position = position
        mock_coordinator.data = {"123": mock_vehicle}

        tracker = AutoPiDeviceTracker(mock_coordinator, "123")

        assert tracker.latitude == 52.123456
        assert tracker.longitude == -2.123456

    def test_location_accuracy_from_satellites(self, mock_coordinator, mock_vehicle):
        """Test calculating location accuracy from satellite count."""
        # Add satellite count data field
        nsat_field = create_data_field("track.pos", "nsat", 8)
        mock_vehicle.data_fields = {"track.pos.nsat": nsat_field}
        mock_coordinator.data = {"123": mock_vehicle}

        tracker = AutoPiDeviceTracker(mock_coordinator, "123")

        # 8 satellites should give 8m accuracy
        assert tracker.location_accuracy == 8

    def test_location_accuracy_ranges(self, mock_coordinator, mock_vehicle):
        """Test location accuracy for different satellite counts."""
        test_cases = [
            (3, 100),   # < 4 satellites
            (4, 30),    # 4 satellites
            (5, 20),    # 5 satellites
            (6, 15),    # 6 satellites
            (7, 11),    # 7 satellites
            (8, 8),     # 8-9 satellites (different from sensor which uses 7.5)
            (10, 5),    # 10-11 satellites
            (12, 3),    # 12+ satellites
        ]

        mock_coordinator.data = {"123": mock_vehicle}
        tracker = AutoPiDeviceTracker(mock_coordinator, "123")

        for sat_count, expected_accuracy in test_cases:
            nsat_field = create_data_field("track.pos", "nsat", sat_count)
            mock_vehicle.data_fields = {"track.pos.nsat": nsat_field}

            assert tracker.location_accuracy == expected_accuracy

    def test_location_accuracy_fallback(self, mock_coordinator, mock_vehicle):
        """Test location accuracy fallback to position data."""
        # No data fields, but position with accuracy
        position = VehiclePosition(
            timestamp=datetime.now(),
            latitude=52.123456,
            longitude=-2.123456,
            altitude=100,
            speed=15.0,
            course=180,
            num_satellites=10,  # Should give 5m accuracy
        )
        mock_vehicle.position = position
        mock_coordinator.data = {"123": mock_vehicle}

        tracker = AutoPiDeviceTracker(mock_coordinator, "123")

        assert tracker.location_accuracy == 5

    def test_no_location_data(self, mock_coordinator, mock_vehicle):
        """Test when no location data is available."""
        # No data fields or position
        mock_coordinator.data = {"123": mock_vehicle}

        tracker = AutoPiDeviceTracker(mock_coordinator, "123")

        assert tracker.latitude is None
        assert tracker.longitude is None
        assert tracker.location_accuracy == 0

    def test_extra_state_attributes(self, mock_coordinator, mock_vehicle):
        """Test extra state attributes only include static data."""
        mock_coordinator.data = {"123": mock_vehicle}

        tracker = AutoPiDeviceTracker(mock_coordinator, "123")

        # Get parent class attributes
        attrs = tracker.extra_state_attributes

        # Should include vehicle attributes but not position data
        assert "vehicle_id" in attrs
        assert "vin" in attrs
        assert "license_plate" in attrs
        # Should not include frequently changing data
        assert "latitude" not in attrs
        assert "longitude" not in attrs
        assert "altitude" not in attrs


class TestDeviceTrackerSetup:
    """Test device tracker setup."""

    @pytest.mark.asyncio
    async def test_async_setup_entry(self, mock_coordinator):
        """Test setting up device tracker entities."""
        from custom_components.autopi.device_tracker import async_setup_entry

        # Create mock hass and config entry
        hass = Mock()
        config_entry = Mock()
        config_entry.entry_id = "test_entry"
        async_add_entities = Mock()

        # Add some vehicles to coordinator
        vehicle1 = Mock(spec=AutoPiVehicle)
        vehicle1.id = 123
        vehicle2 = Mock(spec=AutoPiVehicle)
        vehicle2.id = 456

        mock_coordinator.data = {
            "123": vehicle1,
            "456": vehicle2,
        }

        hass.data = {
            "autopi": {
                "test_entry": {
                    "position_coordinator": mock_coordinator,
                }
            }
        }

        # Call setup
        await async_setup_entry(hass, config_entry, async_add_entities)

        # Should create 2 device trackers
        async_add_entities.assert_called_once()
        entities = async_add_entities.call_args[0][0]
        assert len(entities) == 2
        assert all(isinstance(e, AutoPiDeviceTracker) for e in entities)
