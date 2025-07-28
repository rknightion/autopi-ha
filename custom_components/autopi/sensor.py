"""Support for AutoPi sensors."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import AutoPiDataUpdateCoordinator
from .data_field_sensors import create_data_field_sensors
from .entities.base import AutoPiEntity, AutoPiVehicleEntity
from .position_sensors import create_position_sensors

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
    all_coordinators = data["coordinators"]

    _LOGGER.debug(
        "Setting up AutoPi sensors for config entry %s", config_entry.entry_id
    )

    entities: list[SensorEntity] = []

    # Add vehicle count sensor
    entities.append(AutoPiVehicleCountSensor(coordinator))

    # Add diagnostic sensors (these aggregate from all coordinators)
    entities.append(AutoPiAPICallsSensor(all_coordinators))
    entities.append(AutoPiFailedAPICallsSensor(all_coordinators))
    entities.append(AutoPiSuccessRateSensor(all_coordinators))
    entities.append(AutoPiUpdateDurationSensor(all_coordinators))

    # Add individual vehicle sensors
    if coordinator.data:
        for vehicle_id, vehicle in coordinator.data.items():
            _LOGGER.debug(
                "Creating vehicle sensor for %s (%s)", vehicle.name, vehicle_id
            )
            entities.append(AutoPiVehicleSensor(coordinator, vehicle_id))

            # Add data field sensors if available (includes position sensors)
            if position_coordinator.data and vehicle_id in position_coordinator.data:
                vehicle_data = position_coordinator.data[vehicle_id]
                if vehicle_data.data_fields:
                    available_fields = set(vehicle_data.data_fields.keys())

                    # Create position sensors from data fields
                    position_sensors = create_position_sensors(
                        position_coordinator, vehicle_id, available_fields
                    )
                    entities.extend(position_sensors)
                    _LOGGER.debug(
                        "Created %d position sensors for vehicle %s",
                        len(position_sensors),
                        vehicle.name,
                    )

                    # Create other data field sensors
                    data_field_sensors = create_data_field_sensors(
                        position_coordinator, vehicle_id, available_fields
                    )
                    entities.extend(data_field_sensors)
                    _LOGGER.debug(
                        "Created %d data field sensors for vehicle %s",
                        len(data_field_sensors),
                        vehicle.name,
                    )

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


class AutoPiAPICallsSensor(RestoreEntity, SensorEntity):
    """Sensor showing the total number of API calls across all coordinators."""

    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:api"
    _attr_has_entity_name = True

    def __init__(self, coordinators: dict[str, AutoPiDataUpdateCoordinator]) -> None:
        """Initialize the API calls sensor."""
        self._coordinators = coordinators
        # Use the first coordinator's config entry for the unique ID
        first_coordinator = next(iter(coordinators.values()))
        self._config_entry_id = first_coordinator.config_entry.entry_id
        self._attr_unique_id = f"{self._config_entry_id}_api_calls"
        self._attr_name = "API Calls"
        self._last_value: int | None = None

    async def async_added_to_hass(self) -> None:
        """Restore state when entity is added."""
        await super().async_added_to_hass()
        if restored := await self.async_get_last_state():
            if restored.state not in (None, "unknown", "unavailable"):
                try:
                    self._last_value = int(restored.state)
                except (ValueError, TypeError):
                    pass

    @property
    def native_value(self) -> int:
        """Return the total number of API calls from all coordinators."""
        total = sum(coord.api_call_count for coord in self._coordinators.values())
        # Handle restoration - if the new total is less than restored, use restored
        if self._last_value is not None and total < self._last_value:
            total = self._last_value
        else:
            self._last_value = total
        return total

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return any(coord.last_update_success for coord in self._coordinators.values())

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        return {
            ring: coord.api_call_count for ring, coord in self._coordinators.items()
        }

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._config_entry_id)},
            name="AutoPi Integration",
            manufacturer=MANUFACTURER,
            configuration_url="https://app.autopi.io",
        )


class AutoPiFailedAPICallsSensor(RestoreEntity, SensorEntity):
    """Sensor showing the number of failed API calls across all coordinators."""

    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:alert-circle"
    _attr_has_entity_name = True

    def __init__(self, coordinators: dict[str, AutoPiDataUpdateCoordinator]) -> None:
        """Initialize the failed API calls sensor."""
        self._coordinators = coordinators
        first_coordinator = next(iter(coordinators.values()))
        self._config_entry_id = first_coordinator.config_entry.entry_id
        self._attr_unique_id = f"{self._config_entry_id}_failed_api_calls"
        self._attr_name = "Failed API Calls"
        self._last_value: int | None = None

    async def async_added_to_hass(self) -> None:
        """Restore state when entity is added."""
        await super().async_added_to_hass()
        if restored := await self.async_get_last_state():
            if restored.state not in (None, "unknown", "unavailable"):
                try:
                    self._last_value = int(restored.state)
                except (ValueError, TypeError):
                    pass

    @property
    def native_value(self) -> int:
        """Return the total number of failed API calls from all coordinators."""
        total = sum(
            coord.failed_api_call_count for coord in self._coordinators.values()
        )
        # Handle restoration - if the new total is less than restored, use restored
        if self._last_value is not None and total < self._last_value:
            total = self._last_value
        else:
            self._last_value = total
        return total

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return any(coord.last_update_success for coord in self._coordinators.values())

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        return {
            ring: coord.failed_api_call_count
            for ring, coord in self._coordinators.items()
        }

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._config_entry_id)},
            name="AutoPi Integration",
            manufacturer=MANUFACTURER,
            configuration_url="https://app.autopi.io",
        )


class AutoPiSuccessRateSensor(SensorEntity):
    """Sensor showing the API success rate across all coordinators."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "%"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:percent"
    _attr_has_entity_name = True

    def __init__(self, coordinators: dict[str, AutoPiDataUpdateCoordinator]) -> None:
        """Initialize the success rate sensor."""
        self._coordinators = coordinators
        first_coordinator = next(iter(coordinators.values()))
        self._config_entry_id = first_coordinator.config_entry.entry_id
        self._attr_unique_id = f"{self._config_entry_id}_api_success_rate"
        self._attr_name = "API Success Rate"

    @property
    def native_value(self) -> float:
        """Return the overall success rate from all coordinators."""
        total_calls = sum(coord.api_call_count for coord in self._coordinators.values())
        if total_calls == 0:
            return 100.0

        total_failed = sum(
            coord.failed_api_call_count for coord in self._coordinators.values()
        )
        success_rate = ((total_calls - total_failed) / total_calls) * 100
        return round(success_rate, 1)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return any(coord.last_update_success for coord in self._coordinators.values())

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        return {
            ring: round(coord.success_rate, 1)
            for ring, coord in self._coordinators.items()
        }

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._config_entry_id)},
            name="AutoPi Integration",
            manufacturer=MANUFACTURER,
            configuration_url="https://app.autopi.io",
        )


class AutoPiUpdateDurationSensor(SensorEntity):
    """Sensor showing the average duration of the last updates across all coordinators."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "s"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:timer"
    _attr_has_entity_name = True

    def __init__(self, coordinators: dict[str, AutoPiDataUpdateCoordinator]) -> None:
        """Initialize the update duration sensor."""
        self._coordinators = coordinators
        first_coordinator = next(iter(coordinators.values()))
        self._config_entry_id = first_coordinator.config_entry.entry_id
        self._attr_unique_id = f"{self._config_entry_id}_update_duration"
        self._attr_name = "Update Duration"

    @property
    def native_value(self) -> float | None:
        """Return the average update duration from all coordinators."""
        durations = [
            coord.last_update_duration
            for coord in self._coordinators.values()
            if coord.last_update_duration is not None
        ]

        if not durations:
            return None

        # Return the average duration
        avg_duration = sum(durations) / len(durations)
        return round(avg_duration, 3)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return any(coord.last_update_success for coord in self._coordinators.values())

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        attrs = {}
        for ring, coord in self._coordinators.items():
            if coord.last_update_duration is not None:
                attrs[f"{ring}_duration"] = round(coord.last_update_duration, 3)

        # Also include the most recent update time from any coordinator
        update_times = [
            coord.last_update_time
            for coord in self._coordinators.values()
            if hasattr(coord, "last_update_time") and coord.last_update_time
        ]

        if update_times:
            attrs["last_update"] = max(update_times)

        return attrs

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._config_entry_id)},
            name="AutoPi Integration",
            manufacturer=MANUFACTURER,
            configuration_url="https://app.autopi.io",
        )
