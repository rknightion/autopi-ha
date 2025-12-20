"""Support for AutoPi binary sensors."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DATA_FIELD_TIMEOUT_MINUTES, DOMAIN
from .coordinator import AutoPiDataUpdateCoordinator
from .entities.base import AutoPiVehicleEntity
from .types import DataFieldValue

_LOGGER = logging.getLogger(__name__)


class AutoPiDataFieldBinarySensor(AutoPiVehicleEntity, BinarySensorEntity):
    """Base class for data field derived binary sensors."""

    def __init__(
        self,
        coordinator: AutoPiDataUpdateCoordinator,
        vehicle_id: str,
        field_id: str,
        name: str,
        device_class: BinarySensorDeviceClass | None = None,
        icon: str | None = None,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(
            coordinator, vehicle_id, f"data_field_{field_id.replace('.', '_')}_binary"
        )
        self._field_id = field_id
        self._attr_name = name
        self._attr_device_class = device_class
        self._attr_icon = icon
        self._last_known_value: bool | None = None
        self._last_update_time: datetime | None = None

    def _get_field_data(self) -> DataFieldValue | None:
        """Return data field value."""
        if (
            not self.vehicle
            or not hasattr(self.vehicle, "data_fields")
            or self.vehicle.data_fields is None
        ):
            return None
        return self.vehicle.data_fields.get(self._field_id)

    def _cache_value(self, value: bool, field_data: DataFieldValue) -> bool:
        """Cache value and update timestamps."""
        self._last_known_value = value
        self._last_update_time = field_data.last_update
        return value

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        if not super().available:
            return False

        field_data = self._get_field_data()
        if field_data is not None:
            return True

        if self._last_known_value is not None and self._last_update_time is not None:
            return datetime.now(UTC) - self._last_update_time < timedelta(
                minutes=DATA_FIELD_TIMEOUT_MINUTES
            )

        return False

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        attrs = super().extra_state_attributes
        field_data = self._get_field_data()
        if field_data is not None:
            attrs["field_id"] = field_data.field_id
            attrs["last_seen"] = field_data.last_seen.isoformat()
        return attrs


class BatteryChargingStateBinarySensor(AutoPiDataFieldBinarySensor):
    """Battery charging binary sensor."""

    def __init__(
        self, coordinator: AutoPiDataUpdateCoordinator, vehicle_id: str
    ) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator,
            vehicle_id,
            "obd.bat.state",
            "Battery Charging",
            device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
            icon="mdi:battery-charging",
        )

    @property
    def is_on(self) -> bool | None:
        """Return true if battery is charging."""
        field_data = self._get_field_data()
        if field_data is None:
            return self._last_known_value

        value = field_data.last_value
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"charging", "fast_charging", "slow_charging"}:
                return self._cache_value(True, field_data)
            if normalized in {"discharging", "idle", "not_charging", "unknown"}:
                return self._cache_value(False, field_data)
            return None

        if isinstance(value, (int, float)):
            return self._cache_value(value > 0, field_data)

        if isinstance(value, bool):
            return self._cache_value(value, field_data)

        return None


class IgnitionRunningBinarySensor(AutoPiDataFieldBinarySensor):
    """Ignition/engine running binary sensor."""

    def __init__(
        self, coordinator: AutoPiDataUpdateCoordinator, vehicle_id: str
    ) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator,
            vehicle_id,
            "std.ignition.value",
            "Ignition Running",
            device_class=BinarySensorDeviceClass.RUNNING,
            icon="mdi:key",
        )

    @property
    def is_on(self) -> bool | None:
        """Return true if ignition is on."""
        field_data = self._get_field_data()
        if field_data is None:
            return self._last_known_value

        value = field_data.last_value
        if isinstance(value, (int, float)):
            return self._cache_value(value > 0, field_data)
        if isinstance(value, bool):
            return self._cache_value(value, field_data)
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"on", "true", "running"}:
                return self._cache_value(True, field_data)
            if normalized in {"off", "false", "stopped"}:
                return self._cache_value(False, field_data)
        return None


class MovementBinarySensor(AutoPiVehicleEntity, BinarySensorEntity):
    """Vehicle movement binary sensor."""

    _attr_device_class = BinarySensorDeviceClass.MOVING

    def __init__(
        self, coordinator: AutoPiDataUpdateCoordinator, vehicle_id: str
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, vehicle_id, "movement")
        self._attr_name = "Moving"
        self._attr_icon = "mdi:car-traction-control"

    @property
    def is_on(self) -> bool | None:
        """Return true if vehicle is moving."""
        movement = self.coordinator.get_vehicle_movement(self._vehicle_id)
        if movement is not None:
            return movement
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        attrs = super().extra_state_attributes
        movement_info = self.coordinator.get_vehicle_movement_info(self._vehicle_id)
        if movement_info:
            attrs.update(movement_info)
        return attrs


class ChargingInProgressBinarySensor(AutoPiVehicleEntity, BinarySensorEntity):
    """Charging in progress binary sensor."""

    _attr_device_class = BinarySensorDeviceClass.BATTERY_CHARGING

    def __init__(
        self, coordinator: AutoPiDataUpdateCoordinator, vehicle_id: str
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, vehicle_id, "charging_in_progress")
        self._attr_name = "Charging In Progress"
        self._attr_icon = "mdi:battery-charging"

    @property
    def is_on(self) -> bool | None:
        """Return true if charging is in progress."""
        return self.coordinator.get_vehicle_charging_state(self._vehicle_id)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        attrs = super().extra_state_attributes
        attrs.update(self.coordinator.get_vehicle_charging_info(self._vehicle_id))
        return attrs


class TrackerOnlineBinarySensor(AutoPiVehicleEntity, BinarySensorEntity):
    """Tracker online/offline binary sensor."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(
        self, coordinator: AutoPiDataUpdateCoordinator, vehicle_id: str
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, vehicle_id, "tracker_online")
        self._attr_name = "Tracker Online"
        self._attr_icon = "mdi:access-point"

    @property
    def is_on(self) -> bool | None:
        """Return true if tracker is online."""
        last_comm = self.coordinator.get_last_communication(self._vehicle_id)
        if last_comm is None:
            return None
        threshold = self.coordinator.get_online_threshold()
        return datetime.now(UTC) - last_comm <= threshold

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        attrs = super().extra_state_attributes
        last_comm = self.coordinator.get_last_communication(self._vehicle_id)
        if last_comm is not None:
            attrs["last_communication"] = last_comm.isoformat()
            attrs["last_seen_seconds"] = int(
                (datetime.now(UTC) - last_comm).total_seconds()
            )
        attrs["online_threshold_seconds"] = int(
            self.coordinator.get_online_threshold().total_seconds()
        )
        return attrs


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up AutoPi binary sensors from a config entry."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    coordinator: AutoPiDataUpdateCoordinator = data["coordinator"]
    position_coordinator: AutoPiDataUpdateCoordinator = data["position_coordinator"]

    entities: list[BinarySensorEntity] = []

    vehicle_ids = set(coordinator.data or {})

    for vehicle_id in vehicle_ids:
        # Movement and online sensors use position coordinator data
        entities.append(MovementBinarySensor(position_coordinator, vehicle_id))
        entities.append(TrackerOnlineBinarySensor(position_coordinator, vehicle_id))

        # Charging state sensors use base coordinator data
        entities.append(ChargingInProgressBinarySensor(coordinator, vehicle_id))

        # Data field derived binary sensors
        if (
            position_coordinator.data
            and vehicle_id in position_coordinator.data
            and position_coordinator.data[vehicle_id].data_fields
        ):
            available_fields = set(
                position_coordinator.data[vehicle_id].data_fields.keys()
            )

            if "obd.bat.state" in available_fields:
                entities.append(
                    BatteryChargingStateBinarySensor(
                        position_coordinator, vehicle_id
                    )
                )
            if "std.ignition.value" in available_fields:
                entities.append(
                    IgnitionRunningBinarySensor(
                        position_coordinator, vehicle_id
                    )
                )

    _LOGGER.debug("Adding %d AutoPi binary sensor entities", len(entities))
    async_add_entities(entities)
