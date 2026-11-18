# AutoPi Home Assistant review guide

## What this is

Home Assistant users install this integration to follow vehicle telemetry reported by AutoPi. It updates entities for vehicle data, status and location.

## Invariants

- The API returns field values without units. Keep fields raw until there is evidence for a conversion. Give any conversion a named constant, documented provenance and a test.
- Declare the unit in the entity initializer and convert in `native_value`. Check the device and state class pair against the pinned Home Assistant behavior.
- Keep discovery and readings associated with the correct configured vehicle. Preserve the distinction between a missing field, zero and an available location fallback.

## Changes to scrutinize

- In `client.py` and `coordinator.py`, preserve the API token contract and configured fast polling interval. Check retries and partial results against the correct endpoint and vehicle.
- In sensor and tracker changes, check scaling, availability, unit and class together. Review missing telemetry and the position fallback alongside the common case.
- Keep tokens out of logs and errors. Use structural fixtures and keep real vehicle identifiers and coordinates out of public evidence. Regenerate the entity reference when entity declarations change.

## Findings already covered by CI

Formatting, Ruff, Bandit, mypy and pytest already cover standard checks. Review whether the observed entity values and metadata remain correct for supported Home Assistant versions.

## Verification

Run `just check` for the local gate. Hosted CI also runs Hassfest and HACS validation. `just docgen` regenerates the entity reference. Keep observed vehicle data separate from public fixture evidence.
