"""Tests for AutoPi position sensors."""

from datetime import UTC, datetime
from typing import Any
from unittest.mock import Mock

import pytest
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import EntityCategory, UnitOfLength, UnitOfSpeed

from custom_components.autopi.position_sensors import (
    GPSAltitudeSensor,
    GPSCourseSensor,
    GPSLatitudeSensor,
    GPSLongitudeSensor,
    GPSSatellitesSensor,
    GPSSpeedSensor,
    create_position_sensors,
)
from custom_components.autopi.types import AutoPiVehicle, DataFieldValue


@pytest.fixture
def mock_coordinator():
    """Create a mock coordinator."""
    coordinator = Mock()
    coordinator.data = {}
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
    value_type: str = "float",
) -> DataFieldValue:
    """Create a data field value for testing."""
    now = datetime.now(UTC)
    return DataFieldValue(
        field_prefix=field_prefix,
        field_name=field_name,
        frequency=1.0,
        value_type=value_type,
        title=f"{field_prefix}.{field_name}",
        last_seen=now,
        last_value=value,
        description="Test field",
        last_update=now,
    )


class TestGPSPositionSensors:
    """Test GPS position sensors."""

    def test_gps_altitude_sensor(self, mock_coordinator, mock_vehicle):
        """Test GPS altitude sensor."""
        field = create_data_field("track.pos", "alt", 150, "int")
        mock_vehicle.data_fields = {"track.pos.alt": field}
        mock_coordinator.data = {"123": mock_vehicle}

        sensor = GPSAltitudeSensor(mock_coordinator, "123")

        assert sensor.native_value == 150
        assert sensor._attr_name == "GPS Altitude"
        assert sensor._attr_device_class == SensorDeviceClass.DISTANCE
        assert sensor._attr_native_unit_of_measurement == UnitOfLength.METERS
        assert sensor._attr_state_class == SensorStateClass.MEASUREMENT

    def test_gps_speed_sensor(self, mock_coordinator, mock_vehicle):
        """Test GPS speed sensor."""
        field = create_data_field("track.pos", "sog", 15.5)
        mock_vehicle.data_fields = {"track.pos.sog": field}
        mock_coordinator.data = {"123": mock_vehicle}

        sensor = GPSSpeedSensor(mock_coordinator, "123")

        assert sensor.native_value == 15.5
        assert sensor._attr_name == "GPS Speed"
        assert sensor._attr_device_class == SensorDeviceClass.SPEED
        assert sensor._attr_native_unit_of_measurement == UnitOfSpeed.METERS_PER_SECOND

    def test_gps_course_sensor(self, mock_coordinator, mock_vehicle):
        """Test GPS course sensor."""
        field = create_data_field("track.pos", "cog", 270.5)
        mock_vehicle.data_fields = {"track.pos.cog": field}
        mock_coordinator.data = {"123": mock_vehicle}

        sensor = GPSCourseSensor(mock_coordinator, "123")

        assert sensor.native_value == 270.5
        assert sensor._attr_name == "GPS Course"
        assert sensor._attr_native_unit_of_measurement == "°"
        assert sensor._attr_state_class == SensorStateClass.MEASUREMENT

    def test_gps_satellites_sensor(self, mock_coordinator, mock_vehicle):
        """Test GPS satellites sensor with accuracy calculation."""
        field = create_data_field("track.pos", "nsat", 8, "int")
        mock_vehicle.data_fields = {"track.pos.nsat": field}
        mock_coordinator.data = {"123": mock_vehicle}

        sensor = GPSSatellitesSensor(mock_coordinator, "123")

        assert sensor.native_value == 8
        assert sensor._attr_name == "GPS Satellites"

        # Test accuracy calculation
        attrs = sensor.extra_state_attributes
        assert attrs["location_accuracy"] == 7.5  # 8 satellites = 7.5m accuracy

    def test_gps_satellites_accuracy_ranges(self, mock_coordinator, mock_vehicle):
        """Test GPS satellites accuracy calculation for different ranges."""
        test_cases = [
            (3, 100.0),   # < 4 satellites
            (4, 30.0),    # 4 satellites
            (5, 20.0),    # 5 satellites
            (6, 15.0),    # 6 satellites
            (7, 11.0),    # 7 satellites
            (9, 7.5),     # 8-9 satellites
            (10, 5.0),    # 10-11 satellites
            (12, 3.0),    # 12+ satellites
        ]

        mock_coordinator.data = {"123": mock_vehicle}
        sensor = GPSSatellitesSensor(mock_coordinator, "123")

        for sat_count, expected_accuracy in test_cases:
            field = create_data_field("track.pos", "nsat", sat_count, "int")
            mock_vehicle.data_fields = {"track.pos.nsat": field}

            assert sensor.native_value == sat_count
            attrs = sensor.extra_state_attributes
            assert attrs["location_accuracy"] == expected_accuracy

    def test_gps_latitude_sensor(self, mock_coordinator, mock_vehicle):
        """Test GPS latitude sensor."""
        field = create_data_field("track.pos", "loc", {"lat": 51.264327, "lon": -1.085937}, "dict")
        mock_vehicle.data_fields = {"track.pos.loc": field}
        mock_coordinator.data = {"123": mock_vehicle}

        sensor = GPSLatitudeSensor(mock_coordinator, "123")

        assert sensor.native_value == 51.264327
        assert sensor._attr_name == "GPS Latitude"
        assert sensor._attr_entity_category == EntityCategory.DIAGNOSTIC

    def test_gps_longitude_sensor(self, mock_coordinator, mock_vehicle):
        """Test GPS longitude sensor."""
        field = create_data_field("track.pos", "loc", {"lat": 51.264327, "lon": -1.085937}, "dict")
        mock_vehicle.data_fields = {"track.pos.loc": field}
        mock_coordinator.data = {"123": mock_vehicle}

        sensor = GPSLongitudeSensor(mock_coordinator, "123")

        assert sensor.native_value == -1.085937
        assert sensor._attr_name == "GPS Longitude"
        assert sensor._attr_entity_category == EntityCategory.DIAGNOSTIC

    def test_lat_lon_caching(self, mock_coordinator, mock_vehicle):
        """Test latitude/longitude sensors cache values properly."""
        field = create_data_field("track.pos", "loc", {"lat": 51.264327, "lon": -1.085937}, "dict")
        mock_vehicle.data_fields = {"track.pos.loc": field}
        mock_coordinator.data = {"123": mock_vehicle}

        lat_sensor = GPSLatitudeSensor(mock_coordinator, "123")
        lon_sensor = GPSLongitudeSensor(mock_coordinator, "123")

        # Get initial values
        assert lat_sensor.native_value == 51.264327
        assert lon_sensor.native_value == -1.085937

        # Remove field data
        mock_vehicle.data_fields = {}

        # Should still return cached values
        assert lat_sensor.native_value == 51.264327
        assert lon_sensor.native_value == -1.085937


class TestPositionSensorCreation:
    """Test position sensor creation."""

    def test_create_position_sensors(self, mock_coordinator):
        """Test creating position sensors from available fields."""
        available_fields = {
            "track.pos.alt",
            "track.pos.sog",
            "track.pos.cog",
            "track.pos.nsat",
            "track.pos.loc",
            "track.pos.pr",  # Should be ignored
        }

        sensors = create_position_sensors(mock_coordinator, "123", available_fields)

        # Should create 6 sensors (loc creates both lat and lon)
        assert len(sensors) == 6

        # Check sensor types
        sensor_types = {type(sensor).__name__ for sensor in sensors}
        expected_types = {
            "GPSAltitudeSensor",
            "GPSSpeedSensor",
            "GPSCourseSensor",
            "GPSSatellitesSensor",
            "GPSLatitudeSensor",
            "GPSLongitudeSensor",
        }
        assert sensor_types == expected_types

    def test_create_sensors_handles_errors(self, mock_coordinator, caplog):
        """Test sensor creation handles errors gracefully."""
        # Create a field that's not mapped to any sensor
        available_fields = {"track.pos.pr"}  # Position residual - not implemented
        sensors = create_position_sensors(mock_coordinator, "123", available_fields)

        # Should return empty list for unmapped fields
        assert len(sensors) == 0
