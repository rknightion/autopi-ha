"""Tests for AutoPi data field sensors."""

from datetime import datetime, timedelta
from typing import Any
from unittest.mock import Mock, patch

import pytest
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfElectricPotential,
    UnitOfLength,
    UnitOfSpeed,
    UnitOfTemperature,
)

from custom_components.autopi.const import DATA_FIELD_TIMEOUT_MINUTES
from custom_components.autopi.data_field_sensors import (
    AmbientTemperatureSensor,
    AutoPiDataFieldSensor,
    BatteryChargeLevelSensor,
    BatteryVoltageSensor,
    GSMSignalSensor,
    OBDSpeedSensor,
    TotalOdometerSensor,
    create_data_field_sensors,
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
    frequency: float = 1.0,
    last_update: datetime | None = None,
) -> DataFieldValue:
    """Create a data field value for testing."""
    if last_update is None:
        last_update = datetime.now()

    return DataFieldValue(
        field_prefix=field_prefix,
        field_name=field_name,
        frequency=frequency,
        value_type=value_type,
        title=f"{field_prefix}.{field_name}",
        last_seen=last_update,
        last_value=value,
        description="Test field",
        last_update=last_update,
    )


class TestAutoPiDataFieldSensor:
    """Test the base data field sensor class."""

    def test_sensor_initialization(self, mock_coordinator):
        """Test sensor initialization."""
        sensor = AutoPiDataFieldSensor(
            mock_coordinator,
            "123",
            "test.field",
            "Test Sensor",
            icon="mdi:test",
            device_class=SensorDeviceClass.TEMPERATURE,
            unit_of_measurement="°C",
            state_class=SensorStateClass.MEASUREMENT,
            entity_category=EntityCategory.DIAGNOSTIC,
        )

        assert sensor._field_id == "test.field"
        assert sensor._attr_name == "Test Sensor"
        assert sensor._attr_icon == "mdi:test"
        assert sensor._attr_device_class == SensorDeviceClass.TEMPERATURE
        assert sensor._attr_native_unit_of_measurement == "°C"
        assert sensor._attr_state_class == SensorStateClass.MEASUREMENT
        assert sensor._attr_entity_category == EntityCategory.DIAGNOSTIC

    def test_native_value_with_current_data(self, mock_coordinator, mock_vehicle):
        """Test native_value returns current data when available."""
        field = create_data_field("test", "field", 42.0)
        mock_vehicle.data_fields = {"test.field": field}
        mock_coordinator.data = {"123": mock_vehicle}

        sensor = AutoPiDataFieldSensor(
            mock_coordinator, "123", "test.field", "Test"
        )

        assert sensor.native_value == 42.0

    def test_native_value_with_stale_data(self, mock_coordinator, mock_vehicle):
        """Test native_value returns cached data when within timeout."""
        old_time = datetime.now() - timedelta(minutes=DATA_FIELD_TIMEOUT_MINUTES - 1)
        field = create_data_field("test", "field", 42.0, last_update=old_time)
        mock_vehicle.data_fields = {"test.field": field}
        mock_coordinator.data = {"123": mock_vehicle}

        sensor = AutoPiDataFieldSensor(
            mock_coordinator, "123", "test.field", "Test"
        )

        # Get initial value
        assert sensor.native_value == 42.0

        # Remove field to simulate missing data
        mock_vehicle.data_fields = {}

        # Should still return cached value
        assert sensor.native_value == 42.0

    def test_native_value_with_expired_data(self, mock_coordinator, mock_vehicle):
        """Test native_value returns None when data is expired."""
        old_time = datetime.now() - timedelta(minutes=DATA_FIELD_TIMEOUT_MINUTES + 1)
        field = create_data_field("test", "field", 42.0, last_update=old_time)
        mock_vehicle.data_fields = {"test.field": field}
        mock_coordinator.data = {"123": mock_vehicle}

        sensor = AutoPiDataFieldSensor(
            mock_coordinator, "123", "test.field", "Test"
        )

        # Get initial value
        assert sensor.native_value == 42.0

        # Remove field and set last update to expired
        mock_vehicle.data_fields = {}
        sensor._last_update_time = old_time

        # Should return None
        assert sensor.native_value is None

    def test_availability(self, mock_coordinator, mock_vehicle):
        """Test sensor availability."""
        mock_coordinator.data = {"123": mock_vehicle}
        mock_coordinator.last_update_success = True

        sensor = AutoPiDataFieldSensor(
            mock_coordinator, "123", "test.field", "Test"
        )

        # Should be unavailable without data
        assert sensor.available is False

        # Add data field
        field = create_data_field("test", "field", 42.0)
        mock_vehicle.data_fields = {"test.field": field}

        # Should be available with data
        assert sensor.available is True

    def test_extra_state_attributes(self, mock_coordinator, mock_vehicle):
        """Test extra state attributes."""
        field = create_data_field("test", "field", 42.0, frequency=10.5)
        mock_vehicle.data_fields = {"test.field": field}
        mock_coordinator.data = {"123": mock_vehicle}

        sensor = AutoPiDataFieldSensor(
            mock_coordinator, "123", "test.field", "Test"
        )

        attrs = sensor.extra_state_attributes

        assert attrs["frequency"] == 10.5
        assert attrs["field_id"] == "test.field"
        assert attrs["data_type"] == "float"
        assert attrs["description"] == "Test field"
        assert "last_seen" in attrs
        assert "vehicle_id" in attrs


class TestSpecificSensors:
    """Test specific sensor implementations."""

    def test_battery_charge_level_sensor(self, mock_coordinator, mock_vehicle):
        """Test battery charge level sensor."""
        field = create_data_field("obd.bat", "level", 85, "int")
        mock_vehicle.data_fields = {"obd.bat.level": field}
        mock_coordinator.data = {"123": mock_vehicle}

        sensor = BatteryChargeLevelSensor(mock_coordinator, "123")

        assert sensor.native_value == 85
        assert sensor._attr_name == "Battery Charge Level (OBD)"
        assert sensor._attr_device_class == SensorDeviceClass.BATTERY
        assert sensor._attr_native_unit_of_measurement == PERCENTAGE

    def test_battery_voltage_sensor(self, mock_coordinator, mock_vehicle):
        """Test battery voltage sensor."""
        field = create_data_field("obd.bat", "voltage", 12.7)
        mock_vehicle.data_fields = {"obd.bat.voltage": field}
        mock_coordinator.data = {"123": mock_vehicle}

        sensor = BatteryVoltageSensor(mock_coordinator, "123")

        assert sensor.native_value == 12.7
        assert sensor._attr_name == "Battery Voltage (OBD)"
        assert sensor._attr_device_class == SensorDeviceClass.VOLTAGE
        assert sensor._attr_native_unit_of_measurement == UnitOfElectricPotential.VOLT

    def test_gsm_signal_sensor(self, mock_coordinator, mock_vehicle):
        """Test GSM signal sensor percentage conversion."""
        field = create_data_field("std.gsm_signal", "value", 15, "int")
        mock_vehicle.data_fields = {"std.gsm_signal.value": field}
        mock_coordinator.data = {"123": mock_vehicle}

        sensor = GSMSignalSensor(mock_coordinator, "123")

        # 15/31 * 100 = 48.4, rounded to 48
        assert sensor.native_value == 48
        assert sensor.native_unit_of_measurement == PERCENTAGE
        assert sensor._attr_entity_category == EntityCategory.DIAGNOSTIC

    def test_obd_speed_sensor(self, mock_coordinator, mock_vehicle):
        """Test OBD speed sensor."""
        field = create_data_field("obd.speed", "value", 60, "int")
        mock_vehicle.data_fields = {"obd.speed.value": field}
        mock_coordinator.data = {"123": mock_vehicle}

        sensor = OBDSpeedSensor(mock_coordinator, "123")

        assert sensor.native_value == 60
        assert sensor._attr_name == "Vehicle Speed (OBD)"
        assert sensor._attr_device_class == SensorDeviceClass.SPEED
        assert sensor._attr_native_unit_of_measurement == UnitOfSpeed.KILOMETERS_PER_HOUR

    def test_odometer_sensor_conversion(self, mock_coordinator, mock_vehicle):
        """Test odometer sensor converts meters to kilometers."""
        field = create_data_field("std.total_odometer", "value", 35767143, "int")
        mock_vehicle.data_fields = {"std.total_odometer.value": field}
        mock_coordinator.data = {"123": mock_vehicle}

        sensor = TotalOdometerSensor(mock_coordinator, "123")

        # 35767143 m = 35767.1 km
        assert sensor.native_value == 35767.1
        assert sensor.native_unit_of_measurement == UnitOfLength.KILOMETERS

    def test_temperature_sensor(self, mock_coordinator, mock_vehicle):
        """Test temperature sensor."""
        field = create_data_field("obd.ambient_air_temp", "value", 22, "int")
        mock_vehicle.data_fields = {"obd.ambient_air_temp.value": field}
        mock_coordinator.data = {"123": mock_vehicle}

        sensor = AmbientTemperatureSensor(mock_coordinator, "123")

        assert sensor.native_value == 22
        assert sensor._attr_name == "Ambient Temperature (OBD)"
        assert sensor._attr_device_class == SensorDeviceClass.TEMPERATURE
        assert sensor._attr_native_unit_of_measurement == UnitOfTemperature.CELSIUS


class TestSensorCreation:
    """Test sensor creation functions."""

    def test_create_data_field_sensors(self, mock_coordinator):
        """Test creating sensors from available fields."""
        available_fields = {
            "obd.bat.level",
            "obd.bat.voltage",
            "obd.speed.value",
            "std.total_odometer.value",
            "unknown.field.value",  # Should be ignored
        }

        sensors = create_data_field_sensors(mock_coordinator, "123", available_fields)

        # Should create 4 sensors (unknown field ignored)
        assert len(sensors) == 4

        # Check sensor types
        sensor_types = {type(sensor).__name__ for sensor in sensors}
        assert "BatteryChargeLevelSensor" in sensor_types
        assert "BatteryVoltageSensor" in sensor_types
        assert "OBDSpeedSensor" in sensor_types
        assert "TotalOdometerSensor" in sensor_types

    def test_create_sensors_with_error(self, mock_coordinator, caplog):
        """Test sensor creation handles errors gracefully."""
        # Mock FIELD_ID_TO_SENSOR_CLASS to include a sensor that raises an error
        mock_sensor_class = Mock(side_effect=Exception("Test error"))

        with patch.dict("custom_components.autopi.data_field_sensors.FIELD_ID_TO_SENSOR_CLASS",
                       {"test.field": mock_sensor_class}, clear=False):
            available_fields = {"test.field", "obd.bat.level"}
            sensors = create_data_field_sensors(mock_coordinator, "123", available_fields)

            # Should still create valid sensors and log error for failed one
            assert len(sensors) == 1  # Only battery sensor created
            assert "Failed to create sensor" in caplog.text
