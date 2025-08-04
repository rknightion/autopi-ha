"""Auto-zero functionality for AutoPi metrics.

This module manages automatic zeroing of specific vehicle metrics when data
becomes stale. It includes state persistence across Home Assistant restarts
to ensure zeroed metrics remain zeroed until new data arrives.

Key Features:
- Simple time-based detection: zero if last_seen > 15 minutes old
- Automatic un-zeroing when fresh data arrives
- State persistence using Home Assistant's storage system
- Graceful error handling for corrupted/missing storage

Storage Format:
The module stores zeroed metrics in JSON format at .storage/autopi_auto_zero
with the following structure:
{
    "zeroed_metrics": [
        {
            "vehicle_id": "123",
            "field_id": "obd.rpm.value",
            "zeroed_at": "2025-07-29T10:30:00"
        }
    ]
}
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any, TypedDict

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .types import DataFieldValue

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

# Time threshold for considering data stale and zeroing metrics
STALE_DATA_THRESHOLD_MINUTES = 15

# Storage constants
STORAGE_VERSION = 1
STORAGE_KEY = "autopi_auto_zero"


class ZeroedMetricData(TypedDict):
    """Data structure for a zeroed metric."""

    vehicle_id: str
    field_id: str
    zeroed_at: str  # ISO format timestamp


class AutoZeroStorageData(TypedDict):
    """Storage data structure for auto-zero state."""

    zeroed_metrics: list[ZeroedMetricData]


class AutoZeroManager:
    """Manages auto-zero state for vehicle metrics."""

    def __init__(self) -> None:
        """Initialize the auto-zero manager."""
        # Track which metrics are currently zeroed
        # Key: (vehicle_id, metric_id), Value: last_seen time when zeroed
        self._zeroed_metrics: dict[tuple[str, str], datetime] = {}

        # Storage for persistence
        self._hass: HomeAssistant | None = None
        self._store: Store[AutoZeroStorageData] | None = None

    async def async_initialize(self, hass: HomeAssistant) -> None:
        """Initialize storage and load persisted state.

        Args:
            hass: Home Assistant instance
        """
        self._hass = hass
        self._store = Store[AutoZeroStorageData](hass, STORAGE_VERSION, STORAGE_KEY)

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
                    len(data["zeroed_metrics"]),
                )

                # Restore zeroed metrics
                _LOGGER.debug(
                    "Processing %d zeroed metrics from storage",
                    len(data["zeroed_metrics"]),
                )

                for metric_data in data["zeroed_metrics"]:
                    try:
                        vehicle_id = metric_data["vehicle_id"]
                        field_id = metric_data["field_id"]
                        zeroed_at = datetime.fromisoformat(metric_data["zeroed_at"])

                        metric_key = (vehicle_id, field_id)
                        # Only restore if the metric should still be zeroed
                        # (i.e., it was zeroed within the last 24 hours)
                        now = datetime.now(zeroed_at.tzinfo or UTC)
                        age_hours = (now - zeroed_at).total_seconds() / 3600

                        _LOGGER.debug(
                            "Evaluating stored zero state: %s on vehicle %s, zeroed %.1f hours ago",
                            AUTO_ZERO_METRICS.get(field_id, field_id),
                            vehicle_id,
                            age_hours,
                        )

                        if now - zeroed_at < timedelta(hours=24):
                            self._zeroed_metrics[metric_key] = zeroed_at

                            _LOGGER.info(
                                "RESTORED zeroed state for %s on vehicle %s (zeroed %.1f hours ago at %s)",
                                AUTO_ZERO_METRICS.get(field_id, field_id),
                                vehicle_id,
                                age_hours,
                                zeroed_at.isoformat(),
                            )
                        else:
                            _LOGGER.info(
                                "SKIPPED restoring zeroed state for %s on vehicle %s - too old (%.1f hours, zeroed at %s)",
                                AUTO_ZERO_METRICS.get(field_id, field_id),
                                vehicle_id,
                                age_hours,
                                zeroed_at.isoformat(),
                            )
                    except (KeyError, ValueError) as e:
                        _LOGGER.warning(
                            "Failed to restore zeroed metric: %s",
                            str(e),
                        )
            else:
                _LOGGER.debug("No persisted zeroed metrics found")

        except (OSError, ValueError, TypeError) as e:
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
                zeroed_metrics.append(
                    {
                        "vehicle_id": vehicle_id,
                        "field_id": field_id,
                        "zeroed_at": zeroed_at.isoformat(),
                    }
                )

            data: AutoZeroStorageData = {"zeroed_metrics": zeroed_metrics}

            await self._store.async_save(data)

            _LOGGER.info(
                "[AUTO-ZERO SAVE] Saved %d zeroed metrics to storage",
                len(zeroed_metrics),
            )
            for metric in zeroed_metrics:
                _LOGGER.debug(
                    "[AUTO-ZERO SAVE] Saved: %s on vehicle %s (zeroed at %s)",
                    AUTO_ZERO_METRICS.get(metric["field_id"], metric["field_id"]),
                    metric["vehicle_id"],
                    metric["zeroed_at"],
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
            _LOGGER.debug(
                "[AUTO-ZERO SAVE] Scheduling save operation with %d zeroed metrics",
                len(self._zeroed_metrics),
            )
            # Use Home Assistant's async_create_task to schedule the save
            self._hass.async_create_task(self._async_save())
        else:
            _LOGGER.debug(
                "[AUTO-ZERO SAVE] No Home Assistant instance available, cannot schedule save"
            )

    def should_zero_metric(
        self,
        vehicle_id: str,
        metric_id: str,
        field_data: DataFieldValue | None,
        auto_zero_enabled: bool = False,
    ) -> bool:
        """Determine if a metric should be zeroed.

        Args:
            vehicle_id: Vehicle ID
            metric_id: Metric field ID
            field_data: Current field data
            auto_zero_enabled: Whether auto-zero is enabled

        Returns:
            True if the metric should be zeroed, False otherwise
        """
        try:
            metric_name = AUTO_ZERO_METRICS.get(metric_id, metric_id)

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
            # Use timezone-aware datetime to match field_data.last_seen
            now = datetime.now(field_data.last_seen.tzinfo)

            _LOGGER.debug(
                "[AUTO-ZERO] Processing %s for vehicle %s - last_seen: %s, age: %.1f minutes",
                metric_name,
                vehicle_id,
                field_data.last_seen.isoformat(),
                (now - field_data.last_seen).total_seconds() / 60,
            )

            # Calculate time since last update
            time_since_update = now - field_data.last_seen
            was_zeroed = metric_key in self._zeroed_metrics

            _LOGGER.debug(
                "[AUTO-ZERO EVAL] %s on vehicle %s: last_seen %.1f min ago (threshold %d min), currently zeroed: %s",
                metric_name,
                vehicle_id,
                time_since_update.total_seconds() / 60,
                STALE_DATA_THRESHOLD_MINUTES,
                was_zeroed,
            )

            # Check if data is stale (greater than threshold)
            if time_since_update > timedelta(minutes=STALE_DATA_THRESHOLD_MINUTES):
                if not was_zeroed:
                    _LOGGER.info(
                        "[AUTO-ZERO ACTION] ZEROING %s for vehicle %s - data is %.1f minutes old (threshold: %d min)",
                        metric_name,
                        vehicle_id,
                        time_since_update.total_seconds() / 60,
                        STALE_DATA_THRESHOLD_MINUTES,
                    )
                    self._zeroed_metrics[metric_key] = field_data.last_seen
                    # Schedule save
                    self._schedule_save()
                    _LOGGER.debug(
                        "[AUTO-ZERO] Scheduled save after zeroing %s",
                        metric_name,
                    )
                else:
                    # Update the stored last_seen time if it's changed
                    stored_last_seen = self._zeroed_metrics.get(metric_key)
                    if stored_last_seen != field_data.last_seen:
                        _LOGGER.debug(
                            "[AUTO-ZERO UPDATE] Updating stored last_seen for already-zeroed %s on vehicle %s (old: %s, new: %s)",
                            metric_name,
                            vehicle_id,
                            stored_last_seen.isoformat()
                            if stored_last_seen
                            else "None",
                            field_data.last_seen.isoformat(),
                        )
                        self._zeroed_metrics[metric_key] = field_data.last_seen
                        # Schedule save
                        self._schedule_save()
                    else:
                        _LOGGER.debug(
                            "[AUTO-ZERO] %s already zeroed, no update needed",
                            metric_name,
                        )
                return True
            else:
                # Data is fresh - remove from zeroed metrics if it was zeroed
                if was_zeroed:
                    _LOGGER.info(
                        "[AUTO-ZERO ACTION] UN-ZEROING %s for vehicle %s - fresh data received (%.1f minutes old)",
                        metric_name,
                        vehicle_id,
                        time_since_update.total_seconds() / 60,
                    )
                    del self._zeroed_metrics[metric_key]
                    # Schedule save
                    self._schedule_save()
                    _LOGGER.debug(
                        "[AUTO-ZERO] Scheduled save after un-zeroing %s",
                        metric_name,
                    )
                else:
                    _LOGGER.debug(
                        "[AUTO-ZERO] %s on vehicle %s has fresh data (%.1f min old), not zeroed",
                        metric_name,
                        vehicle_id,
                        time_since_update.total_seconds() / 60,
                    )
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

    def cleanup_old_data(self, keep_hours: int = 24) -> None:
        """Clean up old zeroed metrics to prevent memory growth.

        Args:
            keep_hours: Number of hours to keep zeroed metric data
        """
        try:
            # Use UTC for internal timestamps
            now = datetime.now(UTC)

            # Remove old zeroed metrics that haven't been updated recently
            old_metrics = [
                key
                for key, time in self._zeroed_metrics.items()
                if now - time > timedelta(hours=keep_hours)
            ]

            for key in old_metrics:
                del self._zeroed_metrics[key]

            if old_metrics:
                _LOGGER.debug(
                    "Cleanup complete: removed %d old zeroed metrics",
                    len(old_metrics),
                )

        except Exception as e:
            _LOGGER.error(
                "Error during auto-zero cleanup: %s",
                str(e),
                exc_info=True,
            )

    def is_metric_zeroed(self, vehicle_id: str, metric_id: str) -> bool:
        """Check if a metric is currently marked as zeroed.

        Args:
            vehicle_id: Vehicle ID
            metric_id: Metric field ID

        Returns:
            True if the metric is currently zeroed, False otherwise
        """
        metric_key = (vehicle_id, metric_id)
        is_zeroed = metric_key in self._zeroed_metrics

        if is_zeroed:
            zeroed_at = self._zeroed_metrics[metric_key]
            age_minutes = (
                datetime.now(zeroed_at.tzinfo or UTC) - zeroed_at
            ).total_seconds() / 60
            _LOGGER.debug(
                "is_metric_zeroed check: %s on vehicle %s IS ZEROED (zeroed %.1f minutes ago)",
                AUTO_ZERO_METRICS.get(metric_id, metric_id),
                vehicle_id,
                age_minutes,
            )
        else:
            _LOGGER.debug(
                "is_metric_zeroed check: %s on vehicle %s NOT ZEROED",
                AUTO_ZERO_METRICS.get(metric_id, metric_id),
                vehicle_id,
            )

        return is_zeroed

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

        # No more cooldown tracking

        return status


# Global instance
_auto_zero_manager: AutoZeroManager | None = None


def get_auto_zero_manager() -> AutoZeroManager:
    """Get the global auto-zero manager instance."""
    global _auto_zero_manager
    if _auto_zero_manager is None:
        _auto_zero_manager = AutoZeroManager()
    return _auto_zero_manager
