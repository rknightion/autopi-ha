"""Auto-zero functionality for AutoPi metrics."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from .types import AutoPiTrip, DataFieldValue

_LOGGER = logging.getLogger(__name__)

# Metrics that should be auto-zeroed when vehicle is not on a trip
AUTO_ZERO_METRICS = {
    "obd.coolant_temp.value": "Coolant Temperature (OBD)",
    "obd.engine_load.value": "Engine Load (OBD)",
    "obd.rpm.value": "Engine RPM (OBD)",
    "obd.run_time.value": "Engine Run Time (OBD)",
    "std.fuel_used_gps.value": "Fuel Used (GPS)",
    "obd.throttle_pos.value": "Throttle Position (OBD)",
    "obd.speed.value": "Vehicle Speed (OBD)",
    "std.accelerometer_axis_x.value": "X-Axis Acceleration",
    "std.accelerometer_axis_y.value": "Y-Axis Acceleration",
    "std.accelerometer_axis_z.value": "Z-Axis Acceleration",
}

# Time to wait after trip completion before zeroing metrics
TRIP_COMPLETION_WAIT_MINUTES = 5

# Number of consecutive COMPLETED calls required before zeroing
REQUIRED_COMPLETED_CALLS = 6

# Cooldown period after un-zeroing a metric before it can be zeroed again
METRIC_COOLDOWN_MINUTES = 30

# Fallback timeout for zeroing metrics when no trip data available
FALLBACK_TIMEOUT_MINUTES = 30

# Number of consecutive stale readings required for fallback zeroing
REQUIRED_STALE_CALLS = 30  # 30 minutes with 1-minute polling


class AutoZeroManager:
    """Manages auto-zero state for vehicle metrics."""

    def __init__(self) -> None:
        """Initialize the auto-zero manager."""
        # Track when we first saw each trip as completed
        # Key: (vehicle_id, trip_id), Value: datetime
        self._trip_completion_times: dict[tuple[str, str], datetime] = {}

        # Track consecutive COMPLETED calls for each vehicle
        # Key: vehicle_id, Value: count
        self._completed_call_counts: dict[str, int] = {}

        # Track which metrics are currently zeroed
        # Key: (vehicle_id, metric_id), Value: last_seen time when zeroed
        self._zeroed_metrics: dict[tuple[str, str], datetime] = {}

        # Track metric cooldowns after un-zeroing
        # Key: (vehicle_id, metric_id), Value: cooldown expiry time
        self._metric_cooldowns: dict[tuple[str, str], datetime] = {}

        # Track last known trip state for each vehicle
        # Key: vehicle_id, Value: (trip_id, state)
        self._last_trip_state: dict[str, tuple[str, str]] = {}

        # Track consecutive stale readings for fallback method
        # Key: (vehicle_id, metric_id), Value: (count, last_seen_time)
        self._stale_call_counts: dict[tuple[str, str], tuple[int, datetime]] = {}

    def should_zero_metric(
        self,
        vehicle_id: str,
        metric_id: str,
        field_data: DataFieldValue | None,
        last_trip: AutoPiTrip | None,
        auto_zero_enabled: bool = False,
    ) -> bool:
        """Determine if a metric should be zeroed.

        Args:
            vehicle_id: Vehicle ID
            metric_id: Metric field ID
            field_data: Current field data
            last_trip: Last trip information
            auto_zero_enabled: Whether auto-zero is enabled

        Returns:
            True if the metric should be zeroed, False otherwise
        """
        # Feature must be enabled
        if not auto_zero_enabled:
            return False

        # Only auto-zero specific metrics
        if metric_id not in AUTO_ZERO_METRICS:
            return False

        # If no field data, can't make a decision
        if field_data is None:
            return False

        metric_key = (vehicle_id, metric_id)
        now = datetime.now()

        # Check if metric is in cooldown period
        if metric_key in self._metric_cooldowns:
            if now < self._metric_cooldowns[metric_key]:
                _LOGGER.debug(
                    "Metric %s for vehicle %s is in cooldown, not zeroing",
                    AUTO_ZERO_METRICS.get(metric_id, metric_id),
                    vehicle_id,
                )
                return False
            else:
                # Cooldown expired, remove it
                del self._metric_cooldowns[metric_key]

        # Check if metric was previously zeroed
        was_zeroed = metric_key in self._zeroed_metrics

        # If last_seen has updated, stop zeroing
        if was_zeroed:
            previous_last_seen = self._zeroed_metrics[metric_key]
            if field_data.last_seen > previous_last_seen:
                _LOGGER.debug(
                    "Metric %s for vehicle %s has new data, stopping auto-zero",
                    AUTO_ZERO_METRICS.get(metric_id, metric_id),
                    vehicle_id,
                )
                del self._zeroed_metrics[metric_key]
                # Add cooldown to prevent immediate re-zeroing
                self._metric_cooldowns[metric_key] = now + timedelta(minutes=METRIC_COOLDOWN_MINUTES)
                return False

        # Primary method: Use trip data
        if last_trip:
            trip_key = (vehicle_id, last_trip.trip_id)

            # Check if trip state changed
            current_state = (last_trip.trip_id, last_trip.state)
            previous_state = self._last_trip_state.get(vehicle_id)

            if previous_state != current_state:
                _LOGGER.debug(
                    "Trip state changed for vehicle %s: %s -> %s",
                    vehicle_id,
                    previous_state[1] if previous_state else "None",
                    last_trip.state,
                )
                self._last_trip_state[vehicle_id] = current_state

                # Reset completed call count on any state change
                if last_trip.state != "COMPLETED":
                    self._completed_call_counts[vehicle_id] = 0
                    _LOGGER.debug(
                        "Reset completed call count for vehicle %s due to state change to %s",
                        vehicle_id,
                        last_trip.state,
                    )

                # If trip just completed, record the time
                if last_trip.state == "COMPLETED":
                    if trip_key not in self._trip_completion_times:
                        self._trip_completion_times[trip_key] = now
                        _LOGGER.info(
                            "Trip %s completed for vehicle %s, starting auto-zero timer",
                            last_trip.trip_id,
                            vehicle_id,
                        )

            # Track consecutive COMPLETED calls
            if last_trip.state == "COMPLETED":
                self._completed_call_counts[vehicle_id] = self._completed_call_counts.get(vehicle_id, 0) + 1
                _LOGGER.debug(
                    "Vehicle %s has %d consecutive COMPLETED calls",
                    vehicle_id,
                    self._completed_call_counts[vehicle_id],
                )
            else:
                # Reset count if not COMPLETED
                self._completed_call_counts[vehicle_id] = 0
                # Clean up any zeroed state
                if metric_key in self._zeroed_metrics:
                    del self._zeroed_metrics[metric_key]
                return False

            # Require minimum consecutive COMPLETED calls
            if self._completed_call_counts.get(vehicle_id, 0) < REQUIRED_COMPLETED_CALLS:
                _LOGGER.debug(
                    "Vehicle %s needs %d more COMPLETED calls before zeroing (has %d)",
                    vehicle_id,
                    REQUIRED_COMPLETED_CALLS - self._completed_call_counts.get(vehicle_id, 0),
                    self._completed_call_counts.get(vehicle_id, 0),
                )
                return False

            # Check if enough time has passed since trip completion
            completion_time = self._trip_completion_times.get(trip_key)
            if completion_time:
                time_since_completion = now - completion_time

                if time_since_completion >= timedelta(minutes=TRIP_COMPLETION_WAIT_MINUTES):
                    # Check if metric is stale
                    time_since_update = now - field_data.last_seen

                    if time_since_update >= timedelta(minutes=TRIP_COMPLETION_WAIT_MINUTES):
                        if not was_zeroed:
                            _LOGGER.info(
                                "Auto-zeroing %s for vehicle %s (trip method: %d consecutive COMPLETED calls)",
                                AUTO_ZERO_METRICS.get(metric_id, metric_id),
                                vehicle_id,
                                self._completed_call_counts.get(vehicle_id, 0),
                            )
                            self._zeroed_metrics[metric_key] = field_data.last_seen
                        return True
                    else:
                        _LOGGER.debug(
                            "Metric %s for vehicle %s is not stale enough (%.1f minutes old)",
                            AUTO_ZERO_METRICS.get(metric_id, metric_id),
                            vehicle_id,
                            time_since_update.total_seconds() / 60,
                        )

        # Fallback method: Use consecutive stale readings
        else:
            # Track consecutive stale readings
            current_count, previous_last_seen = self._stale_call_counts.get(metric_key, (0, field_data.last_seen))

            # If last_seen changed, reset count
            if field_data.last_seen != previous_last_seen:
                self._stale_call_counts[metric_key] = (0, field_data.last_seen)
                _LOGGER.debug(
                    "Reset stale count for %s on vehicle %s due to data update",
                    AUTO_ZERO_METRICS.get(metric_id, metric_id),
                    vehicle_id,
                )
                return False

            # Increment stale count
            time_since_update = now - field_data.last_seen
            if time_since_update >= timedelta(minutes=1):  # At least 1 minute old
                current_count += 1
                self._stale_call_counts[metric_key] = (current_count, field_data.last_seen)

                _LOGGER.debug(
                    "Metric %s for vehicle %s has %d consecutive stale readings (%.1f minutes old)",
                    AUTO_ZERO_METRICS.get(metric_id, metric_id),
                    vehicle_id,
                    current_count,
                    time_since_update.total_seconds() / 60,
                )

                # Require minimum consecutive stale calls
                if current_count >= REQUIRED_STALE_CALLS:
                    if not was_zeroed:
                        _LOGGER.info(
                            "Auto-zeroing %s for vehicle %s (fallback method: %d consecutive stale readings)",
                            AUTO_ZERO_METRICS.get(metric_id, metric_id),
                            vehicle_id,
                            current_count,
                        )
                        self._zeroed_metrics[metric_key] = field_data.last_seen
                    return True

        # Don't zero
        return False

    def cleanup_old_trips(self, keep_hours: int = 24) -> None:
        """Clean up old trip completion times to prevent memory growth.

        Args:
            keep_hours: Number of hours to keep trip data
        """
        now = datetime.now()
        cutoff = now - timedelta(hours=keep_hours)

        # Remove old trip completion times (only those older than cutoff)
        old_trip_keys = [
            key for key, time in self._trip_completion_times.items()
            if time < cutoff
        ]

        for key in old_trip_keys:
            del self._trip_completion_times[key]

        # Remove old cooldowns that have expired
        expired_cooldowns = [
            key for key, expiry in self._metric_cooldowns.items()
            if expiry < now
        ]

        for key in expired_cooldowns:
            del self._metric_cooldowns[key]

        # Clean up stale call counts for metrics that haven't been seen recently
        old_stale_keys = []
        for key, (_count, last_seen) in self._stale_call_counts.items():
            if now - last_seen > timedelta(hours=keep_hours):
                old_stale_keys.append(key)

        for key in old_stale_keys:
            del self._stale_call_counts[key]

        if old_trip_keys or expired_cooldowns or old_stale_keys:
            _LOGGER.debug(
                "Cleanup complete: removed %d old trips, %d expired cooldowns, %d old stale counts",
                len(old_trip_keys),
                len(expired_cooldowns),
                len(old_stale_keys),
            )


# Global instance
_auto_zero_manager = AutoZeroManager()


def get_auto_zero_manager() -> AutoZeroManager:
    """Get the global auto-zero manager instance."""
    return _auto_zero_manager

