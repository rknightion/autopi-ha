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
    trip_coordinator: AutoPiDataUpdateCoordinator = data.get("trip_coordinator")
    all_coordinators = data["coordinators"]

    _LOGGER.debug(
        "Setting up AutoPi sensors for config entry %s", config_entry.entry_id
    )

    entities: list[SensorEntity] = []

    # Add vehicle count sensor
    entities.append(AutoPiVehicleCountSensor(coordinator))

    # Add fleet alert count sensor
    entities.append(AutoPiFleetAlertCountSensor(coordinator))

    # Add diagnostic sensors (these aggregate from all coordinators)
    # Use the fast coordinator for updates
    entities.append(AutoPiAPICallsSensor(coordinator, all_coordinators))
    entities.append(AutoPiFailedAPICallsSensor(coordinator, all_coordinators))
    entities.append(AutoPiSuccessRateSensor(coordinator, all_coordinators))
    entities.append(AutoPiUpdateDurationSensor(coordinator, all_coordinators))

    # Add individual vehicle sensors
    if coordinator.data:
        for vehicle_id, vehicle in coordinator.data.items():
            try:
                _LOGGER.debug(
                    "Creating vehicle sensor for %s (%s)", vehicle.name, vehicle_id
                )
                entities.append(AutoPiVehicleSensor(coordinator, vehicle_id))

                # Add data field sensors if available (includes position sensors)
                if (
                    position_coordinator.data
                    and vehicle_id in position_coordinator.data
                ):
                    vehicle_data = position_coordinator.data[vehicle_id]
                    if vehicle_data.data_fields:
                        available_fields = set(vehicle_data.data_fields.keys())
                        _LOGGER.debug(
                            "Found %d available data fields for vehicle %s",
                            len(available_fields),
                            vehicle.name,
                        )

                        # Create position sensors from data fields
                        try:
                            position_sensors = create_position_sensors(
                                position_coordinator, vehicle_id, available_fields
                            )
                            entities.extend(position_sensors)
                            _LOGGER.debug(
                                "Created %d position sensors for vehicle %s",
                                len(position_sensors),
                                vehicle.name,
                            )
                        except Exception as e:
                            _LOGGER.error(
                                "Failed to create position sensors for vehicle %s: %s",
                                vehicle.name,
                                str(e),
                                exc_info=True,
                            )

                        # Create other data field sensors
                        try:
                            data_field_sensors = create_data_field_sensors(
                                position_coordinator, vehicle_id, available_fields
                            )
                            entities.extend(data_field_sensors)
                            _LOGGER.debug(
                                "Created %d data field sensors for vehicle %s",
                                len(data_field_sensors),
                                vehicle.name,
                            )
                        except Exception as e:
                            _LOGGER.error(
                                "Failed to create data field sensors for vehicle %s: %s",
                                vehicle.name,
                                str(e),
                                exc_info=True,
                            )
                    else:
                        _LOGGER.debug(
                            "No data fields available for vehicle %s",
                            vehicle.name,
                        )
                else:
                    _LOGGER.debug(
                        "No position data available for vehicle %s",
                        vehicle.name,
                    )

            except Exception as e:
                _LOGGER.error(
                    "Failed to create sensors for vehicle %s: %s",
                    vehicle.name,
                    str(e),
                    exc_info=True,
                )

            # Add trip sensors if trip coordinator is available
            try:
                if (
                    trip_coordinator
                    and trip_coordinator.data
                    and vehicle_id in trip_coordinator.data
                ):
                    trip_vehicle = trip_coordinator.data[vehicle_id]
                    if trip_vehicle.trip_count > 0:
                        entities.append(
                            AutoPiTripCountSensor(trip_coordinator, vehicle_id)
                        )
                        entities.append(
                            AutoPiLastTripDistanceSensor(trip_coordinator, vehicle_id)
                        )
                        _LOGGER.debug(
                            "Created trip sensors for vehicle %s with %d trips",
                            vehicle.name,
                            trip_vehicle.trip_count,
                        )
                    else:
                        _LOGGER.debug(
                            "No trips found for vehicle %s",
                            vehicle.name,
                        )
            except Exception as e:
                _LOGGER.error(
                    "Failed to create trip sensors for vehicle %s: %s",
                    vehicle.name,
                    str(e),
                    exc_info=True,
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


class AutoPiFleetAlertCountSensor(AutoPiEntity, SensorEntity):
    """Sensor showing the total number of fleet alerts."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "alerts"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:alert"

    def __init__(self, coordinator: AutoPiDataUpdateCoordinator) -> None:
        """Initialize the fleet alert count sensor."""
        super().__init__(coordinator, "fleet_alert_count")
        self._attr_name = "Fleet Alert Count"

        _LOGGER.debug("Initialized AutoPi fleet alert count sensor")

    @property
    def native_value(self) -> int:
        """Return the number of fleet alerts."""
        return self.coordinator.fleet_alerts_total

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        attrs = dict(super().extra_state_attributes or {})

        # Group alerts by severity
        severity_counts: dict[str, int] = {}
        for alert in self.coordinator.fleet_alerts:
            severity_counts[alert.severity] = severity_counts.get(alert.severity, 0) + 1

        attrs["severities"] = severity_counts

        # Include individual alert details
        attrs["alerts"] = [
            {
                "title": alert.title,
                "severity": alert.severity,
                "vehicle_count": alert.vehicle_count,
                "id": alert.alert_id,
            }
            for alert in self.coordinator.fleet_alerts
        ]

        return attrs

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.config_entry.entry_id)},
            name="AutoPi Integration",
            manufacturer=MANUFACTURER,
            configuration_url="https://app.autopi.io",
        )


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


class AutoPiAPICallsSensor(AutoPiEntity, RestoreEntity, SensorEntity):
    """Sensor showing the total number of API calls across all coordinators."""

    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:api"
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: AutoPiDataUpdateCoordinator,
        coordinators: dict[str, AutoPiDataUpdateCoordinator],
    ) -> None:
        """Initialize the API calls sensor."""
        super().__init__(coordinator, "api_calls")
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


class AutoPiFailedAPICallsSensor(AutoPiEntity, RestoreEntity, SensorEntity):
    """Sensor showing the number of failed API calls across all coordinators."""

    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:alert-circle"
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: AutoPiDataUpdateCoordinator,
        coordinators: dict[str, AutoPiDataUpdateCoordinator],
    ) -> None:
        """Initialize the failed API calls sensor."""
        super().__init__(coordinator, "failed_api_calls")
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


class AutoPiSuccessRateSensor(AutoPiEntity, SensorEntity):
    """Sensor showing the API success rate across all coordinators."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "%"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:percent"
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: AutoPiDataUpdateCoordinator,
        coordinators: dict[str, AutoPiDataUpdateCoordinator],
    ) -> None:
        """Initialize the success rate sensor."""
        super().__init__(coordinator, "api_success_rate")
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


class AutoPiUpdateDurationSensor(AutoPiEntity, SensorEntity):
    """Sensor showing the average duration of the last updates across all coordinators."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "s"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:timer"
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: AutoPiDataUpdateCoordinator,
        coordinators: dict[str, AutoPiDataUpdateCoordinator],
    ) -> None:
        """Initialize the update duration sensor."""
        super().__init__(coordinator, "update_duration")
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


class AutoPiTripCountSensor(AutoPiVehicleEntity, SensorEntity):
    """Sensor showing the total number of trips for a vehicle."""

    _attr_state_class = SensorStateClass.TOTAL
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:map-marker-distance"
    _attr_native_unit_of_measurement = "trips"

    def __init__(
        self,
        coordinator: AutoPiDataUpdateCoordinator,
        vehicle_id: str,
    ) -> None:
        """Initialize the trip count sensor."""
        super().__init__(coordinator, vehicle_id, "trip_count")
        self._attr_name = "Trip Count"

        _LOGGER.debug("Initialized trip count sensor for vehicle %s", vehicle_id)

    @property
    def native_value(self) -> int | None:
        """Return the number of trips."""
        if vehicle := self.vehicle:
            return vehicle.trip_count
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        attrs = super().extra_state_attributes

        if vehicle := self.vehicle:
            if vehicle.last_trip:
                attrs["last_trip_id"] = vehicle.last_trip.trip_id
                attrs["last_trip_date"] = vehicle.last_trip.end_time.isoformat()
                attrs["last_trip_distance_km"] = vehicle.last_trip.distance_km
                attrs["last_trip_duration_minutes"] = (
                    vehicle.last_trip.duration_seconds // 60
                )

        return attrs


class AutoPiLastTripDistanceSensor(AutoPiVehicleEntity, SensorEntity):
    """Sensor showing the distance of the last trip."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "km"
    _attr_icon = "mdi:road-variant"

    def __init__(
        self,
        coordinator: AutoPiDataUpdateCoordinator,
        vehicle_id: str,
    ) -> None:
        """Initialize the last trip distance sensor."""
        super().__init__(coordinator, vehicle_id, "last_trip_distance")
        self._attr_name = "Last Trip Distance"

        _LOGGER.debug(
            "Initialized last trip distance sensor for vehicle %s", vehicle_id
        )

    @property
    def native_value(self) -> float | None:
        """Return the distance of the last trip."""
        if vehicle := self.vehicle:
            if vehicle.last_trip:
                return round(vehicle.last_trip.distance_km, 1)
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        attrs = super().extra_state_attributes

        if vehicle := self.vehicle:
            if vehicle.last_trip:
                trip = vehicle.last_trip
                attrs.update(
                    {
                        "trip_id": trip.trip_id,
                        "start_time": trip.start_time.isoformat(),
                        "end_time": trip.end_time.isoformat(),
                        "duration_minutes": trip.duration_seconds // 60,
                        "start_location": {
                            "latitude": trip.start_lat,
                            "longitude": trip.start_lng,
                            "address": trip.start_address,
                        },
                        "end_location": {
                            "latitude": trip.end_lat,
                            "longitude": trip.end_lng,
                            "address": trip.end_address,
                        },
                        "state": trip.state,
                    }
                )

        return attrs
