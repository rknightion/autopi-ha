"""Data field sensors for AutoPi integration."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
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
from homeassistant.helpers.restore_state import RestoreEntity

from .auto_zero import AUTO_ZERO_METRICS, get_auto_zero_manager
from .const import CONF_AUTO_ZERO_ENABLED, DATA_FIELD_TIMEOUT_MINUTES
from .coordinator import AutoPiDataUpdateCoordinator
from .entities.base import AutoPiVehicleEntity
from .types import DataFieldValue

_LOGGER = logging.getLogger(__name__)


class AutoPiDataFieldSensorBase(AutoPiVehicleEntity, SensorEntity):
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

        # Log sensor creation
        _LOGGER.debug(
            "[SENSOR INIT] Created sensor %s for vehicle %s (field_id: %s, auto-zero capable: %s)",
            name,
            vehicle_id,
            field_id,
            field_id in AUTO_ZERO_METRICS,
        )

    @property
    def native_value(self) -> Any:
        """Return the sensor value."""
        try:
            # Check if auto-zero is enabled and this metric supports it
            if self._field_id in AUTO_ZERO_METRICS:
                auto_zero_enabled = self.coordinator.config_entry.options.get(
                    CONF_AUTO_ZERO_ENABLED, False
                )

                if auto_zero_enabled:
                    auto_zero_manager = get_auto_zero_manager()

                    # Special handling: If metric is already marked as zeroed in storage
                    # but we haven't fetched data yet, return 0 immediately
                    if auto_zero_manager.is_metric_zeroed(
                        self._vehicle_id, self._field_id
                    ):
                        field_data = self._get_field_data()
                        if field_data is None:
                            _LOGGER.debug(
                                "Sensor %s for vehicle %s is marked as zeroed and no data available, returning 0",
                                self._attr_name,
                                self._vehicle_id,
                            )
                            return 0

            field_data = self._get_field_data()

            if field_data is not None:
                # Update our last known value and time
                self._last_known_value = field_data.last_value
                self._last_update_time = field_data.last_update

                _LOGGER.debug(
                    "Sensor %s for vehicle %s has value %s (last_seen: %s)",
                    self._attr_name,
                    self._vehicle_id,
                    field_data.last_value,
                    field_data.last_seen.isoformat()
                    if field_data.last_seen
                    else "None",
                )

                # Check if auto-zero should be applied
                if self._field_id in AUTO_ZERO_METRICS:
                    auto_zero_enabled = self.coordinator.config_entry.options.get(
                        CONF_AUTO_ZERO_ENABLED, False
                    )
                    _LOGGER.debug(
                        "Auto-zero check for %s on vehicle %s: enabled=%s, field_id=%s, options=%s",
                        self._attr_name,
                        self._vehicle_id,
                        auto_zero_enabled,
                        self._field_id,
                        self.coordinator.config_entry.options,
                    )

                    # Check if we should zero the metric
                    auto_zero_manager = get_auto_zero_manager()
                    if auto_zero_manager.should_zero_metric(
                        self._vehicle_id,
                        self._field_id,
                        field_data,
                        auto_zero_enabled,
                    ):
                        _LOGGER.debug(
                            "Auto-zeroing sensor %s for vehicle %s",
                            self._attr_name,
                            self._vehicle_id,
                        )
                        return 0

                return field_data.last_value

            # If we have a last known value and it's within timeout, return it
            if (
                self._last_known_value is not None
                and self._last_update_time is not None
            ):
                if datetime.now(UTC) - self._last_update_time < timedelta(
                    minutes=DATA_FIELD_TIMEOUT_MINUTES
                ):
                    _LOGGER.debug(
                        "[SENSOR CACHE] Using cached value %s for sensor %s on vehicle %s (last update: %.1f min ago)",
                        self._last_known_value,
                        self._attr_name,
                        self._vehicle_id,
                        (datetime.now(UTC) - self._last_update_time).total_seconds()
                        / 60,
                    )
                    return self._last_known_value

            _LOGGER.debug(
                "[SENSOR] No value available for sensor %s on vehicle %s (no data, no cache)",
                self._attr_name,
                self._vehicle_id,
            )
            return None

        except Exception as e:
            _LOGGER.error(
                "Error getting value for sensor %s on vehicle %s: %s",
                self._attr_name,
                self._vehicle_id,
                str(e),
                exc_info=True,
            )
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
            if datetime.now(UTC) - self._last_update_time < timedelta(
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
            time_since_update = datetime.now(UTC) - self._last_update_time
            if time_since_update > timedelta(seconds=0):
                attrs["data_age_seconds"] = int(time_since_update.total_seconds())

        # Always show auto-zero enabled status
        attrs["auto_zero_enabled"] = self._field_id in AUTO_ZERO_METRICS

        # Add detailed auto-zero status if enabled
        if self._field_id in AUTO_ZERO_METRICS:
            auto_zero_manager = get_auto_zero_manager()
            auto_zero_status = auto_zero_manager.get_metric_status(
                self._vehicle_id, self._field_id
            )
            # Remove the redundant auto_zero_enabled from status since we already added it
            auto_zero_status.pop("auto_zero_enabled", None)

            # Format timestamps nicely if present
            if "zeroed_at" in auto_zero_status:
                attrs["auto_zero_last_zeroed"] = auto_zero_status.pop("zeroed_at")
            if "cooldown_until" in auto_zero_status:
                attrs["auto_zero_cooldown_until"] = auto_zero_status.pop(
                    "cooldown_until"
                )

            # Add is_zeroed status
            if "is_zeroed" in auto_zero_status:
                attrs["auto_zero_active"] = auto_zero_status.pop("is_zeroed")

            attrs.update(auto_zero_status)

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


class AutoPiDataFieldSensor(AutoPiDataFieldSensorBase):
    """Data field sensor without auto-zero support."""

    pass


class AutoPiAutoZeroDataFieldSensor(AutoPiDataFieldSensorBase, RestoreEntity):
    """Data field sensor with auto-zero support and state restoration."""

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
        """Initialize the auto-zero data field sensor."""
        super().__init__(
            coordinator,
            vehicle_id,
            field_id,
            name,
            icon,
            device_class,
            unit_of_measurement,
            state_class,
            entity_category,
        )
        self._was_zeroed: bool = False
        self._restored_value: Any = None

    async def async_added_to_hass(self) -> None:
        """Handle entity being added to Home Assistant."""
        await super().async_added_to_hass()

        # Restore last state
        if (last_state := await self.async_get_last_state()) is not None:
            _LOGGER.debug(
                "Restoring state for %s on vehicle %s: %s",
                self._attr_name,
                self._vehicle_id,
                last_state.state,
            )

            # Check if it was zeroed
            if (attrs := last_state.attributes) is not None:
                if attrs.get("is_zeroed", False):
                    # Restore as zeroed
                    self._was_zeroed = True
                    self._restored_value = 0
                    _LOGGER.info(
                        "Restored zeroed state for %s on vehicle %s",
                        self._attr_name,
                        self._vehicle_id,
                    )
                elif last_state.state not in ("unknown", "unavailable"):
                    # Restore the actual value
                    try:
                        if self._attr_device_class == SensorDeviceClass.TEMPERATURE:
                            self._restored_value = float(last_state.state)
                        elif self._attr_state_class == SensorStateClass.MEASUREMENT:
                            self._restored_value = float(last_state.state)
                        else:
                            self._restored_value = last_state.state
                    except (ValueError, TypeError):
                        _LOGGER.warning(
                            "Failed to restore value for %s on vehicle %s",
                            self._attr_name,
                            self._vehicle_id,
                        )

    @property
    def native_value(self) -> Any:
        """Return the sensor value."""
        try:
            # Get the value from parent implementation (which handles auto-zero)
            value = super().native_value

            # If parent returned None and we have a restored value, use it
            if value is None and self._restored_value is not None:
                _LOGGER.debug(
                    "Using restored value %s for sensor %s on vehicle %s",
                    self._restored_value,
                    self._attr_name,
                    self._vehicle_id,
                )
                return self._restored_value

            return value

        except Exception as e:
            _LOGGER.error(
                "Error getting value for sensor %s on vehicle %s: %s",
                self._attr_name,
                self._vehicle_id,
                str(e),
                exc_info=True,
            )
            return None


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


class AccelerometerXSensor(AutoPiAutoZeroDataFieldSensor):
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


class AccelerometerYSensor(AutoPiAutoZeroDataFieldSensor):
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


class AccelerometerZSensor(AutoPiAutoZeroDataFieldSensor):
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
            unit_of_measurement=UnitOfLength.KILOMETERS,
            state_class=SensorStateClass.TOTAL_INCREASING,
        )

    @property
    def native_value(self) -> float | None:
        """Return the sensor value converted to kilometers."""
        value = super().native_value
        if value is not None:
            # Convert from meters to kilometers
            return round(value / 1000.0, 2)
        return None


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


class FuelUsedGPSSensor(AutoPiAutoZeroDataFieldSensor):
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


class EngineSensor(AutoPiAutoZeroDataFieldSensor):
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


class EngineLoadSensor(AutoPiAutoZeroDataFieldSensor):
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


class EngineRunTimeSensor(AutoPiAutoZeroDataFieldSensor):
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


class ThrottlePositionSensor(AutoPiAutoZeroDataFieldSensor):
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


class OBDSpeedSensor(AutoPiAutoZeroDataFieldSensor):
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


class CoolantTemperatureSensor(AutoPiAutoZeroDataFieldSensor):
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
            # Convert 1-5 scale to percentage
            # 1 = 20%, 2 = 40%, 3 = 60%, 4 = 80%, 5 = 100%
            return round((value / 5) * 100)
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
            except Exception:
                _LOGGER.exception(
                    "Failed to create sensor for field %s",
                    field_id,
                )

    return sensors
