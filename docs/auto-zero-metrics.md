# Auto-Zero Metrics (BETA)

## Overview

The Auto-Zero Metrics feature is a **BETA** functionality that automatically sets certain vehicle metrics to zero when the vehicle is not on an active trip. This prevents stale sensor values from being displayed for extended periods when the vehicle is parked or turned off.

## ⚠️ BETA Warning

This feature is currently in BETA and is based on assumptions about vehicle behavior and API data patterns. It may not work correctly in all scenarios. Please report any issues you encounter.

## How It Works

### Primary Method: Trip-Based Detection

The integration monitors your vehicle's trip status through the AutoPi API with robust validation:

1. **Consecutive Validation**: Requires 6 consecutive API calls returning "COMPLETED" status (6 minutes)
2. **Time Validation**: After 6 consecutive COMPLETED calls, verifies 5+ minutes have passed since trip completion
3. **Metric Staleness Check**: Confirms each metric's `last_seen` timestamp is older than 5 minutes
4. **Zero Application**: Only then are qualifying metrics set to zero
5. **Cooldown Period**: After a metric receives new data, it cannot be re-zeroed for 30 minutes

### Fallback Method: Consecutive Stale Readings

If trip data is unavailable, the fallback method is equally robust:

1. **Consecutive Tracking**: Monitors each metric individually for consecutive stale readings
2. **30 Consecutive Calls**: Requires 30 consecutive API calls (30 minutes) where the metric's `last_seen` hasn't changed
3. **Reset on Update**: If any new data arrives, the count resets to zero
4. **Same Cooldown**: 30-minute cooldown period applies after un-zeroing

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
4. **⚠️ IMPORTANT: Set "Update Interval" to 1 minute** - The auto-zero feature requires a 1-minute polling interval to function accurately
5. Click **Submit**

The feature is **disabled by default** to ensure existing behavior is maintained.

### Polling Interval Requirement

The auto-zero feature relies on detecting trip completion and monitoring metric staleness through consecutive API calls. With the default timing parameters:
- **6 consecutive calls** are required to confirm trip completion (6 minutes at 1-minute intervals)
- **30 consecutive calls** are required for the fallback method (30 minutes at 1-minute intervals)

If you set a longer polling interval (e.g., 5 minutes), these detection times multiply accordingly, making the feature much less responsive and potentially missing short stops.

## Behavior Details

### When Metrics Are Zeroed

- Vehicle completes a trip and remains stationary for 5+ minutes
- Metric data hasn't been updated by the vehicle
- The auto-zero feature is enabled

### When Metrics Return to Normal

- Vehicle starts a new trip
- Vehicle sends updated data for the metric
- The auto-zero feature is disabled

### Race Condition Prevention

The implementation includes comprehensive safeguards:

- **Consecutive Validation**: 6 consecutive COMPLETED calls required (prevents API glitches)
- **5-minute delay** after trip completion prevents premature zeroing during data upload
- **30-minute cooldown** after un-zeroing prevents rapid cycling
- **Per-metric evaluation** based on individual `last_seen` times
- **Immediate response** to trip state changes or new data
- **Memory cleanup** runs hourly to remove only data older than 24 hours

### State Persistence

The auto-zero feature includes state persistence to handle Home Assistant restarts:

- **Automatic State Restoration**: Zeroed metrics remain at zero after HA restarts
- **Storage of Zeroed Status**: Each zeroed metric's state is saved to disk
- **Graceful Recovery**: If storage files are corrupted or missing, the system logs a warning and starts fresh
- **Per-Entity Tracking**: Each metric is tracked individually - one metric's stale data won't affect others
- **Smart Un-zeroing**: When new data arrives from the API with a recent `last_seen` timestamp, metrics automatically un-zero

This ensures that even if Home Assistant is down for extended periods, sensors won't briefly show stale values before re-zeroing.

## Limitations

1. **Trip Data Dependency**: The primary method requires trip data to be available and accurate
2. **API Update Frequency**: Effectiveness depends on how frequently your AutoPi device reports data
3. **Beta Status**: Edge cases may exist that aren't properly handled

## Entity Attributes

### Auto Zero Enabled Indicator

All sensors (except device tracker and event entities) now include an `auto_zero_enabled` attribute that indicates whether the auto-zero functionality is available for that specific sensor:

- **`auto_zero_enabled: true`** - The sensor supports auto-zero functionality (appears on sensors listed in "Affected Metrics" above)
- **`auto_zero_enabled: false`** - The sensor does not support auto-zero functionality

This attribute appears regardless of whether the auto-zero feature is enabled in the integration configuration. It simply indicates whether the sensor *could* be auto-zeroed if the feature were enabled.

For sensors with `auto_zero_enabled: true` and the feature enabled in configuration, additional attributes will appear:
- `auto_zero_active` - Whether the sensor is currently showing a zeroed value
- `auto_zero_last_zeroed` - Timestamp when the sensor was last zeroed (if it has been zeroed)
- `auto_zero_cooldown_until` - Timestamp when the cooldown period expires (if in cooldown)

## Troubleshooting

### Metrics Not Zeroing

1. Verify the feature is enabled in configuration
2. Check that trip data is being received (Trip Count sensor should update)
3. Ensure affected sensors have the `last_seen` attribute in their state

### Metrics Zeroing Incorrectly

1. Check if the vehicle is actually on a trip
2. Verify the trip state in the vehicle's attributes
3. Consider disabling the feature if it's not working correctly for your use case

### Performance Impact

The feature adds minimal overhead as checks are performed only during regular data updates.

## Feedback

As this is a BETA feature, we welcome feedback and bug reports. Please include:

- Vehicle make/model
- Which metrics are affected
- Screenshots of sensor states and attributes
- Any patterns you notice

Report issues at: https://github.com/rknightion/autopi-ha/issues