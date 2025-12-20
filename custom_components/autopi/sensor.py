"""Support for AutoPi sensors."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, UnitOfLength, UnitOfSpeed, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

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

    # Add fleet vehicle summary sensors
    entities.extend(
        [
            AutoPiFleetVehicleSummarySensor(
                coordinator,
                "all_vehicles",
                "Fleet Vehicles",
                icon="mdi:car-multiple",
            ),
            AutoPiFleetVehicleSummarySensor(
                coordinator,
                "active_now",
                "Fleet Active Now",
                icon="mdi:car-connected",
            ),
            AutoPiFleetVehicleSummarySensor(
                coordinator,
                "driven_last_30_days",
                "Fleet Driven Last 30 Days",
                icon="mdi:calendar-range",
            ),
            AutoPiFleetVehicleSummarySensor(
                coordinator,
                "on_location",
                "Fleet On Location",
                icon="mdi:map-marker",
            ),
        ]
    )

    # Add diagnostic sensors (these aggregate from all coordinators)
    # Use the fast coordinator for updates
    entities.append(AutoPiUpdateDurationSensor(coordinator, all_coordinators))

    # Add individual vehicle sensors
    if coordinator.data:
        for vehicle_id, vehicle in coordinator.data.items():
            try:
                _LOGGER.debug(
                    "Creating vehicle sensor for %s (%s)", vehicle.name, vehicle_id
                )
                entities.append(AutoPiVehicleSensor(coordinator, vehicle_id))
                entities.append(AutoPiVehicleAlertCountSensor(coordinator, vehicle_id))
                entities.append(AutoPiVehicleDtcCountSensor(coordinator, vehicle_id))
                entities.append(AutoPiVehicleLastDtcSensor(coordinator, vehicle_id))
                entities.append(AutoPiGeofenceCountSensor(coordinator, vehicle_id))
                entities.append(AutoPiLocationCountSensor(coordinator, vehicle_id))
                entities.append(AutoPiLastChargeDurationSensor(coordinator, vehicle_id))

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
                        except (AttributeError, ValueError, TypeError):
                            _LOGGER.exception(
                                "Failed to create position sensors for vehicle %s",
                                vehicle.name,
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
                        except (AttributeError, ValueError, TypeError):
                            _LOGGER.exception(
                                "Failed to create data field sensors for vehicle %s",
                                vehicle.name,
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

                # Add last communication sensor (position coordinator)
                entities.append(
                    AutoPiLastCommunicationSensor(position_coordinator, vehicle_id)
                )

                # Add event volume sensors
                entities.extend(
                    [
                        AutoPiEventVolumeSensor(
                            coordinator,
                            vehicle_id,
                            "harsh",
                            "24h",
                            "Harsh Events (24h)",
                            icon="mdi:car-brake-alert",
                        ),
                        AutoPiEventVolumeSensor(
                            coordinator,
                            vehicle_id,
                            "harsh",
                            "7d",
                            "Harsh Events (7d)",
                            icon="mdi:car-brake-alert",
                        ),
                        AutoPiEventVolumeSensor(
                            coordinator,
                            vehicle_id,
                            "speeding",
                            "24h",
                            "Speeding Events (24h)",
                            icon="mdi:speedometer",
                        ),
                        AutoPiEventVolumeSensor(
                            coordinator,
                            vehicle_id,
                            "speeding",
                            "7d",
                            "Speeding Events (7d)",
                            icon="mdi:speedometer",
                        ),
                    ]
                )

            except (AttributeError, ValueError, TypeError):
                _LOGGER.exception(
                    "Failed to create sensors for vehicle %s",
                    vehicle.name,
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
                        entities.append(
                            AutoPiTripLifetimeDistanceSensor(
                                trip_coordinator, vehicle_id
                            )
                        )
                        entities.append(
                            AutoPiTripAverageSpeedSensor(
                                trip_coordinator, vehicle_id
                            )
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
            except (AttributeError, ValueError, TypeError):
                _LOGGER.exception(
                    "Failed to create trip sensors for vehicle %s",
                    vehicle.name,
                )

    _LOGGER.debug("Adding %d AutoPi sensor entities", len(entities))

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
            return {"auto_zero_enabled": False}

        return {
            "vehicles": [
                {
                    "id": vehicle.id,
                    "name": vehicle.name,
                    "license_plate": vehicle.license_plate,
                }
                for vehicle in self.coordinator.data.values()
            ],
            "auto_zero_enabled": False,
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

        attrs["auto_zero_enabled"] = False
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


class AutoPiFleetVehicleSummarySensor(AutoPiEntity, SensorEntity):
    """Sensor showing fleet vehicle activity summary."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "vehicles"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: AutoPiDataUpdateCoordinator,
        metric: str,
        name: str,
        icon: str,
    ) -> None:
        """Initialize the fleet summary sensor."""
        super().__init__(coordinator, f"fleet_vehicle_{metric}")
        self._metric = metric
        self._attr_name = name
        self._attr_icon = icon

    @property
    def native_value(self) -> int | None:
        """Return the metric value."""
        summary = self.coordinator.get_fleet_vehicle_summary()
        if summary is None:
            return None
        return int(getattr(summary, self._metric, 0))

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
                    "auto_zero_enabled": False,
                }
            )

        return attrs


class AutoPiVehicleAlertCountSensor(AutoPiVehicleEntity, SensorEntity):
    """Sensor showing open alerts for a vehicle."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "alerts"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:alert"

    def __init__(
        self,
        coordinator: AutoPiDataUpdateCoordinator,
        vehicle_id: str,
    ) -> None:
        """Initialize the vehicle alert sensor."""
        super().__init__(coordinator, vehicle_id, "vehicle_alerts")
        self._attr_name = "Alerts"

    @property
    def native_value(self) -> int | None:
        """Return alert count."""
        return self.coordinator.get_vehicle_alert_count(self._vehicle_id)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        attrs = super().extra_state_attributes
        summary = self.coordinator.get_vehicle_alert_summary(self._vehicle_id)
        attrs["severity_counts"] = summary.get("severity_counts", {})
        attrs["alerts"] = summary.get("alerts", [])
        return attrs


class AutoPiVehicleDtcCountSensor(AutoPiVehicleEntity, SensorEntity):
    """Sensor showing DTC count for a vehicle."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "codes"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:alert-circle"

    def __init__(
        self,
        coordinator: AutoPiDataUpdateCoordinator,
        vehicle_id: str,
    ) -> None:
        """Initialize the DTC count sensor."""
        super().__init__(coordinator, vehicle_id, "dtc_count")
        self._attr_name = "DTC Count"

    @property
    def native_value(self) -> int | None:
        """Return DTC count."""
        return self.coordinator.get_vehicle_dtc_count(self._vehicle_id)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        attrs = super().extra_state_attributes
        last_dtc = self.coordinator.get_vehicle_last_dtc(self._vehicle_id)
        if last_dtc:
            attrs["last_dtc_code"] = last_dtc.code
            attrs["last_dtc_description"] = last_dtc.description
            attrs["last_dtc_occurred_at"] = (
                last_dtc.occurred_at.isoformat() if last_dtc.occurred_at else None
            )
        return attrs


class AutoPiVehicleLastDtcSensor(AutoPiVehicleEntity, SensorEntity):
    """Sensor showing last DTC code."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:car-wrench"

    def __init__(
        self,
        coordinator: AutoPiDataUpdateCoordinator,
        vehicle_id: str,
    ) -> None:
        """Initialize the last DTC sensor."""
        super().__init__(coordinator, vehicle_id, "last_dtc")
        self._attr_name = "Last DTC"

    @property
    def native_value(self) -> str | None:
        """Return last DTC code."""
        last_dtc = self.coordinator.get_vehicle_last_dtc(self._vehicle_id)
        return last_dtc.code if last_dtc else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        attrs = super().extra_state_attributes
        last_dtc = self.coordinator.get_vehicle_last_dtc(self._vehicle_id)
        if last_dtc:
            attrs["description"] = last_dtc.description
            attrs["occurred_at"] = (
                last_dtc.occurred_at.isoformat() if last_dtc.occurred_at else None
            )
        return attrs


class AutoPiGeofenceCountSensor(AutoPiVehicleEntity, SensorEntity):
    """Sensor showing geofence count for a vehicle."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "geofences"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:map-marker"

    def __init__(
        self,
        coordinator: AutoPiDataUpdateCoordinator,
        vehicle_id: str,
    ) -> None:
        """Initialize the geofence count sensor."""
        super().__init__(coordinator, vehicle_id, "geofence_count")
        self._attr_name = "Geofence Count"

    @property
    def native_value(self) -> int | None:
        """Return geofence count."""
        summary = self.coordinator.get_geofence_summary(self._vehicle_id)
        return summary.geofence_count if summary else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        attrs = super().extra_state_attributes
        summary = self.coordinator.get_geofence_summary(self._vehicle_id)
        if summary:
            attrs["last_entered"] = (
                summary.last_entered.isoformat() if summary.last_entered else None
            )
            attrs["last_exited"] = (
                summary.last_exited.isoformat() if summary.last_exited else None
            )
        return attrs


class AutoPiLocationCountSensor(AutoPiVehicleEntity, SensorEntity):
    """Sensor showing location count for a vehicle."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "locations"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:map-marker-radius"

    def __init__(
        self,
        coordinator: AutoPiDataUpdateCoordinator,
        vehicle_id: str,
    ) -> None:
        """Initialize the location count sensor."""
        super().__init__(coordinator, vehicle_id, "location_count")
        self._attr_name = "Location Count"

    @property
    def native_value(self) -> int | None:
        """Return location count."""
        summary = self.coordinator.get_geofence_summary(self._vehicle_id)
        return summary.location_count if summary else None


class AutoPiLastCommunicationSensor(AutoPiVehicleEntity, SensorEntity):
    """Sensor showing last communication timestamp."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:clock"

    def __init__(
        self,
        coordinator: AutoPiDataUpdateCoordinator,
        vehicle_id: str,
    ) -> None:
        """Initialize the last communication sensor."""
        super().__init__(coordinator, vehicle_id, "last_communication")
        self._attr_name = "Last Communication"

    @property
    def native_value(self) -> datetime | None:
        """Return last communication timestamp."""
        return self.coordinator.get_last_communication(self._vehicle_id)


class AutoPiLastChargeDurationSensor(AutoPiVehicleEntity, SensorEntity):
    """Sensor showing duration of the last charge session."""

    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.SECONDS
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:timer"

    def __init__(
        self,
        coordinator: AutoPiDataUpdateCoordinator,
        vehicle_id: str,
    ) -> None:
        """Initialize the last charge duration sensor."""
        super().__init__(coordinator, vehicle_id, "last_charge_duration")
        self._attr_name = "Last Charge Duration"

    @property
    def native_value(self) -> int | None:
        """Return last charge duration in seconds."""
        info = self.coordinator.get_vehicle_charging_info(self._vehicle_id)
        return info.get("last_charge_duration_seconds")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        attrs = super().extra_state_attributes
        attrs.update(self.coordinator.get_vehicle_charging_info(self._vehicle_id))
        return attrs


class AutoPiEventVolumeSensor(AutoPiVehicleEntity, SensorEntity):
    """Sensor showing event volume for a tag and window."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "events"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: AutoPiDataUpdateCoordinator,
        vehicle_id: str,
        tag: str,
        window: str,
        name: str,
        icon: str,
    ) -> None:
        """Initialize the event volume sensor."""
        super().__init__(coordinator, vehicle_id, f"event_volume_{tag}_{window}")
        self._tag = tag
        self._window = window
        self._attr_name = name
        self._attr_icon = icon

    @property
    def native_value(self) -> int | None:
        """Return event volume."""
        return self.coordinator.get_event_volume(
            self._vehicle_id, self._tag, self._window
        )


class AutoPiUpdateDurationSensor(AutoPiEntity, SensorEntity):
    """Sensor showing the average duration of the last updates across all coordinators."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "s"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:timer"
    _attr_has_entity_name = True
    _attr_should_poll = False

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

    async def async_added_to_hass(self) -> None:
        """Handle entity being added to Home Assistant."""
        await super().async_added_to_hass()

        # Add listeners to all coordinators
        for _coord_name, coord in self._coordinators.items():
            if coord != self.coordinator:  # Already listening to primary coordinator
                self.async_on_remove(
                    coord.async_add_listener(self._handle_coordinator_update)
                )

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

        attrs["auto_zero_enabled"] = False
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

        attrs["auto_zero_enabled"] = False
        return attrs


class AutoPiLastTripDistanceSensor(AutoPiVehicleEntity, SensorEntity):
    """Sensor showing the distance of the last trip."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_native_unit_of_measurement = UnitOfLength.KILOMETERS
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

        attrs["auto_zero_enabled"] = False
        return attrs


class AutoPiTripLifetimeDistanceSensor(AutoPiVehicleEntity, SensorEntity):
    """Sensor showing total lifetime trip distance."""

    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_native_unit_of_measurement = UnitOfLength.KILOMETERS
    _attr_icon = "mdi:road-variant"

    def __init__(
        self,
        coordinator: AutoPiDataUpdateCoordinator,
        vehicle_id: str,
    ) -> None:
        """Initialize the lifetime distance sensor."""
        super().__init__(coordinator, vehicle_id, "trip_distance_total")
        self._attr_name = "Trip Distance Total"

    @property
    def native_value(self) -> float | None:
        """Return the total trip distance."""
        if vehicle := self.vehicle:
            return round(vehicle.total_distance_km, 1)
        return None


class AutoPiTripAverageSpeedSensor(AutoPiVehicleEntity, SensorEntity):
    """Sensor showing average trip speed."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_device_class = SensorDeviceClass.SPEED
    _attr_native_unit_of_measurement = UnitOfSpeed.KILOMETERS_PER_HOUR
    _attr_icon = "mdi:speedometer"

    def __init__(
        self,
        coordinator: AutoPiDataUpdateCoordinator,
        vehicle_id: str,
    ) -> None:
        """Initialize the average speed sensor."""
        super().__init__(coordinator, vehicle_id, "trip_speed_average")
        self._attr_name = "Trip Speed Average"

    @property
    def native_value(self) -> float | None:
        """Return the average trip speed."""
        if vehicle := self.vehicle:
            return (
                round(vehicle.average_speed_kmh, 2)
                if vehicle.average_speed_kmh is not None
                else None
            )
        return None
