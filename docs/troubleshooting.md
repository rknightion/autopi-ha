---
title: Troubleshooting
description: Diagnosing config flow failures, auth errors, missing entities, stale data, and Auto-Zero problems in the AutoPi integration
---

# Troubleshooting

If nothing here matches what you are seeing, check the [FAQ](faq.md), search
[existing GitHub issues](https://github.com/rknightion/autopi-ha/issues), or
[file a bug report](https://github.com/rknightion/autopi-ha/issues/new) with your Home Assistant
version, the integration version, and the relevant log lines (see
[Reading the logs](#reading-the-logs) below).

## Setup and config flow

### "Failed to connect to AutoPi API"

The config flow shows this when the initial connection test to the AutoPi API fails before it can
even check the key.

1. Confirm Home Assistant has outbound internet access - the integration is `cloud_polling`; it has
   no local mode and cannot work offline.
2. If you set a custom **Base URL** during setup, check it's reachable and correct. Leave it blank
   to use the default `https://api.autopi.io`.
3. Retry - transient AutoPi API outages surface as this same error.

### "Invalid API key"

The config flow's authentication test received a `401` from the AutoPi API.

1. Regenerate the token at [app.autopi.io](https://app.autopi.io) under **Account Settings** →
   **API Tokens** and paste the new value in exactly - no surrounding whitespace.
2. Confirm the token hasn't expired or been revoked from the AutoPi dashboard.

### "No vehicles found in your AutoPi account"

The API key is valid but the vehicle profile endpoint returned no vehicles, so the config flow
aborts rather than creating an entry with nothing to monitor.

1. Check the vehicle is actually registered and visible in the AutoPi dashboard.
2. Check the token's permissions include vehicle read access - a token scoped away from vehicles
   authenticates fine but sees nothing.

### "AutoPi is already configured"

Only one config entry is created per AutoPi account setup. If you need a second account, add a
second integration instance with its own API token rather than reusing the first.

### "Unexpected error"

Anything not classified as a connection or auth failure falls through to this generic error.
Enable [debug logging](#reading-the-logs) and retry setup - the traceback in the log is the actual
cause; the config flow only shows the generic message to the UI.

## Authentication during normal operation

### Integration prompts for reauthentication

When a request gets a `401` after setup, the coordinator logs `Authentication failed: Invalid API
key` and Home Assistant raises a reauth flow rather than silently failing. This means the token
was revoked, expired, or regenerated in the AutoPi dashboard after setup.

1. Follow the reauth prompt under **Settings → Devices & Services** and paste a fresh token.
2. Vehicle selection and all other options are preserved across reauth - you are only replacing
   the key.

### "Integration stops updating after some time"

Usually one of:

1. **Token expired or was regenerated** - triggers the reauth flow above; check for a reauth
   notification before assuming something else is wrong.
2. **AutoPi API unreachable** - check Home Assistant's outbound connectivity and the AutoPi service
   status.
3. Check the diagnostic sensors (`sensor.autopi_api_calls`, `sensor.autopi_failed_api_calls`,
   `sensor.autopi_api_success_rate`) for a drop in success rate rather than guessing.

## Entities missing or unavailable

### A vehicle never appeared during setup

Vehicle selection only lists vehicles the AutoPi API returned for that account. If a vehicle is
missing from the selection list:

- Confirm it's registered and online in the AutoPi dashboard.
- Confirm the API token has vehicle read access.

### Entities show "unavailable"

Entity availability tracks the underlying vehicle/API state, not a fixed timeout. Check for:

- The vehicle hasn't reported data recently (device offline, ignition-gated reporting mode).
- The AutoPi API was unreachable on the last update - check
  `sensor.autopi_api_success_rate` and `sensor.autopi_update_duration`.
- A pending reauth (see above) - a stale token makes every entity unavailable at once, not just
  one vehicle's.

### Only some data field sensors exist for a vehicle

Data field sensors (see [Entity Reference](entities.md)) are created dynamically from the
telemetry fields a vehicle actually reports. A vehicle without OBD wiring for a given PID, or an EV
without HV battery telemetry, simply never creates the corresponding sensor - this is expected, not
a bug.

### GPS coordinates or speed look noisy while parked

GPS has inherent jitter and can report small non-zero speeds (0.1-0.5 m/s) or drifting
latitude/longitude while stationary. Use a threshold above the noise floor in automations rather
than treating any non-zero value as movement. **Accelerometer X/Y/Z** sensors specifically have a
**Suppress Accelerometer When Stationary** option (enabled by default) that stops updating those
three sensors while the vehicle is detected as stationary, to prevent this jitter from triggering
automations.

## Stale or zeroed values

This integration's data is a snapshot from the last successful poll, not a push feed - "stale"
means the `last_seen` age on the underlying telemetry field is old, and "zeroed" is a specific
optional behavior layered on top of that. Two different pages own the mechanics in detail:

- [Auto-Zero Metrics (BETA)](auto-zero-metrics.md) - what gets zeroed, when, and why.
- [Auto-Zero Debug Logging](debug-auto-zero.md) - the log tags to read when auto-zero isn't doing
  what you expect.

Quick triage before diving into those pages:

### A metric reads 0 unexpectedly

1. Check whether **Auto-zero Metrics (BETA)** is enabled in the integration options. If it's off,
   a sensor reading exactly 0 is real vehicle data, not auto-zero - go check the vehicle/AutoPi
   dashboard instead.
2. If it's on, only the metrics listed in [Auto-Zero Metrics](auto-zero-metrics.md#affected-metrics)
   are eligible - engine OBD metrics, GPS-calculated fuel used, and the X/Y/Z accelerometer axes.
   Anything else reading 0 is not an auto-zero effect.
3. The threshold is fixed at 15 minutes and is not configurable. If the metric's `last_seen` is
   older than that, zeroing is expected behavior, not a fault.

### A metric won't zero even though the vehicle has been off for a while

1. Confirm auto-zero is enabled and the metric is in the affected list (above).
2. Confirm your **Update Interval** is 1-10 minutes - the integration enforces this range, and
   the feature needs a short interval to catch staleness promptly. 5-10 minute intervals make
   auto-zero markedly less responsive; 1 minute is required for it to behave predictably.
3. Enable debug logging and look for `[AUTO-ZERO EVAL]` entries, which log the data age against the
   15-minute threshold directly - see [Auto-Zero Debug Logging](debug-auto-zero.md).

### A metric zeroes right after a Home Assistant restart even though it was fine before

This is the state-restoration path: a metric that was zeroed before restart stays zeroed until
fresh data arrives, specifically to avoid briefly showing pre-restart stale data as if it were
current. Look for `RESTORED` in the log - if a stored zero state is more than 24 hours old it is
deliberately **not** restored (logged as `SKIPPED`) rather than persisting forever.

## Polling interval and rate limits

### Options won't save / "Update Interval" rejected

The **Update Interval** option only accepts 1-10 minutes. Values outside that range fail
validation in the options flow.

### Rate limited by the AutoPi API

A `429` from the AutoPi API is **not** retried automatically - it's logged as `Rate limit
exceeded` and surfaces as a failed update immediately, so a burst of rate limiting shows up as a
drop in `sensor.autopi_api_success_rate` right away rather than a delayed recovery. (Server errors
and connection failures *are* retried - up to 3 attempts with a short linear backoff - but rate
limiting is not one of those cases.) If you're hitting this often:

1. Increase **Update Interval** (fewer vehicles polled per minute).
2. Check `sensor.autopi_failed_api_calls` and `sensor.autopi_api_success_rate` to see whether
   failures are actually rate-limit related or something else (auth, connectivity).
3. Note the trade-off with [Auto-Zero Metrics](auto-zero-metrics.md): a short interval is what
   auto-zero needs, and is also what drives up call volume - see
   [API Optimization](api-optimization.md) for the interval trade-offs.

## Reading the logs

Enable debug logging in `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.autopi: debug
    custom_components.autopi.coordinator: debug
    custom_components.autopi.client: debug
```

The client logs the HTTP method and endpoint (not the full URL, to avoid leaking the base URL) and
the response status for every request, and explicitly filters `api_key`/`token` out of any logged
request parameters. It does not filter sensor values, so debug logs for position and telemetry
sensors will contain the actual data - including GPS coordinates - while enabled. See
[Security](security.md#logging) before sharing debug logs publicly.
