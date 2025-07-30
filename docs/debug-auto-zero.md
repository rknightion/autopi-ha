# Auto-Zero Debug Logging Guide

This document explains the debug logging added to track auto-zero behavior in real-time.

## Enable Debug Logging

Add this to your `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.autopi: debug
```

## Log Tags and What They Mean

### Initialization Phase

- **`[AUTO-ZERO INIT]`** - Auto-zero manager initialization
  - Shows when the manager starts and whether auto-zero is enabled
  - Shows how many metrics are being restored from storage

- **`[SENSOR INIT]`** - Individual sensor creation
  - Shows each sensor being created and whether it supports auto-zero

### Startup/Restoration Phase

- **`RESTORED`** - A previously zeroed metric was restored from storage
  - Shows the metric name, vehicle, and how long ago it was zeroed
  
- **`SKIPPED`** - A stored zero state was too old (>24 hours) and not restored
  - Prevents ancient zero states from persisting forever

### Runtime Evaluation Phase

- **`[SENSOR AUTO-ZERO]`** - Sensor-level auto-zero checks
  - Shows when a sensor checks if it should be zeroed
  - Special note: "STARTUP PROTECTION" means preventing stale data on HA restart

- **`[SENSOR DATA]`** - Raw sensor data
  - Shows the actual value and age of data from the API
  
- **`[AUTO-ZERO EVAL]`** - Auto-zero manager evaluation
  - Shows the age of data vs. the 15-minute threshold
  - Shows whether the metric is currently zeroed

- **`is_metric_zeroed check`** - Quick check if a metric is already zeroed
  - Used during startup to prevent showing stale data

### Action Phase

- **`[AUTO-ZERO ACTION] ZEROING`** - Metric is being zeroed
  - Shows when data crosses the 15-minute threshold
  
- **`[AUTO-ZERO ACTION] UN-ZEROING`** - Metric is being restored
  - Shows when fresh data arrives (≤15 minutes old)

- **`[AUTO-ZERO UPDATE]`** - Updates to already-zeroed metrics
  - Shows when a zeroed metric gets new (but still stale) data

### Storage Phase

- **`[AUTO-ZERO SAVE]`** - Persistence operations
  - Shows when state is saved to disk
  - Lists all metrics being saved

## Example Log Flow

### Scenario 1: Home Assistant Startup with Stale Data

```
[AUTO-ZERO INIT] Initializing auto-zero manager
[AUTO-ZERO INIT] Auto-zero manager initialized, auto_zero_enabled=True
Processing 3 zeroed metrics from storage
RESTORED zeroed state for Engine RPM (OBD) on vehicle 123 (zeroed 0.5 hours ago)
[SENSOR INIT] Created sensor Engine RPM for vehicle 123 (field_id: obd.rpm.value, auto-zero capable: True)
[SENSOR AUTO-ZERO] Checking Engine RPM on vehicle 123: auto_zero_enabled=True
is_metric_zeroed check: Engine RPM (OBD) on vehicle 123 IS ZEROED (zeroed 30.0 minutes ago)
[SENSOR AUTO-ZERO] Engine RPM for vehicle 123 is marked as zeroed and no data available, returning 0 (STARTUP PROTECTION)
```

### Scenario 2: Data Becoming Stale

```
[SENSOR DATA] Engine RPM for vehicle 123 has value 0 (last_seen: 2025-01-15T10:00:00, age: 16.5 min)
[AUTO-ZERO EVAL] Engine RPM (OBD) on vehicle 123: last_seen 16.5 min ago (threshold 15 min), currently zeroed: False
[AUTO-ZERO ACTION] ZEROING Engine RPM (OBD) for vehicle 123 - data is 16.5 minutes old (threshold: 15 min)
[AUTO-ZERO SAVE] Scheduling save operation with 1 zeroed metrics
[SENSOR AUTO-ZERO] RETURNING 0 for Engine RPM on vehicle 123 (auto-zero applied)
```

### Scenario 3: Fresh Data Arriving

```
[SENSOR DATA] Engine RPM for vehicle 123 has value 850 (last_seen: 2025-01-15T10:20:00, age: 2.1 min)
[AUTO-ZERO EVAL] Engine RPM (OBD) on vehicle 123: last_seen 2.1 min ago (threshold 15 min), currently zeroed: True
[AUTO-ZERO ACTION] UN-ZEROING Engine RPM (OBD) for vehicle 123 - fresh data received (2.1 minutes old)
[SENSOR AUTO-ZERO] Engine RPM on vehicle 123 NOT zeroed, returning actual value 850
```

## Troubleshooting with Logs

### Issue: Sensor shows stale value on startup

Look for:
- Missing `[SENSOR AUTO-ZERO] ... STARTUP PROTECTION` log
- Check if `is_metric_zeroed check` shows the metric as zeroed
- Verify `RESTORED` log shows the metric was loaded from storage

### Issue: Sensor not zeroing when expected

Look for:
- `[AUTO-ZERO EVAL]` to see the actual age vs. threshold
- Check if auto_zero_enabled=True in the logs
- Verify the field_id is in the auto-zero capable list

### Issue: Sensor zeroing too quickly

Look for:
- `[SENSOR DATA]` to see the actual last_seen timestamp
- The age calculation might show the data is older than expected
- Check your AutoPi device's reporting frequency

## Performance Note

These debug logs are verbose and should only be enabled when troubleshooting. Disable debug logging for normal operation to reduce log size.