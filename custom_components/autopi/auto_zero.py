"""Auto-zero functionality for AutoPi metrics.

This module manages automatic zeroing of specific vehicle metrics when the vehicle
is not on an active trip. It includes state persistence across Home Assistant restarts
to ensure zeroed metrics remain zeroed until new data arrives.

Key Features:
- Trip-based detection with 6 consecutive COMPLETED calls validation
- 30-minute fallback method using consecutive stale readings
- State persistence using Home Assistant's storage system
- Per-metric cooldown periods to prevent rapid cycling
- Graceful error handling for corrupted/missing storage

Storage Format:
The module stores zeroed metrics in JSON format at .storage/autopi_auto_zero
with the following structure:
{
    "zeroed_metrics": [
        {
            "vehicle_id": "123",
            "field_id": "obd.rpm.value",
            "zeroed_at": "2025-07-29T10:30:00",
            "reason": "trip_completed"
        }
    ]
}
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, TypedDict

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

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

# Storage constants
STORAGE_VERSION = 1
STORAGE_KEY = "autopi_auto_zero"


class ZeroedMetricData(TypedDict):
    """Data structure for a zeroed metric."""

    vehicle_id: str
    field_id: str
    zeroed_at: str  # ISO format timestamp
    reason: str  # "trip_completed" or "stale_data"


class AutoZeroStorageData(TypedDict):
    """Storage data structure for auto-zero state."""

    zeroed_metrics: list[ZeroedMetricData]


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

        # Storage for persistence
        self._hass: HomeAssistant | None = None
        self._store: Store[AutoZeroStorageData] | None = None

    async def async_initialize(self, hass: HomeAssistant) -> None:
        """Initialize storage and load persisted state.

        Args:
            hass: Home Assistant instance
        """
        self._hass = hass
        self._store = Store[AutoZeroStorageData](
            hass, STORAGE_VERSION, STORAGE_KEY
        )

        # Load persisted state
        await self._async_load()

    async def _async_load(self) -> None:
        """Load persisted zeroed metrics from storage."""
        if not self._store:
            _LOGGER.debug("No storage available, skipping load")
            return

        try:
            data = await self._store.async_load()

            if data and "zeroed_metrics" in data:
                _LOGGER.debug(
                    "Loading %d persisted zeroed metrics from storage",
                    len(data["zeroed_metrics"])
                )

                # Restore zeroed metrics
                for metric_data in data["zeroed_metrics"]:
                    try:
                        vehicle_id = metric_data["vehicle_id"]
                        field_id = metric_data["field_id"]
                        zeroed_at = datetime.fromisoformat(metric_data["zeroed_at"])

                        metric_key = (vehicle_id, field_id)
                        self._zeroed_metrics[metric_key] = zeroed_at

                        _LOGGER.info(
                            "Restored zeroed state for %s on vehicle %s (zeroed at %s)",
                            AUTO_ZERO_METRICS.get(field_id, field_id),
                            vehicle_id,
                            zeroed_at.isoformat(),
                        )
                    except (KeyError, ValueError) as e:
                        _LOGGER.warning(
                            "Failed to restore zeroed metric: %s",
                            str(e),
                        )
            else:
                _LOGGER.debug("No persisted zeroed metrics found")

        except Exception as e:
            _LOGGER.warning(
                "Failed to load auto-zero state from storage, starting fresh: %s",
                str(e),
            )
            # Continue with empty state - don't crash on storage errors

    async def _async_save(self) -> None:
        """Save current zeroed metrics to storage."""
        if not self._store:
            _LOGGER.debug("No storage available, skipping save")
            return

        try:
            # Convert zeroed metrics to storage format
            zeroed_metrics: list[ZeroedMetricData] = []

            for (vehicle_id, field_id), zeroed_at in self._zeroed_metrics.items():
                # Determine reason based on current state
                reason = "trip_completed"  # Default
                if (vehicle_id, field_id) in self._stale_call_counts:
                    count, _ = self._stale_call_counts[(vehicle_id, field_id)]
                    if count >= REQUIRED_STALE_CALLS:
                        reason = "stale_data"

                zeroed_metrics.append({
                    "vehicle_id": vehicle_id,
                    "field_id": field_id,
                    "zeroed_at": zeroed_at.isoformat(),
                    "reason": reason,
                })

            data: AutoZeroStorageData = {
                "zeroed_metrics": zeroed_metrics
            }

            await self._store.async_save(data)

            _LOGGER.debug(
                "Saved %d zeroed metrics to storage",
                len(zeroed_metrics)
            )

        except Exception as e:
            _LOGGER.error(
                "Failed to save auto-zero state to storage: %s",
                str(e),
                exc_info=True,
            )

    def _schedule_save(self) -> None:
        """Schedule a save operation to persist state."""
        if self._hass:
            # Use Home Assistant's async_create_task to schedule the save
            self._hass.async_create_task(self._async_save())
        else:
            _LOGGER.debug("No Home Assistant instance available, cannot schedule save")

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
        try:
            metric_name = AUTO_ZERO_METRICS.get(metric_id, metric_id)
            _LOGGER.debug(
                "Evaluating auto-zero for %s on vehicle %s (enabled: %s, has_trip: %s)",
                metric_name,
                vehicle_id,
                auto_zero_enabled,
                last_trip is not None,
            )

            # Feature must be enabled
            if not auto_zero_enabled:
                return False

            # Only auto-zero specific metrics
            if metric_id not in AUTO_ZERO_METRICS:
                return False

            # If no field data, can't make a decision
            if field_data is None:
                _LOGGER.debug(
                    "No field data available for %s on vehicle %s",
                    metric_name,
                    vehicle_id,
                )
                return False

            metric_key = (vehicle_id, metric_id)
            now = datetime.now()

            _LOGGER.debug(
                "Processing %s for vehicle %s - last_seen: %s, age: %.1f minutes",
                metric_name,
                vehicle_id,
                field_data.last_seen.isoformat(),
                (now - field_data.last_seen).total_seconds() / 60,
            )

            # Check if metric is in cooldown period
            if metric_key in self._metric_cooldowns:
                if now < self._metric_cooldowns[metric_key]:
                    remaining = (self._metric_cooldowns[metric_key] - now).total_seconds() / 60
                    _LOGGER.debug(
                        "Metric %s for vehicle %s is in cooldown (%.1f minutes remaining)",
                        metric_name,
                        vehicle_id,
                        remaining,
                    )
                    return False
                else:
                    # Cooldown expired, remove it
                    _LOGGER.debug(
                        "Cooldown expired for %s on vehicle %s",
                        metric_name,
                        vehicle_id,
                    )
                    del self._metric_cooldowns[metric_key]

            # Check if metric was previously zeroed
            was_zeroed = metric_key in self._zeroed_metrics

            # If last_seen has updated, stop zeroing
            if was_zeroed:
                previous_last_seen = self._zeroed_metrics[metric_key]
                if field_data.last_seen > previous_last_seen:
                    _LOGGER.info(
                        "Metric %s for vehicle %s has new data, stopping auto-zero",
                        metric_name,
                        vehicle_id,
                    )
                    del self._zeroed_metrics[metric_key]
                    # Add cooldown to prevent immediate re-zeroing
                    self._metric_cooldowns[metric_key] = now + timedelta(minutes=METRIC_COOLDOWN_MINUTES)
                    # Schedule save
                    self._schedule_save()
                    return False

            # Primary method: Use trip data
            if last_trip:
                trip_key = (vehicle_id, last_trip.trip_id)

                # Check if trip state changed
                current_state = (last_trip.trip_id, last_trip.state)
                previous_state = self._last_trip_state.get(vehicle_id)

                if previous_state != current_state:
                    _LOGGER.debug(
                        "Trip state changed for vehicle %s: %s -> %s (trip: %s)",
                        vehicle_id,
                        previous_state[1] if previous_state else "None",
                        last_trip.state,
                        last_trip.trip_id[:8],  # First 8 chars of trip ID
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
                                "Trip completed for vehicle %s, starting auto-zero timer",
                                vehicle_id,
                            )

                # Track consecutive COMPLETED calls
                if last_trip.state == "COMPLETED":
                    self._completed_call_counts[vehicle_id] = self._completed_call_counts.get(vehicle_id, 0) + 1
                    _LOGGER.debug(
                        "Vehicle %s has %d/%d consecutive COMPLETED calls",
                        vehicle_id,
                        self._completed_call_counts[vehicle_id],
                        REQUIRED_COMPLETED_CALLS,
                    )
                else:
                    # Reset count if not COMPLETED
                    self._completed_call_counts[vehicle_id] = 0
                    # Clean up any zeroed state
                    if metric_key in self._zeroed_metrics:
                        _LOGGER.info(
                            "Removing auto-zero for %s on vehicle %s due to trip state %s",
                            metric_name,
                            vehicle_id,
                            last_trip.state,
                        )
                        del self._zeroed_metrics[metric_key]
                        # Schedule save
                        self._schedule_save()
                    return False

                # Require minimum consecutive COMPLETED calls
                if self._completed_call_counts.get(vehicle_id, 0) < REQUIRED_COMPLETED_CALLS:
                    _LOGGER.debug(
                        "Vehicle %s needs %d more COMPLETED calls before zeroing",
                        vehicle_id,
                        REQUIRED_COMPLETED_CALLS - self._completed_call_counts.get(vehicle_id, 0),
                    )
                    return False

                # Check if enough time has passed since trip completion
                completion_time = self._trip_completion_times.get(trip_key)
                if completion_time:
                    time_since_completion = now - completion_time

                    _LOGGER.debug(
                        "Trip %s for vehicle %s completed %.1f minutes ago",
                        last_trip.trip_id[:8],
                        vehicle_id,
                        time_since_completion.total_seconds() / 60,
                    )

                    if time_since_completion >= timedelta(minutes=TRIP_COMPLETION_WAIT_MINUTES):
                        # Check if metric is stale
                        time_since_update = now - field_data.last_seen

                        if time_since_update >= timedelta(minutes=TRIP_COMPLETION_WAIT_MINUTES):
                            if not was_zeroed:
                                _LOGGER.info(
                                    "Auto-zeroing %s for vehicle %s (trip method)",
                                    metric_name,
                                    vehicle_id,
                                )
                                self._zeroed_metrics[metric_key] = field_data.last_seen
                                # Schedule save
                                self._schedule_save()
                            return True
                        else:
                            _LOGGER.debug(
                                "Metric %s for vehicle %s is not stale enough (%.1f minutes old, need %d)",
                                metric_name,
                                vehicle_id,
                                time_since_update.total_seconds() / 60,
                                TRIP_COMPLETION_WAIT_MINUTES,
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
                        metric_name,
                        vehicle_id,
                    )
                    return False

                # Increment stale count
                time_since_update = now - field_data.last_seen
                if time_since_update >= timedelta(minutes=1):  # At least 1 minute old
                    current_count += 1
                    self._stale_call_counts[metric_key] = (current_count, field_data.last_seen)

                    _LOGGER.debug(
                        "Metric %s for vehicle %s has %d/%d consecutive stale readings",
                        metric_name,
                        vehicle_id,
                        current_count,
                        REQUIRED_STALE_CALLS,
                    )

                    # Require minimum consecutive stale calls
                    if current_count >= REQUIRED_STALE_CALLS:
                        if not was_zeroed:
                            _LOGGER.info(
                                "Auto-zeroing %s for vehicle %s (fallback method)",
                                metric_name,
                                vehicle_id,
                            )
                            self._zeroed_metrics[metric_key] = field_data.last_seen
                            # Schedule save
                            self._schedule_save()
                        return True

            # Don't zero
            return False

        except Exception as e:
            _LOGGER.error(
                "Error evaluating auto-zero for %s on vehicle %s: %s",
                metric_id,
                vehicle_id,
                str(e),
                exc_info=True,
            )
            # On error, fail safe - don't zero
            return False

    def cleanup_old_trips(self, keep_hours: int = 24) -> None:
        """Clean up old trip completion times to prevent memory growth.

        Args:
            keep_hours: Number of hours to keep trip data
        """
        try:
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

            # Clean up completed call counts for vehicles with no recent activity
            old_vehicles = []
            for vehicle_id in list(self._completed_call_counts.keys()):
                # Check if vehicle has any recent trip times
                has_recent = any(
                    k[0] == vehicle_id and time >= cutoff
                    for k, time in self._trip_completion_times.items()
                )
                if not has_recent and vehicle_id not in self._last_trip_state:
                    old_vehicles.append(vehicle_id)

            for vehicle_id in old_vehicles:
                del self._completed_call_counts[vehicle_id]

            if old_trip_keys or expired_cooldowns or old_stale_keys or old_vehicles:
                _LOGGER.debug(
                    "Cleanup complete: removed %d old trips, %d expired cooldowns, %d old stale counts, %d old vehicle counts",
                    len(old_trip_keys),
                    len(expired_cooldowns),
                    len(old_stale_keys),
                    len(old_vehicles),
                )

        except Exception as e:
            _LOGGER.error(
                "Error during auto-zero cleanup: %s",
                str(e),
                exc_info=True,
            )

    def get_metric_status(self, vehicle_id: str, metric_id: str) -> dict[str, Any]:
        """Get the current status of a metric for entity attributes.

        Args:
            vehicle_id: Vehicle ID
            metric_id: Metric field ID

        Returns:
            Dictionary with metric status information
        """
        metric_key = (vehicle_id, metric_id)

        status: dict[str, Any] = {
            "auto_zero_enabled": metric_id in AUTO_ZERO_METRICS,
            "is_zeroed": metric_key in self._zeroed_metrics,
        }

        if metric_key in self._zeroed_metrics:
            status["zeroed_at"] = self._zeroed_metrics[metric_key].isoformat()

        if metric_key in self._metric_cooldowns:
            cooldown_expiry = self._metric_cooldowns[metric_key]
            if datetime.now() < cooldown_expiry:
                status["cooldown_until"] = cooldown_expiry.isoformat()

        return status


# Global instance
_auto_zero_manager: AutoZeroManager | None = None


def get_auto_zero_manager() -> AutoZeroManager:
    """Get the global auto-zero manager instance."""
    global _auto_zero_manager
    if _auto_zero_manager is None:
        _auto_zero_manager = AutoZeroManager()
    return _auto_zero_manager
