"""Comprehensive tests for AutoPi sensor platform."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.autopi.const import DOMAIN
from custom_components.autopi.sensor import (
    AutoPiFleetAlertCountSensor,
    AutoPiLastTripDistanceSensor,
    AutoPiTripCountSensor,
    AutoPiUpdateDurationSensor,
    AutoPiVehicleCountSensor,
    AutoPiVehicleSensor,
    async_setup_entry,
)
from custom_components.autopi.types import (
    AutoPiTrip,
    AutoPiVehicle,
    DataFieldValue,
    FleetAlert,
)


class TestAutopiVehicleCountSensor:
    """Test the vehicle count sensor."""

    async def test_vehicle_count_sensor_init(self, mock_coordinator):
        """Test vehicle count sensor initialization."""
        sensor = AutoPiVehicleCountSensor(mock_coordinator)

        assert sensor.name == "Vehicle Count"
        assert sensor.native_unit_of_measurement == "vehicles"
        assert sensor.icon == "mdi:car-multiple"

    async def test_vehicle_count_with_vehicles(self, mock_coordinator, mock_vehicle, mock_vehicle_2):
        """Test vehicle count with multiple vehicles."""
        mock_coordinator.data = {
            str(mock_vehicle.id): mock_vehicle,
            str(mock_vehicle_2.id): mock_vehicle_2,
        }
        mock_coordinator.get_vehicle_count = Mock(return_value=2)

        sensor = AutoPiVehicleCountSensor(mock_coordinator)

        assert sensor.native_value == 2

    async def test_vehicle_count_zero_vehicles(self, mock_coordinator):
        """Test vehicle count with no vehicles."""
        mock_coordinator.data = {}
        mock_coordinator.get_vehicle_count = Mock(return_value=0)

        sensor = AutoPiVehicleCountSensor(mock_coordinator)

        assert sensor.native_value == 0

    async def test_vehicle_count_extra_attributes(self, mock_coordinator, mock_vehicle):
        """Test vehicle count sensor extra attributes."""
        mock_coordinator.data = {str(mock_vehicle.id): mock_vehicle}

        sensor = AutoPiVehicleCountSensor(mock_coordinator)
        attrs = sensor.extra_state_attributes

        assert "vehicles" in attrs
        assert len(attrs["vehicles"]) == 1
        assert attrs["vehicles"][0]["id"] == mock_vehicle.id
        assert attrs["vehicles"][0]["name"] == mock_vehicle.name
        assert attrs["vehicles"][0]["license_plate"] == mock_vehicle.license_plate


class TestAutopiFleetAlertCountSensor:
    """Test the fleet alert count sensor."""

    async def test_fleet_alert_count_init(self, mock_coordinator):
        """Test fleet alert count sensor initialization."""
        sensor = AutoPiFleetAlertCountSensor(mock_coordinator)

        assert sensor.name == "Fleet Alert Count"
        assert sensor.native_unit_of_measurement == "alerts"
        assert sensor.icon == "mdi:alert"

    async def test_fleet_alert_count_with_alerts(self, mock_coordinator):
        """Test fleet alert count with active alerts."""
        mock_coordinator._fleet_alerts_total = 3
        mock_coordinator._fleet_alerts = [
            FleetAlert(
                alert_id="alert1",
                title="Test alert 1",
                severity="high",
                vehicle_count=1,
            ),
            FleetAlert(
                alert_id="alert2",
                title="Test alert 2",
                severity="medium",
                vehicle_count=1,
            ),
            FleetAlert(
                alert_id="alert3",
                title="Test alert 3",
                severity="low",
                vehicle_count=2,
            ),
        ]

        sensor = AutoPiFleetAlertCountSensor(mock_coordinator)

        assert sensor.native_value == 3

    async def test_fleet_alert_count_no_alerts(self, mock_coordinator):
        """Test fleet alert count with no alerts."""
        mock_coordinator._fleet_alerts_total = 0
        mock_coordinator._fleet_alerts = []

        sensor = AutoPiFleetAlertCountSensor(mock_coordinator)

        assert sensor.native_value == 0

    async def test_fleet_alert_extra_attributes(self, mock_coordinator):
        """Test fleet alert sensor extra attributes."""
        mock_coordinator._fleet_alerts_total = 2
        mock_coordinator._fleet_alerts = [
            FleetAlert(
                alert_id="alert1",
                title="Battery low",
                severity="high",
                vehicle_count=1,
            ),
            FleetAlert(
                alert_id="alert2",
                title="Service due",
                severity="medium",
                vehicle_count=1,
            ),
        ]

        sensor = AutoPiFleetAlertCountSensor(mock_coordinator)
        attrs = sensor.extra_state_attributes

        assert "severities" in attrs
        assert attrs["severities"]["high"] == 1
        assert attrs["severities"]["medium"] == 1
        assert "alerts" in attrs
        assert len(attrs["alerts"]) == 2


class TestAutopiVehicleSensor:
    """Test the individual vehicle sensor."""

    async def test_vehicle_sensor_init(self, mock_coordinator, mock_vehicle):
        """Test vehicle sensor initialization."""
        mock_coordinator.data = {str(mock_vehicle.id): mock_vehicle}

        sensor = AutoPiVehicleSensor(mock_coordinator, str(mock_vehicle.id))

        assert sensor.name == "Status"
        assert sensor.vehicle == mock_vehicle

    async def test_vehicle_sensor_state(self, mock_coordinator, mock_vehicle):
        """Test vehicle sensor state."""
        mock_coordinator.data = {str(mock_vehicle.id): mock_vehicle}

        sensor = AutoPiVehicleSensor(mock_coordinator, str(mock_vehicle.id))

        assert sensor.native_value == mock_vehicle.license_plate

    async def test_vehicle_sensor_extra_attributes(self, mock_coordinator, mock_vehicle):
        """Test vehicle sensor extra attributes."""
        mock_coordinator.data = {str(mock_vehicle.id): mock_vehicle}

        sensor = AutoPiVehicleSensor(mock_coordinator, str(mock_vehicle.id))
        attrs = sensor.extra_state_attributes

        assert attrs["vehicle_id"] == mock_vehicle.id
        assert attrs["name"] == mock_vehicle.name
        assert attrs["license_plate"] == mock_vehicle.license_plate
        assert attrs["vin"] == mock_vehicle.vin
        assert attrs["year"] == mock_vehicle.year
        assert attrs["type"] == mock_vehicle.type


class TestAutopiUpdateDurationSensor:
    """Test the update duration sensor."""

    async def test_update_duration_sensor_init(self, mock_coordinator):
        """Test update duration sensor initialization."""
        all_coordinators = {"coordinator": mock_coordinator}

        sensor = AutoPiUpdateDurationSensor(mock_coordinator, all_coordinators)

        assert sensor.name == "Update Duration"
        assert sensor.native_unit_of_measurement == "s"

    async def test_update_duration_with_data(self, mock_coordinator):
        """Test update duration with actual duration data."""
        mock_coordinator._last_update_duration = 2.5
        all_coordinators = {"coordinator": mock_coordinator}

        sensor = AutoPiUpdateDurationSensor(mock_coordinator, all_coordinators)

        # The sensor should return the maximum duration from all coordinators
        assert sensor.native_value == 2.5

    async def test_update_duration_no_data(self, mock_coordinator):
        """Test update duration with no duration data."""
        mock_coordinator._last_update_duration = None
        all_coordinators = {"coordinator": mock_coordinator}

        sensor = AutoPiUpdateDurationSensor(mock_coordinator, all_coordinators)

        assert sensor.native_value is None


class TestAutopiTripSensors:
    """Test the trip-related sensors."""

    async def test_trip_count_sensor(self, mock_vehicle):
        """Test trip count sensor."""
        # Create mock trip coordinator with trip data
        mock_trip_coordinator = Mock()
        trip_vehicle = Mock()
        trip_vehicle.trip_count = 5
        trip_vehicle.trips = []
        mock_trip_coordinator.data = {str(mock_vehicle.id): trip_vehicle}

        sensor = AutoPiTripCountSensor(mock_trip_coordinator, str(mock_vehicle.id))

        assert sensor.name == "Trip Count"
        assert sensor.native_value == 5

    async def test_trip_count_sensor_no_trips(self, mock_vehicle):
        """Test trip count sensor with no trips."""
        mock_trip_coordinator = Mock()
        trip_vehicle = Mock()
        trip_vehicle.trip_count = 0
        mock_trip_coordinator.data = {str(mock_vehicle.id): trip_vehicle}

        sensor = AutoPiTripCountSensor(mock_trip_coordinator, str(mock_vehicle.id))

        assert sensor.native_value == 0

    async def test_last_trip_distance_sensor(self, mock_vehicle):
        """Test last trip distance sensor."""
        mock_trip_coordinator = Mock()

        # Create a mock trip
        last_trip = AutoPiTrip(
            trip_id="trip-123",
            vehicle_id=mock_vehicle.id,
            start_time=datetime.now(UTC),
            end_time=datetime.now(UTC),
            start_lat=-1.0,
            start_lng=51.0,
            start_address="Start",
            end_lat=-1.1,
            end_lng=51.1,
            end_address="End",
            duration_seconds=1800,
            distance_km=15.5,
            state="completed",
        )

        trip_vehicle = Mock()
        trip_vehicle.last_trip = last_trip
        mock_trip_coordinator.data = {str(mock_vehicle.id): trip_vehicle}

        sensor = AutoPiLastTripDistanceSensor(mock_trip_coordinator, str(mock_vehicle.id))

        assert sensor.name == "Last Trip Distance"
        assert sensor.native_value == 15.5

    async def test_last_trip_distance_sensor_no_trips(self, mock_vehicle):
        """Test last trip distance sensor with no trips."""
        mock_trip_coordinator = Mock()
        trip_vehicle = Mock()
        trip_vehicle.last_trip = None
        mock_trip_coordinator.data = {str(mock_vehicle.id): trip_vehicle}

        sensor = AutoPiLastTripDistanceSensor(mock_trip_coordinator, str(mock_vehicle.id))

        assert sensor.native_value is None


class TestAsyncSetupEntry:
    """Test the async_setup_entry function."""

    async def test_setup_entry_with_vehicles(
        self, hass: HomeAssistant, mock_config_entry_data, mock_vehicle, mock_vehicle_2
    ):
        """Test setup entry with vehicles."""
        # Create coordinators with data
        mock_coordinator = Mock()
        mock_coordinator.data = {
            str(mock_vehicle.id): mock_vehicle,
            str(mock_vehicle_2.id): mock_vehicle_2,
        }
        mock_coordinator.get_vehicle_count = Mock(return_value=2)
        mock_coordinator._fleet_alerts_total = 0
        mock_coordinator._fleet_alerts = []

        mock_position_coordinator = Mock()
        # Add data fields to position data
        vehicle_with_position = Mock(spec=AutoPiVehicle)
        vehicle_with_position.id = mock_vehicle.id
        vehicle_with_position.name = mock_vehicle.name
        vehicle_with_position.data_fields = {
            "track.pos.alt": DataFieldValue(
                field_prefix="track.pos",
                field_name="alt",
                frequency=1.0,
                value_type="float",
                title="Altitude",
                last_seen=datetime.now(UTC),
                last_value=125.5,
                description="GPS altitude",
                last_update=datetime.now(UTC),
            )
        }
        mock_position_coordinator.data = {
            str(mock_vehicle.id): vehicle_with_position,
        }

        mock_trip_coordinator = None

        # Setup hass data
        hass.data[DOMAIN] = {
            "test_entry": {
                "coordinator": mock_coordinator,
                "position_coordinator": mock_position_coordinator,
                "trip_coordinator": mock_trip_coordinator,
                "coordinators": {
                    "coordinator": mock_coordinator,
                    "position_coordinator": mock_position_coordinator,
                },
            }
        }

        # Create mock config entry
        mock_entry = Mock()
        mock_entry.entry_id = "test_entry"

        # Mock entity callback
        added_entities = []

        def mock_add_entities(entities):
            added_entities.extend(entities)

        # Call async_setup_entry
        await async_setup_entry(hass, mock_entry, mock_add_entities)

        # Verify entities were created
        assert len(added_entities) > 0

        # Should have at least: vehicle count, fleet alert count, update duration, 2 vehicle sensors
        assert any(isinstance(e, AutoPiVehicleCountSensor) for e in added_entities)
        assert any(isinstance(e, AutoPiFleetAlertCountSensor) for e in added_entities)
        assert any(isinstance(e, AutoPiUpdateDurationSensor) for e in added_entities)

    async def test_setup_entry_no_vehicles(
        self, hass: HomeAssistant, mock_config_entry_data
    ):
        """Test setup entry with no vehicles."""
        # Create coordinators with no data
        mock_coordinator = Mock()
        mock_coordinator.data = {}
        mock_coordinator.get_vehicle_count = Mock(return_value=0)
        mock_coordinator._fleet_alerts_total = 0
        mock_coordinator._fleet_alerts = []

        mock_position_coordinator = Mock()
        mock_position_coordinator.data = {}

        # Setup hass data
        hass.data[DOMAIN] = {
            "test_entry": {
                "coordinator": mock_coordinator,
                "position_coordinator": mock_position_coordinator,
                "trip_coordinator": None,
                "coordinators": {
                    "coordinator": mock_coordinator,
                    "position_coordinator": mock_position_coordinator,
                },
            }
        }

        mock_entry = Mock()
        mock_entry.entry_id = "test_entry"

        added_entities = []

        def mock_add_entities(entities):
            added_entities.extend(entities)

        await async_setup_entry(hass, mock_entry, mock_add_entities)

        # Should still create the count sensors
        assert len(added_entities) >= 3
        assert any(isinstance(e, AutoPiVehicleCountSensor) for e in added_entities)
        assert any(isinstance(e, AutoPiFleetAlertCountSensor) for e in added_entities)
