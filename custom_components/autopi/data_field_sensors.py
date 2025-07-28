"""Data field sensors for AutoPi integration."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfLength,
    UnitOfSpeed,
    UnitOfTemperature,
    UnitOfTime,
    UnitOfVolume,
)

from .const import DATA_FIELD_TIMEOUT_MINUTES
from .coordinator import AutoPiDataUpdateCoordinator
from .entities.base import AutoPiVehicleEntity
from .types import DataFieldValue

_LOGGER = logging.getLogger(__name__)


class AutoPiDataFieldSensor(AutoPiVehicleEntity, SensorEntity):
    """Base class for AutoPi data field sensors."""

    def __init__(
        self,
        coordinator: AutoPiDataUpdateCoordinator,
        vehicle_id: str,
        field_id: str,
        name: str,
        icon: str | None = None,
        device_class: SensorDeviceClass | None = None,
        unit_of_measurement: str | None = None,
        state_class: SensorStateClass | None = None,
        entity_category: EntityCategory | None = None,
    ) -> None:
        """Initialize the data field sensor."""
        super().__init__(
            coordinator, vehicle_id, f"data_field_{field_id.replace('.', '_')}"
        )
        self._field_id = field_id
        self._attr_name = name
        self._attr_icon = icon
        self._attr_device_class = device_class
        self._attr_native_unit_of_measurement = unit_of_measurement
        self._attr_state_class = state_class
        self._attr_entity_category = entity_category
        self._last_known_value: Any = None
        self._last_update_time: datetime | None = None

    @property
    def native_value(self) -> Any:
        """Return the sensor value."""
        field_data = self._get_field_data()

        if field_data is not None:
            # Update our last known value and time
            self._last_known_value = field_data.last_value
            self._last_update_time = field_data.last_update
            return field_data.last_value

        # If we have a last known value and it's within timeout, return it
        if self._last_known_value is not None and self._last_update_time is not None:
            if datetime.now() - self._last_update_time < timedelta(
                minutes=DATA_FIELD_TIMEOUT_MINUTES
            ):
                return self._last_known_value

        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        # Check base availability first
        if not super().available:
            return False

        # Check if we have current data
        field_data = self._get_field_data()
        if field_data is not None:
            return True

        # Check if we have stale data within timeout
        if self._last_known_value is not None and self._last_update_time is not None:
            if datetime.now() - self._last_update_time < timedelta(
                minutes=DATA_FIELD_TIMEOUT_MINUTES
            ):
                return True

        return False

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        attrs = super().extra_state_attributes

        field_data = self._get_field_data()
        if field_data is not None:
            attrs.update(
                {
                    "frequency": round(field_data.frequency, 2),
                    "last_seen": field_data.last_seen.isoformat(),
                    "field_id": field_data.field_id,
                    "data_type": field_data.value_type,
                }
            )

            if field_data.description:
                attrs["description"] = field_data.description

        # Add stale data indicator if using cached value
        if self._last_update_time is not None:
            time_since_update = datetime.now() - self._last_update_time
            if time_since_update > timedelta(seconds=0):
                attrs["data_age_seconds"] = int(time_since_update.total_seconds())

        return attrs

    def _get_field_data(self) -> DataFieldValue | None:
        """Get the field data from the coordinator."""
        if (
            not self.vehicle
            or not hasattr(self.vehicle, "data_fields")
            or self.vehicle.data_fields is None
        ):
            return None

        return self.vehicle.data_fields.get(self._field_id)


# Battery and Power Sensors


class BatteryChargeLevelSensor(AutoPiDataFieldSensor):
    """Battery charge level sensor."""

    def __init__(
        self, coordinator: AutoPiDataUpdateCoordinator, vehicle_id: str
    ) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator,
            vehicle_id,
            "obd.bat.level",
            "Battery Charge Level (OBD)",
            icon="mdi:battery",
            device_class=SensorDeviceClass.BATTERY,
            unit_of_measurement=PERCENTAGE,
            state_class=SensorStateClass.MEASUREMENT,
        )


class BatteryVoltageSensor(AutoPiDataFieldSensor):
    """Battery voltage sensor."""

    def __init__(
        self, coordinator: AutoPiDataUpdateCoordinator, vehicle_id: str
    ) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator,
            vehicle_id,
            "obd.bat.voltage",
            "Battery Voltage (OBD)",
            icon="mdi:lightning-bolt",
            device_class=SensorDeviceClass.VOLTAGE,
            unit_of_measurement=UnitOfElectricPotential.VOLT,
            state_class=SensorStateClass.MEASUREMENT,
        )


class BatteryCurrentSensor(AutoPiDataFieldSensor):
    """Battery current sensor."""

    def __init__(
        self, coordinator: AutoPiDataUpdateCoordinator, vehicle_id: str
    ) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator,
            vehicle_id,
            "std.battery_current.value",
            "Battery Current",
            icon="mdi:current-dc",
            device_class=SensorDeviceClass.CURRENT,
            unit_of_measurement=UnitOfElectricCurrent.AMPERE,
            state_class=SensorStateClass.MEASUREMENT,
        )


class TrackerBatteryLevelSensor(AutoPiDataFieldSensor):
    """Tracker battery level sensor."""

    def __init__(
        self, coordinator: AutoPiDataUpdateCoordinator, vehicle_id: str
    ) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator,
            vehicle_id,
            "std.battery_level.value",
            "Tracker Battery",
            icon="mdi:battery",
            device_class=SensorDeviceClass.BATTERY,
            unit_of_measurement=PERCENTAGE,
            state_class=SensorStateClass.MEASUREMENT,
            entity_category=EntityCategory.DIAGNOSTIC,
        )


class VehicleBatteryVoltageSensor(AutoPiDataFieldSensor):
    """Vehicle system battery voltage sensor."""

    def __init__(
        self, coordinator: AutoPiDataUpdateCoordinator, vehicle_id: str
    ) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator,
            vehicle_id,
            "std.battery_voltage.value",
            "Vehicle Battery Voltage",
            icon="mdi:car-battery",
            device_class=SensorDeviceClass.VOLTAGE,
            unit_of_measurement=UnitOfElectricPotential.VOLT,
            state_class=SensorStateClass.MEASUREMENT,
        )


# Accelerometer Sensors


class AccelerometerXSensor(AutoPiDataFieldSensor):
    """X-axis accelerometer sensor."""

    def __init__(
        self, coordinator: AutoPiDataUpdateCoordinator, vehicle_id: str
    ) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator,
            vehicle_id,
            "std.accelerometer_axis_x.value",
            "X-Axis Acceleration",
            icon="mdi:axis-x-arrow",
            unit_of_measurement="g",
            device_class=None,
            state_class=SensorStateClass.MEASUREMENT,
        )

    @property
    def native_value(self) -> float | None:
        """Return the sensor value converted to standard g."""
        value = super().native_value
        if value is not None:
            # Convert from milli-g to g
            return round(value / 1000.0, 3)
        return None


class AccelerometerYSensor(AutoPiDataFieldSensor):
    """Y-axis accelerometer sensor."""

    def __init__(
        self, coordinator: AutoPiDataUpdateCoordinator, vehicle_id: str
    ) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator,
            vehicle_id,
            "std.accelerometer_axis_y.value",
            "Y-Axis Acceleration",
            icon="mdi:axis-y-arrow",
            unit_of_measurement="g",
            device_class=None,
            state_class=SensorStateClass.MEASUREMENT,
        )

    @property
    def native_value(self) -> float | None:
        """Return the sensor value converted to standard g."""
        value = super().native_value
        if value is not None:
            # Convert from milli-g to g
            return round(value / 1000.0, 3)
        return None


class AccelerometerZSensor(AutoPiDataFieldSensor):
    """Z-axis accelerometer sensor."""

    def __init__(
        self, coordinator: AutoPiDataUpdateCoordinator, vehicle_id: str
    ) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator,
            vehicle_id,
            "std.accelerometer_axis_z.value",
            "Z-Axis Acceleration",
            icon="mdi:axis-z-arrow",
            unit_of_measurement="g",
            device_class=None,
            state_class=SensorStateClass.MEASUREMENT,
        )

    @property
    def native_value(self) -> float | None:
        """Return the sensor value converted to standard g."""
        value = super().native_value
        if value is not None:
            # Convert from milli-g to g
            return round(value / 1000.0, 3)
        return None


# Odometer and Distance Sensors


class TotalOdometerSensor(AutoPiDataFieldSensor):
    """Total odometer sensor."""

    def __init__(
        self, coordinator: AutoPiDataUpdateCoordinator, vehicle_id: str
    ) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator,
            vehicle_id,
            "std.total_odometer.value",
            "Odometer",
            icon="mdi:counter",
            device_class=SensorDeviceClass.DISTANCE,
            unit_of_measurement=UnitOfLength.METERS,
            state_class=SensorStateClass.TOTAL_INCREASING,
        )

    @property
    def native_value(self) -> float | None:
        """Return the sensor value converted to kilometers."""
        value = super().native_value
        if value is not None:
            # Convert from meters to kilometers
            return round(value / 1000.0, 1)
        return None

    @property
    def native_unit_of_measurement(self) -> str:
        """Return km as the unit."""
        return UnitOfLength.KILOMETERS


class TripOdometerSensor(AutoPiDataFieldSensor):
    """Trip odometer sensor."""

    def __init__(
        self, coordinator: AutoPiDataUpdateCoordinator, vehicle_id: str
    ) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator,
            vehicle_id,
            "std.trip_odometer.value",
            "Trip Odometer",
            icon="mdi:map-marker-distance",
            device_class=SensorDeviceClass.DISTANCE,
            unit_of_measurement=UnitOfLength.METERS,
            state_class=SensorStateClass.TOTAL_INCREASING,
        )

    @property
    def native_value(self) -> float | None:
        """Return the sensor value converted to kilometers."""
        value = super().native_value
        if value is not None:
            # Convert from meters to kilometers
            return round(value / 1000.0, 1)
        return None

    @property
    def native_unit_of_measurement(self) -> str:
        """Return km as the unit."""
        return UnitOfLength.KILOMETERS


class DistanceSinceCodesClearSensor(AutoPiDataFieldSensor):
    """Distance since diagnostic codes cleared sensor."""

    def __init__(
        self, coordinator: AutoPiDataUpdateCoordinator, vehicle_id: str
    ) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator,
            vehicle_id,
            "obd.distance_since_codes_clear.value",
            "Distance Since DTC Clear (OBD)",
            icon="mdi:road-variant",
            device_class=SensorDeviceClass.DISTANCE,
            unit_of_measurement=UnitOfLength.KILOMETERS,
            state_class=SensorStateClass.TOTAL_INCREASING,
            entity_category=EntityCategory.DIAGNOSTIC,
        )


# Fuel Sensors


class FuelUsedGPSSensor(AutoPiDataFieldSensor):
    """Fuel used GPS sensor."""

    def __init__(
        self, coordinator: AutoPiDataUpdateCoordinator, vehicle_id: str
    ) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator,
            vehicle_id,
            "std.fuel_used_gps.value",
            "Fuel Used (GPS)",
            icon="mdi:fuel",
            device_class=SensorDeviceClass.VOLUME,
            unit_of_measurement=UnitOfVolume.LITERS,
            state_class=SensorStateClass.TOTAL_INCREASING,
        )


class FuelRateGPSSensor(AutoPiDataFieldSensor):
    """Fuel rate GPS sensor."""

    def __init__(
        self, coordinator: AutoPiDataUpdateCoordinator, vehicle_id: str
    ) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator,
            vehicle_id,
            "std.fuel_rate_gps.value",
            "Fuel Rate (GPS)",
            icon="mdi:fuel",
            unit_of_measurement="L/h",
            state_class=SensorStateClass.MEASUREMENT,
        )


class FuelLevelSensor(AutoPiDataFieldSensor):
    """Fuel level sensor."""

    def __init__(
        self, coordinator: AutoPiDataUpdateCoordinator, vehicle_id: str
    ) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator,
            vehicle_id,
            "obd.fuel_level.value",
            "Fuel Level (OBD)",
            icon="mdi:gas-station",
            unit_of_measurement=PERCENTAGE,
            state_class=SensorStateClass.MEASUREMENT,
        )


class OEMFuelLevelSensor(AutoPiDataFieldSensor):
    """OEM fuel level sensor."""

    def __init__(
        self, coordinator: AutoPiDataUpdateCoordinator, vehicle_id: str
    ) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator,
            vehicle_id,
            "obd.obd_oem_fuel_level.value",
            "Fuel Volume (OBD)",
            icon="mdi:fuel",
            device_class=SensorDeviceClass.VOLUME_STORAGE,
            unit_of_measurement=UnitOfVolume.LITERS,
            state_class=SensorStateClass.MEASUREMENT,
        )


# Engine Sensors


class IgnitionStateSensor(AutoPiDataFieldSensor):
    """Ignition state sensor."""

    def __init__(
        self, coordinator: AutoPiDataUpdateCoordinator, vehicle_id: str
    ) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator,
            vehicle_id,
            "std.ignition.value",
            "Ignition State",
            icon="mdi:key",
        )


class EngineSensor(AutoPiDataFieldSensor):
    """Engine RPM sensor."""

    def __init__(
        self, coordinator: AutoPiDataUpdateCoordinator, vehicle_id: str
    ) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator,
            vehicle_id,
            "obd.rpm.value",
            "Engine RPM (OBD)",
            icon="mdi:engine",
            unit_of_measurement="rpm",
            state_class=SensorStateClass.MEASUREMENT,
        )


class EngineLoadSensor(AutoPiDataFieldSensor):
    """Engine load sensor."""

    def __init__(
        self, coordinator: AutoPiDataUpdateCoordinator, vehicle_id: str
    ) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator,
            vehicle_id,
            "obd.engine_load.value",
            "Engine Load (OBD)",
            icon="mdi:gauge",
            unit_of_measurement=PERCENTAGE,
            state_class=SensorStateClass.MEASUREMENT,
        )


class EngineRunTimeSensor(AutoPiDataFieldSensor):
    """Engine run time sensor."""

    def __init__(
        self, coordinator: AutoPiDataUpdateCoordinator, vehicle_id: str
    ) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator,
            vehicle_id,
            "obd.run_time.value",
            "Engine Run Time (OBD)",
            icon="mdi:timer",
            device_class=SensorDeviceClass.DURATION,
            unit_of_measurement=UnitOfTime.SECONDS,
            state_class=SensorStateClass.MEASUREMENT,
        )


class ThrottlePositionSensor(AutoPiDataFieldSensor):
    """Throttle position sensor."""

    def __init__(
        self, coordinator: AutoPiDataUpdateCoordinator, vehicle_id: str
    ) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator,
            vehicle_id,
            "obd.throttle_pos.value",
            "Throttle Position (OBD)",
            icon="mdi:gas-pedal",
            unit_of_measurement=PERCENTAGE,
            state_class=SensorStateClass.MEASUREMENT,
        )


# Speed Sensors


class OBDSpeedSensor(AutoPiDataFieldSensor):
    """OBD speed sensor."""

    def __init__(
        self, coordinator: AutoPiDataUpdateCoordinator, vehicle_id: str
    ) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator,
            vehicle_id,
            "obd.speed.value",
            "Vehicle Speed (OBD)",
            icon="mdi:speedometer",
            device_class=SensorDeviceClass.SPEED,
            unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
            state_class=SensorStateClass.MEASUREMENT,
        )


class TrackerSpeedSensor(AutoPiDataFieldSensor):
    """Tracker-derived speed sensor."""

    def __init__(
        self, coordinator: AutoPiDataUpdateCoordinator, vehicle_id: str
    ) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator,
            vehicle_id,
            "std.speed.value",
            "Tracker Speed (GPS)",
            icon="mdi:speedometer",
            device_class=SensorDeviceClass.SPEED,
            unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
            state_class=SensorStateClass.MEASUREMENT,
        )


# Temperature Sensors


class AmbientTemperatureSensor(AutoPiDataFieldSensor):
    """Ambient air temperature sensor."""

    def __init__(
        self, coordinator: AutoPiDataUpdateCoordinator, vehicle_id: str
    ) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator,
            vehicle_id,
            "obd.ambient_air_temp.value",
            "Ambient Temperature (OBD)",
            icon="mdi:thermometer",
            device_class=SensorDeviceClass.TEMPERATURE,
            unit_of_measurement=UnitOfTemperature.CELSIUS,
            state_class=SensorStateClass.MEASUREMENT,
        )


class IntakeTemperatureSensor(AutoPiDataFieldSensor):
    """Intake air temperature sensor."""

    def __init__(
        self, coordinator: AutoPiDataUpdateCoordinator, vehicle_id: str
    ) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator,
            vehicle_id,
            "obd.intake_temp.value",
            "Intake Temperature (OBD)",
            icon="mdi:thermometer",
            device_class=SensorDeviceClass.TEMPERATURE,
            unit_of_measurement=UnitOfTemperature.CELSIUS,
            state_class=SensorStateClass.MEASUREMENT,
        )


class CoolantTemperatureSensor(AutoPiDataFieldSensor):
    """Engine coolant temperature sensor."""

    def __init__(
        self, coordinator: AutoPiDataUpdateCoordinator, vehicle_id: str
    ) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator,
            vehicle_id,
            "obd.coolant_temp.value",
            "Coolant Temperature (OBD)",
            icon="mdi:thermometer",
            device_class=SensorDeviceClass.TEMPERATURE,
            unit_of_measurement=UnitOfTemperature.CELSIUS,
            state_class=SensorStateClass.MEASUREMENT,
        )


# Other Sensors


class GSMSignalSensor(AutoPiDataFieldSensor):
    """GSM signal strength sensor."""

    def __init__(
        self, coordinator: AutoPiDataUpdateCoordinator, vehicle_id: str
    ) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator,
            vehicle_id,
            "std.gsm_signal.value",
            "Cellular Signal Strength",
            icon="mdi:signal",
            state_class=SensorStateClass.MEASUREMENT,
            entity_category=EntityCategory.DIAGNOSTIC,
        )

    @property
    def native_value(self) -> int | None:
        """Return the sensor value."""
        value = super().native_value
        if value is not None:
            # Convert 0-31 scale to percentage
            return round((value / 31) * 100)
        return None

    @property
    def native_unit_of_measurement(self) -> str:
        """Return percentage as unit."""
        return PERCENTAGE


class DTCCountSensor(AutoPiDataFieldSensor):
    """Diagnostic trouble code count sensor."""

    def __init__(
        self, coordinator: AutoPiDataUpdateCoordinator, vehicle_id: str
    ) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator,
            vehicle_id,
            "obd.number_of_dtc.value",
            "DTC Count",
            icon="mdi:alert-circle",
            state_class=SensorStateClass.MEASUREMENT,
            entity_category=EntityCategory.DIAGNOSTIC,
        )


# Sensor mapping
FIELD_ID_TO_SENSOR_CLASS: dict[str, Any] = {
    "obd.bat.level": BatteryChargeLevelSensor,
    "obd.bat.voltage": BatteryVoltageSensor,
    "std.accelerometer_axis_x.value": AccelerometerXSensor,
    "std.accelerometer_axis_y.value": AccelerometerYSensor,
    "std.accelerometer_axis_z.value": AccelerometerZSensor,
    "std.battery_current.value": BatteryCurrentSensor,
    "std.battery_level.value": TrackerBatteryLevelSensor,
    "std.total_odometer.value": TotalOdometerSensor,
    "std.fuel_used_gps.value": FuelUsedGPSSensor,
    "std.ignition.value": IgnitionStateSensor,
    "std.trip_odometer.value": TripOdometerSensor,
    "std.fuel_rate_gps.value": FuelRateGPSSensor,
    "std.gsm_signal.value": GSMSignalSensor,
    "obd.ambient_air_temp.value": AmbientTemperatureSensor,
    "obd.engine_load.value": EngineLoadSensor,
    "obd.fuel_level.value": FuelLevelSensor,
    "obd.intake_temp.value": IntakeTemperatureSensor,
    "obd.rpm.value": EngineSensor,
    "obd.speed.value": OBDSpeedSensor,
    "obd.distance_since_codes_clear.value": DistanceSinceCodesClearSensor,
    "obd.number_of_dtc.value": DTCCountSensor,
    "obd.obd_oem_fuel_level.value": OEMFuelLevelSensor,
    "obd.run_time.value": EngineRunTimeSensor,
    "obd.throttle_pos.value": ThrottlePositionSensor,
    "std.battery_voltage.value": VehicleBatteryVoltageSensor,
    "std.speed.value": TrackerSpeedSensor,
    "obd.coolant_temp.value": CoolantTemperatureSensor,
}


def create_data_field_sensors(
    coordinator: AutoPiDataUpdateCoordinator,
    vehicle_id: str,
    available_fields: set[str],
) -> list[AutoPiDataFieldSensor]:
    """Create sensor entities for available data fields."""
    sensors = []

    for field_id, sensor_class in FIELD_ID_TO_SENSOR_CLASS.items():
        if field_id in available_fields:
            try:
                sensor = sensor_class(coordinator, vehicle_id)
                sensors.append(sensor)
                _LOGGER.debug(
                    "Created sensor for field %s on vehicle %s",
                    field_id,
                    vehicle_id,
                )
            except Exception as err:
                _LOGGER.error(
                    "Failed to create sensor for field %s: %s",
                    field_id,
                    err,
                )

    return sensors
