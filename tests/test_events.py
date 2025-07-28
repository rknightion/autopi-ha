"""Tests for AutoPi event entities."""

from datetime import datetime
from unittest.mock import MagicMock

import pytest
from homeassistant.core import HomeAssistant

from custom_components.autopi.event import AutoPiVehicleEvent
from custom_components.autopi.types import AutoPiEvent, AutoPiVehicle


@pytest.fixture
def mock_vehicle():
    """Create a mock vehicle."""
    return AutoPiVehicle(
        id=123,
        name="Test Vehicle",
        license_plate="ABC123",
        vin="1234567890",
        year=2022,
        type="ICE",
        battery_voltage=12,
        devices=["device1", "device2"],
        make_id=1,
        model_id=2,
    )


@pytest.fixture
def mock_coordinator(mock_vehicle):
    """Create a mock coordinator."""
    coordinator = MagicMock()
    coordinator.data = {"123": mock_vehicle}
    coordinator.get_device_events = MagicMock(return_value=[])
    return coordinator


@pytest.fixture
def mock_event():
    """Create a mock event."""
    return AutoPiEvent(
        timestamp=datetime.now(),
        tag="vehicle/battery/charging",
        area="vehicle/battery",
        event_type="charging",
        data={"event.vehicle.battery.level": 95},
        device_id="device1",
    )


async def test_event_entity_init(mock_coordinator, mock_vehicle):
    """Test event entity initialization."""
    event_entity = AutoPiVehicleEvent(mock_coordinator, "123")

    assert event_entity.vehicle == mock_vehicle
    assert event_entity._device_ids == ["device1", "device2"]
    assert event_entity.name == "Events"
    assert event_entity.available is True
    assert "charging" in event_entity._attr_event_types


async def test_event_entity_unavailable(mock_coordinator):
    """Test event entity when vehicle is unavailable."""
    mock_coordinator.data = {}
    event_entity = AutoPiVehicleEvent(mock_coordinator, "123")

    assert event_entity.vehicle is None
    assert event_entity._device_ids == []
    assert event_entity.available is False


async def test_event_entity_attributes(mock_coordinator, mock_vehicle, mock_event):
    """Test event entity attributes."""
    # Return event only for device1, empty for device2
    def get_device_events(device_id):
        if device_id == "device1":
            return [mock_event]
        return []

    mock_coordinator.get_device_events.side_effect = get_device_events

    event_entity = AutoPiVehicleEvent(mock_coordinator, "123")
    attrs = event_entity.extra_state_attributes

    assert "recent_events" in attrs
    assert len(attrs["recent_events"]) == 1
    assert attrs["recent_events"][0]["device_id"] == "device1"
    assert attrs["recent_events"][0]["area"] == "vehicle/battery"
    assert attrs["recent_events"][0]["event"] == "charging"


async def test_event_entity_event_handling(hass: HomeAssistant, mock_coordinator, mock_vehicle):
    """Test event entity handles device events."""
    event_entity = AutoPiVehicleEvent(mock_coordinator, "123")
    event_entity.hass = hass
    event_entity._trigger_event = MagicMock()
    event_entity.async_write_ha_state = MagicMock()

    await event_entity.async_added_to_hass()

    # Simulate a device event
    event_data = {
        "device_id": "device1",
        "vehicle_id": "123",
        "timestamp": datetime.now().isoformat(),
        "tag": "vehicle/battery/charging",
        "area": "vehicle/battery",
        "event_type": "charging",
        "data": {"event.vehicle.battery.level": 95},
    }

    # Fire the event
    hass.bus.async_fire("autopi_device_event", event_data)
    await hass.async_block_till_done()

    # Check that the event was triggered
    event_entity._trigger_event.assert_called_once_with(
        "charging",
        {
            "device_id": "device1",
            "timestamp": event_data["timestamp"],
            "tag": "vehicle/battery/charging",
            "area": "vehicle/battery",
            "data": {"event.vehicle.battery.level": 95},
            "original_event_type": "charging",
        }
    )
    event_entity.async_write_ha_state.assert_called_once()


async def test_event_entity_ignores_other_vehicles(hass: HomeAssistant, mock_coordinator, mock_vehicle):
    """Test event entity ignores events from other vehicles."""
    event_entity = AutoPiVehicleEvent(mock_coordinator, "123")
    event_entity.hass = hass
    event_entity._trigger_event = MagicMock()

    await event_entity.async_added_to_hass()

    # Simulate a device event from a different vehicle
    event_data = {
        "device_id": "device3",
        "vehicle_id": "456",  # Different vehicle
        "timestamp": datetime.now().isoformat(),
        "tag": "vehicle/battery/charging",
        "area": "vehicle/battery",
        "event_type": "charging",
        "data": {},
    }

    # Fire the event
    hass.bus.async_fire("autopi_device_event", event_data)
    await hass.async_block_till_done()

    # Check that the event was NOT triggered
    event_entity._trigger_event.assert_not_called()


async def test_event_entity_unknown_event_type(hass: HomeAssistant, mock_coordinator, mock_vehicle, caplog):
    """Test event entity handles unknown event types."""
    event_entity = AutoPiVehicleEvent(mock_coordinator, "123")
    event_entity.hass = hass
    event_entity._trigger_event = MagicMock()
    event_entity.async_write_ha_state = MagicMock()

    await event_entity.async_added_to_hass()

    # Simulate a device event with unknown type
    event_data = {
        "device_id": "device1",
        "vehicle_id": "123",
        "timestamp": datetime.now().isoformat(),
        "tag": "vehicle/new_feature/action",
        "area": "vehicle/new_feature",
        "event_type": "some_new_event_type",
        "data": {"custom": "data"},
    }

    # Fire the event
    hass.bus.async_fire("autopi_device_event", event_data)
    await hass.async_block_till_done()

    # Check that the event was triggered with "unknown" type
    event_entity._trigger_event.assert_called_once_with(
        "unknown",
        {
            "device_id": "device1",
            "timestamp": event_data["timestamp"],
            "tag": "vehicle/new_feature/action",
            "area": "vehicle/new_feature",
            "data": {"custom": "data"},
            "original_event_type": "some_new_event_type",
        }
    )
    event_entity.async_write_ha_state.assert_called_once()

    # Check that a warning was logged
    assert "Unknown event type 'some_new_event_type'" in caplog.text
