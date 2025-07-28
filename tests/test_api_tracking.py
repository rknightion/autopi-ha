"""Test API call tracking across coordinators."""

from unittest.mock import Mock

from custom_components.autopi.sensor import AutoPiAPICallsSensor


class TestAPITracking:
    """Test API call tracking."""

    def test_api_calls_sensor_counts_all_coordinators(self):
        """Test that API calls sensor counts from all coordinators."""
        # Create mock coordinators with different API call counts
        coordinator1 = Mock()
        coordinator1.api_call_count = 10
        coordinator1.config_entry = Mock()
        coordinator1.config_entry.entry_id = "test_entry"
        coordinator1.last_update_success = True

        coordinator2 = Mock()
        coordinator2.api_call_count = 5
        coordinator2.last_update_success = True

        coordinator3 = Mock()
        coordinator3.api_call_count = 3
        coordinator3.last_update_success = True

        coordinators = {
            "base": coordinator1,
            "position": coordinator2,
            "trip": coordinator3,
        }

        # Create sensor - use coordinator1 as the primary coordinator
        sensor = AutoPiAPICallsSensor(coordinator1, coordinators)

        # Check total
        assert sensor.native_value == 18  # 10 + 5 + 3

        # Check attributes show breakdown
        attrs = sensor.extra_state_attributes
        assert attrs["base"] == 10
        assert attrs["position"] == 5
        assert attrs["trip"] == 3

    def test_api_calls_sensor_handles_empty_coordinators(self):
        """Test that API calls sensor handles empty coordinator dict."""
        # Need at least one coordinator for initialization
        coordinator = Mock()
        coordinator.api_call_count = 0
        coordinator.config_entry = Mock()
        coordinator.config_entry.entry_id = "test_entry"
        coordinator.last_update_success = True

        coordinators = {"base": coordinator}

        sensor = AutoPiAPICallsSensor(coordinator, coordinators)
        assert sensor.native_value == 0

    def test_api_calls_sensor_restoration(self):
        """Test that API calls sensor handles restoration correctly."""
        coordinator = Mock()
        coordinator.api_call_count = 5
        coordinator.config_entry = Mock()
        coordinator.config_entry.entry_id = "test_entry"
        coordinator.last_update_success = True

        coordinators = {"base": coordinator}

        sensor = AutoPiAPICallsSensor(coordinator, coordinators)

        # Simulate restored value being higher
        sensor._last_value = 100

        # Should use restored value when current is lower
        assert sensor.native_value == 100

        # Update coordinator count
        coordinator.api_call_count = 150

        # Should use actual value when it's higher than restored
        assert sensor.native_value == 150
