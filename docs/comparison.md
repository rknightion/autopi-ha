---
title: When to Use This
description: When the AutoPi Home Assistant integration is the right tool, when the AutoPi dashboard or a generic integration serves you better
---

# When to Use This

This page is about deciding whether this integration is the right fit, not about scoring it
against alternatives. It describes what this integration does and does not do; where it would be
guessing about a third-party product, it says so and stops rather than making a claim it can't
back up.

## What this integration is

A Home Assistant custom integration (HACS or manual install) that polls the **AutoPi cloud API**
for vehicles on your AutoPi account and exposes them as Home Assistant devices and entities - a
device tracker per vehicle, GPS position sensors, dozens of OBD/telemetry data field sensors
created dynamically from whatever fields a given vehicle reports, integration health diagnostics,
and event entities. See the [Entity Reference](entities.md) for the full list.

It requires:

- An AutoPi account with at least one AutoPi device already installed in a vehicle.
- An API token with vehicle read access.
- Home Assistant with outbound internet access - it's `cloud_polling`, there is no local/offline
  mode.

It is read-only: it fetches data, it does not send commands to the vehicle or device (see
[Security](security.md#read-only-operation)).

## When to use it

- **You already have an AutoPi device** and want its data inside Home Assistant - device trackers
  on the map, sensors in dashboards, and vehicle state available to automations and scripts.
- **You want vehicle data to drive Home Assistant automations** - arrival/departure detection,
  charging state, engine/ignition state, DTC alerts - rather than checking a separate app.
- **You're fine with cloud polling.** Data freshness is bounded by your configured update interval
  (1-10 minutes) and by AutoPi's own reporting behavior for the device, not by anything faster.

## When not to

- **You don't have an AutoPi device.** This integration only surfaces data that already exists in
  an AutoPi account; it has no way to talk to a vehicle directly, and installing an AutoPi device
  purely to get Home Assistant integration is a hardware and account decision this page can't make
  for you.
- **You need write/control operations** (locking, remote commands, configuration changes on the
  device). This integration doesn't do that at all - see
  [Security](security.md#read-only-operation).
- **You need it to work without internet, or without AutoPi's cloud being up.** There's no local
  mode; an AutoPi or Home Assistant connectivity outage means stale or unavailable entities until
  it clears.
- **You only need to glance at one vehicle occasionally.** If Home Assistant automation isn't the
  goal, checking the AutoPi account directly at [app.autopi.io](https://app.autopi.io) - where the
  API token itself is generated - is one less moving part. This page can't say what that dashboard
  does or doesn't offer beyond what's already referenced elsewhere in this documentation, since
  that's AutoPi's product to describe, not this integration's.

## Other ways to get vehicle data into Home Assistant

Home Assistant has other integrations in the vehicle-tracking and OBD-II space, generically. This
page doesn't compare against any of them by name or claim what they do or don't support - that
would mean asserting things about code this repository doesn't own. If you're evaluating options,
the questions this page above answers (do you already have an AutoPi device, do you need
control/write access, do you need it to work offline) are the ones worth asking of any alternative
too.

## See also

- [Entity Reference](entities.md) - the full list of entities this integration creates
- [Security](security.md) - credentials, data flow, and read-only guarantees
- [FAQ](faq.md) - feature scope and current limitations
