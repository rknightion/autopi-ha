"""Tests for AutoPi fleet alert functionality."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from custom_components.autopi.client import AutoPiClient
from custom_components.autopi.types import AlertDict, FleetAlert


class TestAlertData:
    """Test alert data models."""

    def test_fleet_alert_from_api_data(self):
        """Test creating FleetAlert from API data."""
        alert_data: AlertDict = {
            "title": "Low Battery Voltage",
            "uuid": "alert-123",
            "vehicle_count": 3,
        }

        alert = FleetAlert.from_api_data("warning", alert_data)

        assert alert.alert_id == "alert-123"
        assert alert.title == "Low Battery Voltage"
        assert alert.severity == "warning"
        assert alert.vehicle_count == 3


class TestAutoPiClientAlerts:
    """Test AutoPi client alert methods."""

    @pytest.mark.asyncio
    async def test_get_fleet_alerts_success(self):
        """Test successful fleet alerts fetching."""
        session = Mock()
        client = AutoPiClient(session, "test_key")

        alerts_response = {
            "total": 2,
            "severities": [
                {
                    "severity": "warning",
                    "alerts": [
                        {
                            "title": "Low Battery",
                            "uuid": "alert-1",
                            "vehicle_count": 2,
                        },
                        {
                            "title": "No GPS Signal",
                            "uuid": "alert-2",
                            "vehicle_count": 1,
                        },
                    ],
                }
            ],
        }

        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = alerts_response

            total, alerts = await client.get_fleet_alerts()

            assert total == 2
            assert len(alerts) == 2
            assert alerts[0].title == "Low Battery"
            assert alerts[0].severity == "warning"
            assert alerts[0].vehicle_count == 2
            assert alerts[1].title == "No GPS Signal"

            mock_request.assert_called_once_with(
                "GET",
                "/logbook/fleet_summary/alerts/",
            )

    @pytest.mark.asyncio
    async def test_get_fleet_alerts_empty(self):
        """Test fleet alerts with no active alerts."""
        session = Mock()
        client = AutoPiClient(session, "test_key")

        alerts_response = {"total": 0, "severities": []}

        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = alerts_response

            total, alerts = await client.get_fleet_alerts()

            assert total == 0
            assert len(alerts) == 0

    @pytest.mark.asyncio
    async def test_get_fleet_alerts_multiple_severities(self):
        """Test fleet alerts with multiple severity levels."""
        session = Mock()
        client = AutoPiClient(session, "test_key")

        alerts_response = {
            "total": 3,
            "severities": [
                {
                    "severity": "critical",
                    "alerts": [
                        {
                            "title": "Engine Failure",
                            "uuid": "alert-1",
                            "vehicle_count": 1,
                        }
                    ],
                },
                {
                    "severity": "warning",
                    "alerts": [
                        {
                            "title": "Low Battery",
                            "uuid": "alert-2",
                            "vehicle_count": 2,
                        },
                        {
                            "title": "Service Due",
                            "uuid": "alert-3",
                            "vehicle_count": 3,
                        },
                    ],
                },
            ],
        }

        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = alerts_response

            total, alerts = await client.get_fleet_alerts()

            assert total == 3
            assert len(alerts) == 3

            # Check alerts are parsed correctly
            critical_alerts = [a for a in alerts if a.severity == "critical"]
            warning_alerts = [a for a in alerts if a.severity == "warning"]

            assert len(critical_alerts) == 1
            assert len(warning_alerts) == 2
            assert critical_alerts[0].title == "Engine Failure"


class TestFleetAlertCountSensor:
    """Test the fleet alert count sensor."""

    @pytest.mark.asyncio
    async def test_fleet_alert_count_sensor(self):
        """Test fleet alert count sensor with alerts."""
        from custom_components.autopi.sensor import AutoPiFleetAlertCountSensor

        # Create mock coordinator
        coordinator = Mock()
        coordinator.config_entry = Mock()
        coordinator.config_entry.entry_id = "test_entry"
        coordinator.last_update_success = True
        coordinator.fleet_alerts_total = 3
        coordinator.fleet_alerts = [
            FleetAlert(
                alert_id="alert-1",
                title="Low Battery",
                severity="warning",
                vehicle_count=2,
            ),
            FleetAlert(
                alert_id="alert-2",
                title="Engine Issue",
                severity="critical",
                vehicle_count=1,
            ),
            FleetAlert(
                alert_id="alert-3",
                title="Service Due",
                severity="warning",
                vehicle_count=5,
            ),
        ]

        sensor = AutoPiFleetAlertCountSensor(coordinator)

        assert sensor.native_value == 3
        assert sensor.name == "Fleet Alert Count"
        assert sensor.icon == "mdi:alert"

        # Check extra state attributes
        attrs = sensor.extra_state_attributes
        assert attrs["severities"] == {"warning": 2, "critical": 1}
        assert len(attrs["alerts"]) == 3
        assert attrs["alerts"][0]["title"] == "Low Battery"
        assert attrs["alerts"][0]["severity"] == "warning"
        assert attrs["alerts"][0]["vehicle_count"] == 2

    @pytest.mark.asyncio
    async def test_fleet_alert_count_sensor_no_alerts(self):
        """Test fleet alert count sensor with no alerts."""
        from custom_components.autopi.sensor import AutoPiFleetAlertCountSensor

        # Create mock coordinator
        coordinator = Mock()
        coordinator.config_entry = Mock()
        coordinator.config_entry.entry_id = "test_entry"
        coordinator.last_update_success = True
        coordinator.fleet_alerts_total = 0
        coordinator.fleet_alerts = []

        sensor = AutoPiFleetAlertCountSensor(coordinator)

        assert sensor.native_value == 0

        # Check extra state attributes
        attrs = sensor.extra_state_attributes
        assert attrs["severities"] == {}
        assert attrs["alerts"] == []
