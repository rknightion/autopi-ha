# autopi-ha

Home Assistant custom integration for the AutoPi cloud platform. Public repo, distributed through
HACS as a zip release.

## Task interface

`just check` is the local gate. It is not the whole gate: CI additionally runs Home Assistant
`hassfest` and HACS validation, neither of which has a local recipe, and both of which can fail a
change that passed `just check`.

`just clean` is `[confirm]`. Never pass `--yes` or `JUST_YES=1` to work around a confirm prompt.

A `pre-commit` hook runs the whole pytest suite whenever a Python file is staged, so a one-line
code change pays for the full run.

## This is a public repo carrying real vehicle data

Issues, pull request bodies, `docs/`, `.github/tracker/` and every instruction file here are public. Never write a real AutoPi API
token, device UUID, vehicle id, VIN, registration plate, GPS coordinate, email address or account
id into any of them - including as an illustrative example. Write the shape instead:
`<device-uuid>`, `<vehicle-id>`, "the second vehicle on the account". Aggregate counts, field
names, response *shapes* and structural findings are fine.

Sweep before committing:

```bash
grep -rniE "APIToken +[0-9a-z]{16,}|[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}|(vehicle|device)_id=[0-9a-f]|-?[0-9]{1,3}\.[0-9]{5,}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}" docs/ .github/tracker/ && echo "PII FOUND"
```

## AutoPi API

- Auth header is `Authorization: APIToken <key>`. Not `Bearer`, not `Token`.
- Every endpoint path lives as a `Final` constant in `const.py`. Add new ones there; do not inline a
  path at the call site.
- Exactly one polling interval is user-configurable: `update_interval_fast`, surfaced in the options
  flow under the field name `polling_interval`, clamped to `MIN_SCAN_INTERVAL_MINUTES` ..
  `MAX_SCAN_INTERVAL_MINUTES`. `update_interval_medium` and `update_interval_slow` exist only in
  test fixtures - the coordinator reads neither, and `test_update_interval_from_options` asserts
  that it ignores them. Do not treat them as config keys.
- The integration force-sets the `aiohttp` logger to `ERROR` with `propagate = False` unless
  `custom_components.autopi` itself is at DEBUG. Raising Home Assistant's global log level alone
  will not make aiohttp talk.

## Generated documentation

`docs/entities.md` is generated from the entity classes by `just docgen`. Hand edits to it are
overwritten. Nothing in CI or pre-commit regenerates it, so a change to entity definitions needs
`just docgen` run and committed by hand.

## Tracking work

Work is tracked in this repository's GitHub issues; they are the only queue. Do not add a checklist
file such as `ROADMAP.md` beside them.

- A pull request body says how it relates to an issue, on a line of its own: `Closes #N` with the
  `Acceptance evidence` table from `.github/pull_request_template.md` (one row for each acceptance
  criterion of that issue), `Refs #N` when it only relates to one, or `Task: none, <reason>`.
- A pull request that changes `.github/workflows/` or `.github/actions/` carries no closing keyword:
  write `Task: none, <reason>`, with `Refs #N` beside it if you like.
- Contributors never need the project board or the tracker tooling; a maintainer handles both.
- Issues and pull requests are public, so they carry no real identifiers: no AutoPi token, device
  UUID, vehicle id, VIN, plate, coordinate or email address. Write the shape, not the instance.
- Older commits, docs and tests cite legacy board ids such as `APH-0001`. `just issue <ID>` prints
  the issue each one became; `.github/tracker/id-map.json` is the map, and the retired board's
  documents are kept under `.github/tracker/history/`. Pre-tracker GitHub issues stay where they were.

## Deeper references

- `autopi-api-combined.md` - read before adding an endpoint or a new metric source; it is the
  endpoint and response-shape survey the integration was built from.
- `docs/api-optimization.md` - read before changing polling, caching or which entities are created
  by default; AutoPi API call volume is the cost driver here.
- `docs/auto-zero-metrics.md` - read before touching `auto_zero.py` or any staleness or zeroing
  behaviour on telemetry sensors.
- `docs/naming-conventions.md` - read before changing entity or device naming; renames break users'
  automations and dashboards.
