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

`backlog/`, `docs/` and every instruction file here are published. Never write a real AutoPi API
token, device UUID, vehicle id, VIN, registration plate, GPS coordinate, email address or account
id into any of them - including as an illustrative example. Write the shape instead:
`<device-uuid>`, `<vehicle-id>`, "the second vehicle on the account". Aggregate counts, field
names, response *shapes* and structural findings are fine.

The repo has already been burned: the now-deleted `todos.txt` carried a live `APIToken`, a device
UUID and home coordinates into public git history, where deleting the file does not unpublish them.

Sweep before committing:

```bash
grep -rniE "APIToken +[0-9a-z]{16,}|[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}|(vehicle|device)_id=[0-9a-f]|-?[0-9]{1,3}\.[0-9]{5,}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}" backlog/ docs/ && echo "PII FOUND"
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

## Tracker

Work is tracked in `backlog/`. Run `backlog instructions overview` before acting on tracker work;
`backlog instructions task-creation|task-execution|task-finalization` carry the lifecycle detail.
Read the **Agent fan-out protocol (canonical)** doc before designing a wave, and the **Wave
operating model** doc for this repo's own conventions. Closed pre-tracker GitHub issues are indexed
in the **Closed GitHub issues** doc, which is a pointer - the issues themselves are still live on
GitHub.

- **Never use `--notes` or `--plan` bare.** They *silently replace* the whole section, an open
  upstream bug that destroys another session's writes with no warning. Use `--append-notes` and
  `--append-plan`. A hook in the agent config denies the bare forms; do not work around it.
- Finalize in one call so an interrupted session cannot leave finished work looking unfinished:
  `backlog task edit APH-0007 --check-ac 1 --check-ac 2 -s Done`.
- Section boundaries in tracker markdown are HTML-comment markers. Break one and the section is
  *silently dropped*, exit code 0, with the data still in the file but invisible until the next
  write destroys it. There is no repair command; `backlog doctor` only fixes duplicate task ids.
- `backlog/config.yml` is the one file that must be hand-edited: list-valued keys cannot be set
  through `backlog config set`.
- Two sessions must never edit the same task. v1.50.x fixed the lost-write race in the edit funnel
  but not in reorder, draft saves, the TUI edit path, `doc update` or decision updates.

## Deeper references

- `autopi-api-combined.md` - read before adding an endpoint or a new metric source; it is the
  endpoint and response-shape survey the integration was built from.
- `docs/api-optimization.md` - read before changing polling, caching or which entities are created
  by default; AutoPi API call volume is the cost driver here.
- `docs/auto-zero-metrics.md` - read before touching `auto_zero.py` or any staleness or zeroing
  behaviour on telemetry sensors.
- `docs/naming-conventions.md` - read before changing entity or device naming; renames break users'
  automations and dashboards.
