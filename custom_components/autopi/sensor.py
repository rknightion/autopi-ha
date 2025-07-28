"""Support for AutoPi sensors."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, UnitOfLength, UnitOfSpeed
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, MANUFACTURER
from .coordinator import AutoPiDataUpdateCoordinator
from .entities.base import AutoPiEntity, AutoPiVehicleEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up AutoPi sensors from a config entry."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    coordinator: AutoPiDataUpdateCoordinator = data["coordinator"]
    position_coordinator: AutoPiDataUpdateCoordinator = data["position_coordinator"]

    _LOGGER.debug(
        "Setting up AutoPi sensors for config entry %s", config_entry.entry_id
    )

    entities: list[SensorEntity] = []

    # Add vehicle count sensor
    entities.append(AutoPiVehicleCountSensor(coordinator))

    # Add diagnostic sensors
    entities.append(AutoPiAPICallsSensor(coordinator))
    entities.append(AutoPiFailedAPICallsSensor(coordinator))
    entities.append(AutoPiSuccessRateSensor(coordinator))
    entities.append(AutoPiUpdateDurationSensor(coordinator))

    # Add individual vehicle sensors
    if coordinator.data:
        for vehicle_id, vehicle in coordinator.data.items():
            _LOGGER.debug(
                "Creating vehicle sensor for %s (%s)", vehicle.name, vehicle_id
            )
            entities.append(AutoPiVehicleSensor(coordinator, vehicle_id))

            # Add position-related sensors
            entities.append(AutoPiVehicleAltitudeSensor(position_coordinator, vehicle_id))
            entities.append(AutoPiVehicleSpeedSensor(position_coordinator, vehicle_id))
            entities.append(AutoPiVehicleCourseSensor(position_coordinator, vehicle_id))
            entities.append(AutoPiVehicleSatellitesSensor(position_coordinator, vehicle_id))
            entities.append(AutoPiVehicleLatitudeSensor(position_coordinator, vehicle_id))
            entities.append(AutoPiVehicleLongitudeSensor(position_coordinator, vehicle_id))

    _LOGGER.info("Adding %d AutoPi sensor entities", len(entities))

    async_add_entities(entities)


class AutoPiVehicleCountSensor(AutoPiEntity, SensorEntity):
    """Sensor showing the total number of vehicles."""

    # Remove device_class as it's not appropriate for a vehicle count
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "vehicles"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:car-multiple"

    def __init__(self, coordinator: AutoPiDataUpdateCoordinator) -> None:
        """Initialize the vehicle count sensor."""
        super().__init__(coordinator, "vehicle_count")
        self._attr_name = "Vehicle Count"

        _LOGGER.debug("Initialized AutoPi vehicle count sensor")

    @property
    def native_value(self) -> int:
        """Return the number of vehicles."""
        return self.coordinator.get_vehicle_count()

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.config_entry.entry_id)},
            name="AutoPi Integration",
            manufacturer=MANUFACTURER,
            configuration_url="https://app.autopi.io",
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        if not self.coordinator.data:
            return {}

        return {
            "vehicles": [
                {
                    "id": vehicle.id,
                    "name": vehicle.name,
                    "license_plate": vehicle.license_plate,
                }
                for vehicle in self.coordinator.data.values()
            ]
        }


class AutoPiVehicleSensor(AutoPiVehicleEntity, SensorEntity):
    """Sensor representing an individual vehicle."""

    _attr_icon = "mdi:car"

    def __init__(
        self,
        coordinator: AutoPiDataUpdateCoordinator,
        vehicle_id: str,
    ) -> None:
        """Initialize the vehicle sensor."""
        super().__init__(coordinator, vehicle_id, "vehicle")

        _LOGGER.debug("Initialized AutoPi vehicle sensor for vehicle %s", vehicle_id)

    @property
    def name(self) -> str | None:
        """Return the name of the sensor."""
        # Since we're using has_entity_name, just return a simple name
        # The device name will be prepended automatically
        return "Status"

    @property
    def native_value(self) -> str | None:
        """Return the state of the sensor."""
        if vehicle := self.vehicle:
            return vehicle.license_plate or vehicle.name
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        attrs = super().extra_state_attributes

        if vehicle := self.vehicle:
            # Add any additional vehicle-specific attributes
            attrs.update(
                {
                    "name": vehicle.name,
                }
            )

        return attrs


class AutoPiAPICallsSensor(AutoPiEntity, SensorEntity):
    """Sensor showing the total number of API calls."""

    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:api"

    def __init__(self, coordinator: AutoPiDataUpdateCoordinator) -> None:
        """Initialize the API calls sensor."""
        super().__init__(coordinator, "api_calls")
        self._attr_name = "API Calls"

    @property
    def native_value(self) -> int:
        """Return the number of API calls."""
        return self.coordinator.api_call_count

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.config_entry.entry_id)},
            name="AutoPi Integration",
            manufacturer=MANUFACTURER,
            configuration_url="https://app.autopi.io",
        )


class AutoPiFailedAPICallsSensor(AutoPiEntity, SensorEntity):
    """Sensor showing the number of failed API calls."""

    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:alert-circle"

    def __init__(self, coordinator: AutoPiDataUpdateCoordinator) -> None:
        """Initialize the failed API calls sensor."""
        super().__init__(coordinator, "failed_api_calls")
        self._attr_name = "Failed API Calls"

    @property
    def native_value(self) -> int:
        """Return the number of failed API calls."""
        return self.coordinator.failed_api_call_count

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.config_entry.entry_id)},
            name="AutoPi Integration",
            manufacturer=MANUFACTURER,
            configuration_url="https://app.autopi.io",
        )


class AutoPiSuccessRateSensor(AutoPiEntity, SensorEntity):
    """Sensor showing the API success rate."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "%"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:percent"

    def __init__(self, coordinator: AutoPiDataUpdateCoordinator) -> None:
        """Initialize the success rate sensor."""
        super().__init__(coordinator, "api_success_rate")
        self._attr_name = "API Success Rate"

    @property
    def native_value(self) -> float:
        """Return the success rate."""
        return round(self.coordinator.success_rate, 1)

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.config_entry.entry_id)},
            name="AutoPi Integration",
            manufacturer=MANUFACTURER,
            configuration_url="https://app.autopi.io",
        )


class AutoPiUpdateDurationSensor(AutoPiEntity, SensorEntity):
    """Sensor showing the duration of the last update."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "s"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:timer"

    def __init__(self, coordinator: AutoPiDataUpdateCoordinator) -> None:
        """Initialize the update duration sensor."""
        super().__init__(coordinator, "update_duration")
        self._attr_name = "Update Duration"

    @property
    def native_value(self) -> float | None:
        """Return the update duration."""
        if self.coordinator.last_update_duration is not None:
            return round(self.coordinator.last_update_duration, 3)
        return None

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.config_entry.entry_id)},
            name="AutoPi Integration",
            manufacturer=MANUFACTURER,
            configuration_url="https://app.autopi.io",
        )


class AutoPiVehicleAltitudeSensor(AutoPiVehicleEntity, SensorEntity):
    """Sensor representing a vehicle's altitude."""

    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfLength.METERS
    _attr_icon = "mdi:elevation-rise"

    def __init__(
        self,
        coordinator: AutoPiDataUpdateCoordinator,
        vehicle_id: str,
    ) -> None:
        """Initialize the altitude sensor."""
        super().__init__(coordinator, vehicle_id, "altitude")
        _LOGGER.debug("Initialized AutoPi altitude sensor for vehicle %s", vehicle_id)

    @property
    def name(self) -> str | None:
        """Return the name of the sensor."""
        return "Altitude"

    @property
    def native_value(self) -> float | None:
        """Return the altitude of the vehicle."""
        if vehicle := self.vehicle:
            if vehicle.position:
                return vehicle.position.altitude
        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        # Only available if we have position data
        return (
            super().available
            and self.vehicle is not None
            and self.vehicle.position is not None
        )


class AutoPiVehicleSpeedSensor(AutoPiVehicleEntity, SensorEntity):
    """Sensor representing a vehicle's speed."""

    _attr_device_class = SensorDeviceClass.SPEED
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfSpeed.METERS_PER_SECOND
    _attr_icon = "mdi:speedometer"

    def __init__(
        self,
        coordinator: AutoPiDataUpdateCoordinator,
        vehicle_id: str,
    ) -> None:
        """Initialize the speed sensor."""
        super().__init__(coordinator, vehicle_id, "speed")
        _LOGGER.debug("Initialized AutoPi speed sensor for vehicle %s", vehicle_id)

    @property
    def name(self) -> str | None:
        """Return the name of the sensor."""
        return "Speed"

    @property
    def native_value(self) -> float | None:
        """Return the speed of the vehicle."""
        if vehicle := self.vehicle:
            if vehicle.position:
                return vehicle.position.speed
        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            super().available
            and self.vehicle is not None
            and self.vehicle.position is not None
        )


class AutoPiVehicleCourseSensor(AutoPiVehicleEntity, SensorEntity):
    """Sensor representing a vehicle's course (direction)."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "°"
    _attr_icon = "mdi:compass"

    def __init__(
        self,
        coordinator: AutoPiDataUpdateCoordinator,
        vehicle_id: str,
    ) -> None:
        """Initialize the course sensor."""
        super().__init__(coordinator, vehicle_id, "course")
        _LOGGER.debug("Initialized AutoPi course sensor for vehicle %s", vehicle_id)

    @property
    def name(self) -> str | None:
        """Return the name of the sensor."""
        return "Course"

    @property
    def native_value(self) -> float | None:
        """Return the course of the vehicle."""
        if vehicle := self.vehicle:
            if vehicle.position:
                return vehicle.position.course
        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            super().available
            and self.vehicle is not None
            and self.vehicle.position is not None
        )


class AutoPiVehicleSatellitesSensor(AutoPiVehicleEntity, SensorEntity):
    """Sensor representing the number of GPS satellites."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:satellite-variant"

    def __init__(
        self,
        coordinator: AutoPiDataUpdateCoordinator,
        vehicle_id: str,
    ) -> None:
        """Initialize the satellites sensor."""
        super().__init__(coordinator, vehicle_id, "satellites")
        _LOGGER.debug("Initialized AutoPi satellites sensor for vehicle %s", vehicle_id)

    @property
    def name(self) -> str | None:
        """Return the name of the sensor."""
        return "GPS Satellites"

    @property
    def native_value(self) -> int | None:
        """Return the number of satellites."""
        if vehicle := self.vehicle:
            if vehicle.position:
                return vehicle.position.num_satellites
        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            super().available
            and self.vehicle is not None
            and self.vehicle.position is not None
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        attrs = super().extra_state_attributes

        if vehicle := self.vehicle:
            if vehicle.position:
                attrs["location_accuracy"] = vehicle.position.location_accuracy
                attrs["timestamp"] = vehicle.position.timestamp.isoformat()

        return attrs


class AutoPiVehicleLatitudeSensor(AutoPiVehicleEntity, SensorEntity):
    """Sensor representing a vehicle's latitude."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:latitude"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: AutoPiDataUpdateCoordinator,
        vehicle_id: str,
    ) -> None:
        """Initialize the latitude sensor."""
        super().__init__(coordinator, vehicle_id, "latitude")
        _LOGGER.debug("Initialized AutoPi latitude sensor for vehicle %s", vehicle_id)

    @property
    def name(self) -> str | None:
        """Return the name of the sensor."""
        return "Latitude"

    @property
    def native_value(self) -> float | None:
        """Return the latitude of the vehicle."""
        if vehicle := self.vehicle:
            if vehicle.position:
                return round(vehicle.position.latitude, 6)
        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            super().available
            and self.vehicle is not None
            and self.vehicle.position is not None
        )


class AutoPiVehicleLongitudeSensor(AutoPiVehicleEntity, SensorEntity):
    """Sensor representing a vehicle's longitude."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:longitude"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: AutoPiDataUpdateCoordinator,
        vehicle_id: str,
    ) -> None:
        """Initialize the longitude sensor."""
        super().__init__(coordinator, vehicle_id, "longitude")
        _LOGGER.debug("Initialized AutoPi longitude sensor for vehicle %s", vehicle_id)

    @property
    def name(self) -> str | None:
        """Return the name of the sensor."""
        return "Longitude"

    @property
    def native_value(self) -> float | None:
        """Return the longitude of the vehicle."""
        if vehicle := self.vehicle:
            if vehicle.position:
                return round(vehicle.position.longitude, 6)
        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            super().available
            and self.vehicle is not None
            and self.vehicle.position is not None
        )
