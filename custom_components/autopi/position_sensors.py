"""Position sensors using data fields for AutoPi integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.const import (
    EntityCategory,
    UnitOfLength,
    UnitOfSpeed,
)

from .coordinator import AutoPiDataUpdateCoordinator
from .data_field_sensors import AutoPiDataFieldSensor

_LOGGER = logging.getLogger(__name__)


class GPSAltitudeSensor(AutoPiDataFieldSensor):
    """GPS altitude sensor."""

    def __init__(
        self, coordinator: AutoPiDataUpdateCoordinator, vehicle_id: str
    ) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator,
            vehicle_id,
            "track.pos.alt",
            "GPS Altitude",
            icon="mdi:elevation-rise",
            device_class=SensorDeviceClass.DISTANCE,
            unit_of_measurement=UnitOfLength.METERS,
            state_class=SensorStateClass.MEASUREMENT,
        )


class GPSSpeedSensor(AutoPiDataFieldSensor):
    """GPS speed sensor."""

    def __init__(
        self, coordinator: AutoPiDataUpdateCoordinator, vehicle_id: str
    ) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator,
            vehicle_id,
            "track.pos.sog",
            "GPS Speed",
            icon="mdi:speedometer",
            device_class=SensorDeviceClass.SPEED,
            unit_of_measurement=UnitOfSpeed.METERS_PER_SECOND,
            state_class=SensorStateClass.MEASUREMENT,
        )


class GPSCourseSensor(AutoPiDataFieldSensor):
    """GPS course/heading sensor."""

    def __init__(
        self, coordinator: AutoPiDataUpdateCoordinator, vehicle_id: str
    ) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator,
            vehicle_id,
            "track.pos.cog",
            "GPS Course",
            icon="mdi:compass",
            unit_of_measurement="°",
            state_class=SensorStateClass.MEASUREMENT,
        )


class GPSSatellitesSensor(AutoPiDataFieldSensor):
    """GPS satellites sensor."""

    def __init__(
        self, coordinator: AutoPiDataUpdateCoordinator, vehicle_id: str
    ) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator,
            vehicle_id,
            "track.pos.nsat",
            "GPS Satellites",
            icon="mdi:satellite-variant",
            state_class=SensorStateClass.MEASUREMENT,
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        attrs = super().extra_state_attributes

        # Add location accuracy based on satellite count
        if self.native_value is not None:
            num_satellites = int(self.native_value)
            if num_satellites < 4:
                accuracy = 100.0
            elif num_satellites == 4:
                accuracy = 30.0
            elif num_satellites == 5:
                accuracy = 20.0
            elif num_satellites == 6:
                accuracy = 15.0
            elif num_satellites == 7:
                accuracy = 11.0
            elif num_satellites in (8, 9):
                accuracy = 7.5
            elif num_satellites in (10, 11):
                accuracy = 5.0
            else:  # 12+
                accuracy = 3.0

            attrs["location_accuracy"] = accuracy

        return attrs


class GPSLatitudeSensor(AutoPiDataFieldSensor):
    """GPS latitude sensor."""

    def __init__(
        self, coordinator: AutoPiDataUpdateCoordinator, vehicle_id: str
    ) -> None:
        """Initialize the sensor."""
        # Call parent init with custom parameters
        super().__init__(
            coordinator,
            vehicle_id,
            "track.pos.loc",  # field_id
            "GPS Latitude",  # name
            icon="mdi:latitude",
            state_class=SensorStateClass.MEASUREMENT,
            entity_category=EntityCategory.DIAGNOSTIC,
        )
        # Override the unique_id suffix
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_vehicle_{vehicle_id}_data_field_track_pos_lat"

    @property
    def native_value(self) -> float | None:
        """Return the sensor value."""
        field_data = self._get_field_data()

        if field_data is not None and isinstance(field_data.last_value, dict):
            lat = field_data.last_value.get("lat")
            if lat is not None:
                # Update our last known value and time
                self._last_known_value = lat
                self._last_update_time = field_data.last_update
                return round(float(lat), 6)

        # Use cached value logic from parent
        return super().native_value


class GPSLongitudeSensor(AutoPiDataFieldSensor):
    """GPS longitude sensor."""

    def __init__(
        self, coordinator: AutoPiDataUpdateCoordinator, vehicle_id: str
    ) -> None:
        """Initialize the sensor."""
        # Call parent init with custom parameters
        super().__init__(
            coordinator,
            vehicle_id,
            "track.pos.loc",  # field_id
            "GPS Longitude",  # name
            icon="mdi:longitude",
            state_class=SensorStateClass.MEASUREMENT,
            entity_category=EntityCategory.DIAGNOSTIC,
        )
        # Override the unique_id suffix
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_vehicle_{vehicle_id}_data_field_track_pos_lon"

    @property
    def native_value(self) -> float | None:
        """Return the sensor value."""
        field_data = self._get_field_data()

        if field_data is not None and isinstance(field_data.last_value, dict):
            lon = field_data.last_value.get("lon")
            if lon is not None:
                # Update our last known value and time
                self._last_known_value = lon
                self._last_update_time = field_data.last_update
                return round(float(lon), 6)

        # Use cached value logic from parent
        return super().native_value


# Position sensor mapping
POSITION_FIELD_TO_SENSOR_CLASS: dict[str, Any] = {
    "track.pos.alt": GPSAltitudeSensor,
    "track.pos.sog": GPSSpeedSensor,
    "track.pos.cog": GPSCourseSensor,
    "track.pos.nsat": GPSSatellitesSensor,
    "track.pos.loc": (
        GPSLatitudeSensor,
        GPSLongitudeSensor,
    ),  # Special case for lat/lon
}


def create_position_sensors(
    coordinator: AutoPiDataUpdateCoordinator,
    vehicle_id: str,
    available_fields: set[str],
) -> list[AutoPiDataFieldSensor]:
    """Create position sensor entities for available data fields."""
    sensors = []

    for field_id, sensor_info in POSITION_FIELD_TO_SENSOR_CLASS.items():
        if field_id in available_fields:
            try:
                # Handle special case for lat/lon which share the same field
                if isinstance(sensor_info, tuple):
                    for sensor_class in sensor_info:
                        sensor = sensor_class(coordinator, vehicle_id)
                        sensors.append(sensor)
                        _LOGGER.debug(
                            "Created position sensor %s for vehicle %s",
                            sensor.__class__.__name__,
                            vehicle_id,
                        )
                else:
                    sensor = sensor_info(coordinator, vehicle_id)
                    sensors.append(sensor)
                    _LOGGER.debug(
                        "Created position sensor for field %s on vehicle %s",
                        field_id,
                        vehicle_id,
                    )
            except Exception:
                _LOGGER.exception(
                    "Failed to create position sensor for field %s",
                    field_id,
                )

    return sensors
