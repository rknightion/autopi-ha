# Auto-Zero Metrics (BETA)

## Overview

The Auto-Zero Metrics feature is a **BETA** functionality that automatically sets certain vehicle metrics to zero when the data becomes stale (older than 15 minutes). This prevents outdated sensor values from being displayed for extended periods when the vehicle is parked or turned off.

## ⚠️ BETA Warning

This feature is currently in BETA and may not work correctly in all scenarios. Please report any issues you encounter.

## How It Works

### Simple Time-Based Detection

The integration monitors each metric's `last_seen` timestamp from the AutoPi API:

1. **Staleness Check**: On every update, checks if each metric's `last_seen` is older than 15 minutes
2. **Automatic Zeroing**: If data is stale (> 15 minutes old), the metric is set to zero
3. **Automatic Recovery**: When fresh data arrives (≤ 15 minutes old), the metric automatically returns to showing the actual value
4. **No Complex Logic**: No trip detection, no consecutive call counting, just simple time comparison

### Update Interval Considerations

To ensure the auto-zero feature works reliably:
- **Maximum polling interval**: 10 minutes (enforced by the integration)
- **Recommended interval**: 1-5 minutes for best results
- **Why it matters**: With a 15-minute threshold, polling every 10 minutes ensures we catch stale data within 5-25 minutes

## Affected Metrics

The following sensors are affected by this feature when enabled:

- **Engine Metrics (OBD)**
  - Coolant Temperature
  - Engine Load
  - Engine RPM
  - Engine Run Time
  - Throttle Position
  - Vehicle Speed

- **GPS Metrics**
  - Fuel Used (GPS-calculated)

- **Acceleration Metrics**
  - X-Axis Acceleration
  - Y-Axis Acceleration
  - Z-Axis Acceleration

## Configuration

1. Navigate to **Settings** → **Devices & Services** → **AutoPi**
2. Click **Configure**
3. Enable **"Auto-zero Metrics (BETA)"**
4. Set your preferred **"Update Interval"** (1-10 minutes)
5. Click **Submit**

The feature is **disabled by default** to ensure existing behavior is maintained.

## Behavior Details

### When Metrics Are Zeroed

- The metric's `last_seen` timestamp is older than 15 minutes
- The auto-zero feature is enabled
- The metric is in the affected metrics list

### When Metrics Return to Normal

- Fresh data arrives with a `last_seen` timestamp within 15 minutes
- The auto-zero feature is disabled

### State Persistence

The auto-zero feature includes state persistence to handle Home Assistant restarts:

- **Automatic State Restoration**: Zeroed metrics remain at zero after HA restarts
- **Storage of Zeroed Status**: Each zeroed metric's state is saved to disk
- **Graceful Recovery**: If storage files are corrupted or missing, the system logs a warning and starts fresh
- **Per-Entity Tracking**: Each metric is tracked individually - one metric's stale data won't affect others

This ensures that even if Home Assistant is down for extended periods, sensors won't briefly show stale values before re-zeroing.

## Limitations

1. **API Update Frequency**: Effectiveness depends on how frequently your AutoPi device reports data
2. **15-Minute Threshold**: Fixed at 15 minutes - not configurable
3. **Beta Status**: Edge cases may exist that aren't properly handled

## Entity Attributes

### Auto Zero Enabled Indicator

All sensors (except device tracker and event entities) now include an `auto_zero_enabled` attribute that indicates whether the auto-zero functionality is available for that specific sensor:

- **`auto_zero_enabled: true`** - The sensor supports auto-zero functionality (appears on sensors listed in "Affected Metrics" above)
- **`auto_zero_enabled: false`** - The sensor does not support auto-zero functionality

This attribute appears regardless of whether the auto-zero feature is enabled in the integration configuration. It simply indicates whether the sensor *could* be auto-zeroed if the feature were enabled.

For sensors with `auto_zero_enabled: true` and the feature enabled in configuration, additional attributes will appear:
- `is_zeroed` - Whether the sensor is currently showing a zeroed value
- `zeroed_at` - Timestamp when the sensor was last zeroed (if it has been zeroed)

## Troubleshooting

### Metrics Not Zeroing

1. Verify the feature is enabled in configuration
2. Check that the metric's `last_seen` is actually older than 15 minutes
3. Ensure affected sensors have the `last_seen` attribute in their state

### Metrics Zeroing Too Quickly/Slowly

1. Adjust your polling interval - shorter intervals detect stale data faster
2. Check if your vehicle is reporting data regularly
3. Consider disabling the feature if it's not working correctly for your use case

### Performance Impact

The feature adds minimal overhead as checks are performed only during regular data updates.

## Feedback

As this is a BETA feature, we welcome feedback and bug reports. Please include:

- Vehicle make/model
- Which metrics are affected
- Screenshots of sensor states and attributes
- Your polling interval setting

Report issues at: https://github.com/rknightion/autopi-ha/issues