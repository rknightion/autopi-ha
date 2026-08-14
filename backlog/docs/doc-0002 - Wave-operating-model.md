---
id: doc-0002
title: Wave operating model
type: guide
created_date: '2026-08-14 16:07'
updated_date: '2026-08-14 16:08'
---
This document carries **only what is specific to `autopi-ha`**. The campaign model itself — run
contract and run modes, the routing contract, authority and the thread pool, append-only registry
contention, the child lane brief, external-contract freezing, the unattended blocker contract, the
goal-file template, the pre-flight checklist — is the **Agent fan-out protocol (canonical)** doc.
Read that first. Nothing here restates it; if a section below could be pasted into another project
unchanged, it is in the wrong document.

## 1. Rules this project added, and the failure that caused each

### R1 — a unit is an inference, and the inference must be written where a bug report can land

The AutoPi API **returns no unit for any data field.** `/logbook/storage/data_fields/` resolves to
the OpenAPI `Field` definition, whose whole surface is `display_name, pretty_name, field_prefix,
field, field_name, frequency, type, title, last_seen, last_value, description` — and `last_value` is
an untyped object. Units exist in the spec only on `PIDDetail` (`unit`, `formula`, `min`, `max`) and
`DataParameter` (`unit`, `multiplier`), which live behind `/obd/pids/` and `/can_logging/pids/` and
are not called by this integration. **The scaling cannot be keyed off anything the integration
receives**, so it is a standing inference, not a temporary gap.

The failure (#378): a `0.1 kWh` scaling for `obd.oem_hv_battery_measured_energy.value` was derived
from one contributor's vehicle and registered for every vehicle reporting the field. A vehicle whose
PID reports whole kWh reads 10× low, and there is no runtime fix available.

So: put the conversion behind a **named constant**, state its **provenance and its failure mode in
the docstring**, and **pin the assumption with a test** — a wrong unit then has somewhere to land
when a user reports it. Where there is no evidence at all, register **raw passthrough** — no unit, no
device class, no state class — rather than guessing. #378 did exactly that for
`obd.oem_hv_battery_lifetime_power_use` and `_charge_power`, because a guessed unit on a
`TOTAL_INCREASING` series writes wrong long-term statistics that are painful to unpick.

### R2 — declare the unit in `__init__`, convert in `native_value`, never override the property

The failure (#379): `TotalOdometerSensor` passed `unit_of_measurement=UnitOfLength.METERS` while its
`native_unit_of_measurement` property returned `KILOMETERS`; `GSMSignalSensor` passed no unit while
its property returned `PERCENTAGE`. **The property wins** for HA and for `scripts/generate_docs.py`,
so nothing was user-visible and the contradiction survived review — but the attribute is public and
anything reading it directly got the wrong answer.

`TripOdometerSensor` is the shape to copy: declare in `__init__`, convert in `native_value`, no
property override.

### R3 — check the device_class/state_class pair against the pinned HA, not from memory

The failure (#378): `HVBatteryEnergySensor` was registered `SensorDeviceClass.ENERGY` +
`SensorStateClass.MEASUREMENT`, which HA rejects — `energy → {total, total_increasing}`,
`energy_storage → {measurement}`. It logged *on every startup* and recorded the wrong semantics into
long-term statistics. Remaining stored energy is `ENERGY_STORAGE`; both classes accept kWh.

Read the permitted pair out of the installed package rather than recalling it. Pinned at the time of
writing: **homeassistant 2026.8.1** (`uv.lock`). The pin moves; re-read it.

### R4 — `docs/entities.md` is generated and is NOT CI-enforced

`scripts/generate_docs.py` derives it from `FIELD_ID_TO_SENSOR_CLASS`. **Nothing in
`.github/workflows/` or `.pre-commit-config.yaml` runs it** — verified 2026-08-14. A lane that adds a
sensor and does not regenerate ships a green build with stale published docs, which is how #378 §4
happened.

`make docgen` (`uv run python scripts/generate_docs.py`). This is a **wave-level wiring step, not a
lane's own gate**, because the file is a shared derived artefact — see §4. In sync as of 2026-08-14.

### R5 — an unreported field costs nothing, so the bar for adding one is evidence about its unit

`sensor.py` builds `available_fields` dynamically from coordinator data, so a registered field that
a vehicle never reports simply produces no entity. That removes the usual reason to hold a
speculative field back — which means the question to answer before registering is never "does some
vehicle have this", it is R1's question: what is the unit, and what is the evidence.

### R6 — the local gate does not cover everything CI checks

`definition_of_done` carries the three commands a lane can run (`ruff check`, `mypy`, `pytest`), all
via `uv run` — never a bare `python`/`pytest`. CI additionally runs **hassfest** and **HACS
validation**, which have no local equivalent here. A lane touching `manifest.json`, `hacs.json` or
the integration's directory layout cannot prove itself green locally; say so in its notes rather
than claiming a full gate.

## 2. Recurring defects in this codebase

Every one of the above is a **units-and-classes** defect, and that is the pattern: this integration's
risk is concentrated almost entirely in the sensor metadata layer, not in its I/O. Two of the three
2026-08-08 issues were found by *post-merge review of another change* (#379 was spotted while
reviewing #377), which is the tell — these defects survive the gate because they are green.

Size is where they hide. `coordinator.py` 2060 lines, `data_field_sensors.py` 1568, `sensor.py` 983,
`client.py` 881, `types.py` 725. Three of those five are exactly what a sensor-adding wave touches.

Contributor-reported fields (#376, an external contributor) arrive as **field names with no units and
no sample values**. Treat that as an R1 input, not as a spec.

## 3. The exclusive resource: the live AutoPi account

There is one real API token, one real fleet, a third-party rate limit, and — decisively — **the
account's data is precisely the PII the tracker rules forbid** (see `AGENTS.md`).

- **At most one lane per wave may make live API calls**, and the goal file must name it.
- Every other lane works from fixtures under `tests/`. A lane needing a new sample **requests it from
  the live lane**; it does not authenticate itself.
- The live lane redacts before anything leaves it: `<device-uuid>`, `<vehicle-id>`, shapes not
  instances.

This repo has already paid for that rule the expensive way. `todos.txt` carried a live `APIToken`, a
device UUID and home GPS coordinates, and was committed to a **public** repo — where deleting the
file does not unpublish it. The file is gone and the token was rotated; the rule is what remains.

## 4. Ownership conventions and the escape hatch

One file, one lane, as usual. What is specific here is which files are **wiring-only** — edited by the
wiring pass alone, never by a lane, because concurrent appends to them is the contention case:

| Wiring-only | Why |
|---|---|
| `FIELD_ID_TO_SENSOR_CLASS` — `custom_components/autopi/data_field_sensors.py:1493` | append-only registry |
| `POSITION_FIELD_TO_SENSOR_CLASS` — `custom_components/autopi/position_sensors.py:230` | append-only registry |
| `AUTO_ZERO_METRICS` — `custom_components/autopi/auto_zero.py:41` | append-only registry |
| `PLATFORMS` — `custom_components/autopi/const.py:43` | append-only registry |
| `docs/entities.md` | derived — regenerate with `make docgen`, never hand-edit |
| `manifest.json`, `hacs.json` | one hassfest/HACS surface, no local gate (R6) |

Note the first four are **blocks inside otherwise lane-owned files**. A lane writes its sensor class
into `data_field_sensors.py` and stops at the registry: the wiring pass adds the row. That keeps the
one-owner rule intact without freezing a 1568-line file behind a single lane.

**The escape hatch**: a lane that finds it needs a change outside its map does not edit it and does
not stop. It records the exact change it needs with `backlog task edit APH-NNNN --append-notes`,
finishes everything else in its scope, and only then sets `Parked` with the boundary named. The
wiring pass applies the recorded change.

## 5. Run-end against this tracker

Prefix `aph` → `APH-0001`. Statuses `To Do` → `In Progress` → `Parked` → `Done`. Every new task
inherits the three gate commands as acceptance criteria from `definition_of_done`.

- **Landed** — one call, so an interruption cannot leave it half-finalized:
  `backlog task edit APH-0007 --check-ac 1 --check-ac 2 -s Done`, with the commit SHA in the final
  summary.
- **Parked** — `-s Parked` plus a resume boundary concrete enough that a session with no memory of
  the run can restart from it.
- **Untouched** — left `To Do`. It is self-evident; do not annotate it.
- **Discovered** — a new task labelled `needs-triage`. Not a note on an unrelated task.
- **Archaeology** — closed pre-tracker work belongs in the *Closed GitHub issues index* doc, never as
  new `Done` tasks. Backlog IDs follow creation order and can never be made to match a `#NNN` already
  cited in `CHANGELOG.md` or a commit message, so importing them would create a second ID space over
  the same history.

The run's closing message is a terminal action, not a reply to a request: it goes to the terminal and
carries only **what the run learned that no single task captures**. Nothing durable may live only
there.
