---
id: APH-0001
title: Migrate the repo task surface to just and retire Makefiles and ad-hoc scripts
status: To Do
assignee: []
created_date: '2026-08-28 19:09'
updated_date: '2026-08-29 09:18'
labels:
  - 'wave:2-fleet'
dependencies: []
priority: medium
type: chore
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
# Migrate autopi-ha task surface to just

## 1. Outcome

`autopi-ha` has one top-level `justfile` implementing the fleet-mandatory recipe vocabulary
(`default`, `setup`, `fmt`, `fmt-check`, `lint`, `test`, `check`) plus repo-specific optional
recipes (`docgen`, `run`, `clean`, `package`). `Makefile` is deleted. `scripts/setup` and
`scripts/lint` are deleted (absorbed). `scripts/develop` and `scripts/generate_docs.py` remain as
files, each reachable through a recipe. `.github/workflows/tests.yml`'s lint-and-scan job calls
`just fmt-check` and `just lint`; its pytest job calls `just test`. `backlog/config.yml`'s
`definition_of_done` names `just` recipes. `AGENTS.md` documents the `just` task interface. Nobody
runs `make` or `./scripts/setup`/`./scripts/lint` again.

## 2. The complete justfile

Toolchain facts used below (verified from `pyproject.toml`, `.pre-commit-config.yaml`,
`backlog/config.yml`, `.github/workflows/tests.yml`):
- Python 3.14, dependency manager `uv`, no lockfile committed (`uv sync --all-extras`).
- Lint/format: `ruff` (`ruff check`, `ruff format`), config in `pyproject.toml` (`[tool.ruff]`),
  target dirs are `custom_components tests` (per-file-ignores exempt `scripts/*` and
  `.claude/hooks/*` from ruff entirely — do not lint those).
- Typecheck: `mypy custom_components` (mypy config in `pyproject.toml` excludes `tests/` and
  `scripts/`).
- Security: `bandit -r custom_components` (bandit config in `pyproject.toml`, `[tool.bandit]`,
  targets `custom_components` only, excludes `tests`/`scripts`).
- Tests: `pytest` via `pytest-homeassistant-custom-component`, config in `pyproject.toml`
  (`[tool.pytest.ini_options]`) already sets coverage flags via `addopts` — do not duplicate them
  on the command line, that's what the old Makefile did.
- Pre-commit: `.pre-commit-config.yaml` exists and CI does NOT currently run `pre-commit run
  --all-files` as a gate (`tests.yml` only runs ruff check/format directly) — pre-commit is a local
  convenience hook, not part of `check`. Do not add it to `check`; keep a `pre-commit` recipe as
  optional dev convenience only if wanted, but it is NOT required by this migration.
- `scripts/generate_docs.py` — a 37KB real Python program (AST-based doc generator), invoked today
  as `uv run python scripts/generate_docs.py`. KEEP, wrap in `docgen`.
- `scripts/develop` — starts a local Home Assistant instance for manual testing
  (`uv run hass --config ... --debug`), has real control flow (conditional directory/file
  creation) and is long-running / interactive. KEEP, wrap in `run`.
- `scripts/fetch_all_events.py` — one-off API exploration script with a **hardcoded live API
  token and device ID** (`scripts/fetch_all_events.py:9-10`). Not invoked by Makefile, CI, or any
  documented workflow. Out of scope for this migration — do not wrap it in a recipe, do not delete
  it, do not touch it. Flag it in the PR description as a pre-existing secret-in-repo concern for
  Rob to triage separately; this task does not fix it.
- No `typecheck` split needed as a separate optional recipe from `lint` in the old Makefile, but
  the fleet standard lists `typecheck` as optional vocabulary and CI/mypy is a distinct gate — add
  it as its own recipe and put it in `check` explicitly (matches Makefile's separate `type-check`
  target and keeps `lint` fast/ruff-only, `typecheck` separate, matching common Python fleet
  pattern in §11).
- `package` (zip the integration for manual HACS-less distribution) existed in the Makefile
  (`make package`) — keep as an optional `build` recipe since it's real, harmless, and has fleet
  precedent (`build` is in the optional vocabulary).
- No `deps-update`/`docs`/`gen` need in this repo beyond what's listed. `docs` in the old Makefile
  just echoed pointers to README/CONTRIBUTING — drop it; it did nothing worth keeping as a recipe.
- `release` in the old Makefile was an interactive `read -p` version-bump-and-tag script — this
  repo uses `release-please` (see `.github/workflows/release-please.yml`), so that manual release
  flow is obsolete tooling, not a recipe to port. Do not add a `release` recipe; note this in
  traps (§9).

```just
set shell := ["bash", "-euo", "pipefail", "-c"]

# show the task surface
default:
    @just --list

# install toolchain + deps into the repo-local environment
[group('check')]
setup:
    uv sync --all-extras
    uv run pre-commit install
    uv run pre-commit install --hook-type commit-msg

# format code in place
[group('check')]
fmt:
    uv run ruff format custom_components tests
    uv run ruff check --fix custom_components tests
    just --fmt

# verify formatting without mutating
[group('check')]
[no-exit-message]
fmt-check:
    uv run ruff format --check custom_components tests
    just --fmt --check

# run static analysis (ruff + bandit)
[group('check')]
[no-exit-message]
lint:
    uv run ruff check custom_components tests
    uv run bandit -r custom_components

# run mypy type checking
[group('check')]
[no-exit-message]
typecheck:
    uv run mypy custom_components

# run the test suite (optional pytest -k filter)
[group('check')]
[no-exit-message]
test filter="":
    #!/usr/bin/env bash
    set -euo pipefail
    if [ -n "{{ filter }}" ]; then
        uv run pytest -k "{{ filter }}" -vv
    else
        uv run pytest -vv
    fi

# full local gate — everything CI enforces
[group('check')]
check: fmt-check lint typecheck test

# regenerate entity documentation from code
[group('gen')]
docgen:
    uv run python scripts/generate_docs.py

# start a local Home Assistant instance for manual testing (long-running)
[group('dev')]
run:
    ./scripts/develop

# build a distributable integration zip
[group('build')]
build:
    rm -rf dist/
    mkdir -p dist/
    cd custom_components && zip -r ../dist/autopi.zip autopi/ -x "*.pyc" "*/__pycache__/*" "*/.DS_Store"

# remove build artifacts and caches
[group('dev')]
[confirm('remove build/dist/coverage/cache artifacts?')]
clean:
    rm -rf build/ dist/ *.egg-info .coverage htmlcov/ .pytest_cache/ .mypy_cache/ .ruff_cache/ coverage.xml bandit-report.json
    find . -type d -name "__pycache__" -exec rm -rf {} +
```

Notes on this file:
- `test` uses a `[script('bash')]`-equivalent shebang recipe (`#!/usr/bin/env bash` body) because
  it branches on whether `filter` was passed — a plain line-based recipe cannot do `if` safely
  (§10 of the standard, "extra leading whitespace"). This is the correct §6/§10 pattern, not an
  ABSORB violation.
- `fmt` calls `just --fmt` at the end (mutates the justfile itself into canonical formatting, per
  §5.10) and `fmt-check` calls `just --fmt --check` (verifies it, per §1's `fmt-check` contract —
  "must include `just --fmt --check`").
- `[no-exit-message]` is applied to `fmt-check`, `lint`, `typecheck`, `test` because ruff/bandit/
  mypy/pytest all print their own actionable errors (§5.5).
- `clean` gets `[confirm]` — it is destructive of untracked local state per §5.4's "anything that
  ... deletes unrecoverable state" reading; htmlcov/coverage.xml are regenerable but this keeps a
  consistent safety posture. (If Rob wants `clean` un-gated because it only deletes reproducible
  build output, that is a one-line judgement call the follow-up agent may make — but ship it gated
  by default, matching §5.4's literal wording about deletion.)
- No `ci` recipe: CI's lint-and-scan job runs exactly `ruff check --fix` + `ruff format` (not
  `--check`/no `--fix`) — see §5 CI changes below for why that's being tightened to match `check`,
  not why `check` needs a superset. There is no genuine CI-only superset in this repo (no matrix,
  no publish step in `tests.yml`), so `check` alone covers it.

## 3. Makefile disposition

`Makefile` (repo root) — every target:

| Make target | Replacement | Notes |
|---|---|---|
| `help` | `default` (`@just --list`) | |
| `install` | `setup` | drops the `echo "Development environment setup complete!"` — noise, `just --list` output already tells you it ran |
| `test` | `test` | drops the coverage flags on the command line; they live in `pyproject.toml` `addopts` already (Makefile was duplicating them) |
| `test-file` | dropped | `just test <path via filter? no>` — pytest path args aren't the same as `-k` filter. Not carried forward; `uv run pytest tests/test_x.py` remains a fine escape hatch, not worth a dedicated recipe. Record as a deliberate drop, not an oversight. |
| `test-match` | `test filter=...` | `just test filter="test_pattern"` |
| `test-watch` | dropped | required installing `watchdog` on demand — non-trivial control flow (`command -v` check + conditional install) and a niche workflow. Not fleet vocabulary. Drop; note in traps. |
| `test-debug` | dropped | `uv run pytest -vv -s --log-cli-level=DEBUG` remains a fine one-off; not common enough to be a recipe |
| `lint` (+ `lint-ruff`, `lint-mypy`, `lint-bandit`) | `lint` + `typecheck` | mypy split out to its own recipe per §2 above; `lint` now covers ruff+bandit only |
| `format` | `fmt` | |
| `type-check` | `typecheck` | |
| `clean` | `clean` | `[confirm]` added |
| `coverage` | dropped | opening `htmlcov/index.html` in a browser is a human-interactive convenience with OS-specific branching (`open`/`xdg-open`) — non-trivial control flow, not fleet-recipe-shaped. `just test` already produces `htmlcov/` via `pyproject.toml`'s `--cov-report=html`. Drop the browser-open wrapper. |
| `pre-commit` | dropped from `check` | not part of CI's actual gate (see §2 toolchain notes) — do NOT wire into `check`. May be re-added later as an explicit non-gate convenience recipe if Rob wants it; not required by this task |
| `pre-commit-update` | dropped | one-off maintenance command, not routine task surface |
| `validate` | dropped | was `lint pre-commit` plus echo statements about hassfest/HACS running in CI — no unique logic, superseded by `check` |
| `docs` | dropped | did nothing but print two lines pointing at README/CONTRIBUTING |
| `docgen` | `docgen` | |
| `check-all` | dropped | was `lint test validate` — superseded by `check` |
| `dev-server` | dropped | printed 3 lines of manual instructions, did not start anything. `run` (wrapping `scripts/develop`) actually starts HA — that's the real recipe |
| `release` | dropped | interactive manual version-bump/tag flow; obsolete now that `release-please` (`.github/workflows/release-please.yml`) owns releases. Do not port. |
| `update-deps` | dropped | `uv lock --upgrade` — one-off maintenance, not fleet vocabulary (no lockfile is even committed per `pyproject.toml` inspection: no `uv.lock` referenced in gate). If a `uv.lock` exists and is committed, this could become `deps-update`; verify with `ls uv.lock` before dropping — if present, add `deps-update: uv lock --upgrade` in the `check` group instead of dropping. |
| `security` | dropped | `uv run bandit -r custom_components` is now just `lint`; the `safety check` half was already conditional/best-effort and not installed by default |
| `stubs` | dropped | one-off `stubgen` invocation, not routine |
| `docker-build` / `docker-test` | dropped | no `Dockerfile` confirmed present in this repo (this is a HACS custom_component, not a containerized service) — verify with `ls Dockerfile`; if absent, these targets are dead already and dropping is correct |
| `new-platform` | dropped | interactive scaffolding helper (`read -p`), non-trivial control flow, not a fleet recipe pattern |
| `package` | `build` | renamed to match fleet optional vocabulary (`build`, not `package`) |
| `setup` (make target, distinct from `install`) | `setup` (just) already covers this — merge, the make `setup` target just called `install` plus printed a banner | |
| `check-python` | dropped | version-compatibility guard with conditional exit; `requires-python = ">=3.14.2"` in `pyproject.toml` already enforces this via `uv sync` itself |
| `install-hooks` | folded into `setup` | `pre-commit install` + `pre-commit install --hook-type commit-msg`, now two lines inside `just setup` |

**After the justfile is proven locally and CI is switched (§8 order of work), run:**
```
git rm Makefile
```

## 4. Script disposition

| Script | Classification | Replacement | Reason |
|---|---|---|---|
| `scripts/setup` | ABSORB | folded into `just setup` | thin wrapper: `pip3 install uv` (unneeded — CI/dev already has `uv` via `astral-sh/setup-uv` or a local install) + `make install`. No control flow worth keeping. `just setup` (§2) already does the real work (`uv sync --all-extras`, `pre-commit install` ×2). Delete the file. |
| `scripts/lint` | ABSORB | folded into `just fmt` + `just lint` (run separately, or `just fmt lint` when both are wanted) | thin wrapper that just called `make format` then `make lint` with banner echoes. No unique logic. Delete the file. |
| `scripts/develop` | KEEP | `just run` calls `./scripts/develop` | has real conditional control flow (creates `config/` dir and `config/secrets.yaml` template if missing, checks `uv` is on PATH with a fallback error message) and is long-running/interactive (starts a live Home Assistant server on port 8123). §6 KEEP criteria: non-trivial control flow. Update its final error message (`Please run 'make install'...`) to say `just setup` — this is a one-line edit inside the KEPT script, done as part of this task, not a recipe-authoring decision. |
| `scripts/generate_docs.py` | KEEP | `just docgen` calls `uv run python scripts/generate_docs.py` | 37KB AST-based doc generator — a real program per §6, not a task. |
| `scripts/fetch_all_events.py` | OUT OF SCOPE — do not touch | none | Not invoked by Makefile, CI, docs, or AGENTS.md. Contains a hardcoded live API token and device ID (`scripts/fetch_all_events.py:9-10`) — this is a pre-existing exposed-secret concern, unrelated to the just migration. Do not wrap it in a recipe (that would imply it's part of the routine task surface, which it isn't) and do not delete it (not authorized — this task is additive/replacement only for the Makefile-adjacent surface). Flag it to Rob separately. |

## 5. CI changes

### `.github/workflows/tests.yml`

Add the `setup-just` step to both jobs that currently run raw tool commands (`lint-and-scan` and
`pytest`), immediately after the existing `Set up uv` step in each, before `Install dependencies`:

```yaml
      - name: Set up just
        uses: extractions/setup-just@<pin-exact-sha> # v4
        with:
          just-version: '1.58.0'
```
(Resolve `<pin-exact-sha>` to the current SHA for `extractions/setup-just` tag `v4` at
implementation time — match the fleet's existing SHA-pin + `# vN` comment convention visible on
every other `uses:` line in this same file. Do not hand-guess a SHA.)

**`lint-and-scan` job** — replace:
```yaml
      - name: Install dependencies
        run: uv sync --all-extras

      - name: Run Ruff linting
        run: uv run ruff check --fix custom_components tests

      - name: Run Ruff formatting
        run: uv run ruff format custom_components tests
```
with:
```yaml
      - name: Install dependencies
        run: just setup

      - name: Check formatting
        run: just fmt-check

      - name: Run linting
        run: just lint

      - name: Run type checking
        run: just typecheck
```
This is a **behavior tightening**, not a mechanical rename: the old steps ran `ruff check --fix`
(auto-fixing and silently committing nothing — a no-op fixer in CI that can mask drift) and
`ruff format` (also mutating, not checking). `just lint` and `just fmt-check` are non-mutating and
correctly fail the job on any finding, matching what `check` enforces locally. This job did not
run mypy at all before — `just typecheck` is now added so CI matches `just check` exactly (the §1
contract: "If CI runs a check that `check` does not, the contract is broken"; the converse gap —
`check` covering something CI didn't — is being closed here, and this is required, not optional,
because agents will otherwise run `just check` locally, see it fail on typecheck errors that CI
was never catching, and lose trust in the gate).

**`pytest` job** — replace:
```yaml
      - name: Install dependencies
        run: |
          # Install dependencies with all extras
          uv sync --all-extras
          # Verify installation
          uv pip list

      - name: Verify Python environment
        run: |
          uv run python --version
          uv run python -c "import sys; print('Python executable:', sys.executable)"
          uv run python -c "from homeassistant.const import __version__; print('Home Assistant version:', __version__)"

      - name: Create Home Assistant config directory
        run: mkdir -p /tmp/homeassistant

      - name: Run tests with coverage
        env:
          PYTHONPATH: ${{ github.workspace }}
          PYTHONIOENCODING: utf-8
          TZ: UTC
          HA_DISABLE_ANALYTICS: true
          HOMEASSISTANT_CONFIG_DIR: /tmp/homeassistant
          LC_ALL: C.UTF-8
          LANG: C.UTF-8
        run: |
          uv run python -m pytest tests/ \
            --cov=custom_components.autopi \
            --cov-report=term-missing \
            --cov-report=xml \
            --cov-report=html \
            --cov-fail-under=10 \
            --tb=short \
            -v
```
with:
```yaml
      - name: Install dependencies
        run: just setup

      - name: Create Home Assistant config directory
        run: mkdir -p /tmp/homeassistant

      - name: Run tests with coverage
        env:
          PYTHONPATH: ${{ github.workspace }}
          PYTHONIOENCODING: utf-8
          TZ: UTC
          HA_DISABLE_ANALYTICS: true
          HOMEASSISTANT_CONFIG_DIR: /tmp/homeassistant
          LC_ALL: C.UTF-8
          LANG: C.UTF-8
        run: just test
```
Keep the `env:` block on the `just test` step exactly as-is — those are runtime environment
variables `pytest`/Home Assistant read, unrelated to `just` itself, and `just` recipes inherit the
step's environment (§8: "Secrets and env pass through normally"). Drop the "Verify Python
environment" step — it was diagnostic noise (printing the interpreter path and HA version), not a
gate; if Rob wants that back it's a `just`-external decision, not part of this migration.
`--tb=short` and `-v` from the old CI invocation are dropped since they're CI-only cosmetic flags
not present in `pyproject.toml`'s `addopts` — `just test` uses the `pyproject.toml`-defined
`addopts` (`-vv -s`, more verbose than CI's old `-v`) uniformly for both local and CI runs, which
is the point of the gate contract (§1: `check`/`test` must be exactly what CI enforces).

**Do NOT touch:**
- `hassfest` job — GitHub-native reusable action, no `run:` shell logic (§8: never fold
  non-shell `uses:` into `just`).
- `hacs` job — same, GitHub-native action.
- `ci-success` job and its `needs:` list (`lint-and-scan`, `pytest`, `hassfest`, `hacs`) — do not
  rename, do not add/remove entries, the branch ruleset gates on this exact check name.
- The `Codecov`/`Codacy` upload steps — leave exactly as-is, both are `uses:` calls unrelated to
  `just`.
- `permissions:` blocks on every job — unchanged.
- `step-security/harden-runner` steps — unchanged, first step in every job.
- SHA pins on `actions/checkout`, `actions/setup-python`, `astral-sh/setup-uv`,
  `codecov/codecov-action`, `codacy/codacy-coverage-reporter-action` — unchanged.

### Other workflow files — no `just` changes

`actionlint.yml`, `codeql.yml`, `dependency-review.yml`, `release-please.yml`, `scorecard.yml`,
`stale.yml`, `trigger-docs-sync.yml`, `zizmor.yml`, `cleanup-draft-releases.yml`, `arm-automerge.yml`
— none contain build/test/lint `run:` shell logic that maps to a `just` recipe. Confirmed by
reading `actionlint.yml` (a single `uses: rknightion/.github/.github/workflows/actionlint.yml@...`
reusable call, no shell) and `bandit.yml` (a single `uses: shundor/python-bandit-scan@...`
third-party action, no shell — separate from the `bandit` CLI invocation folded into `just lint`
above; this workflow's own bandit run stays as-is, it's a different execution path uploading SARIF
to the Security tab). Do not add `just` calls to any of these files.

## 6. Docs and agent-contract changes

No file in this repo currently references `make <target>` or `./scripts/foo.sh` in prose (verified:
`grep -n "make " AGENTS.md CLAUDE.md README.md` returns nothing — README and AGENTS.md never told
anyone to run `make`, they used raw `uv run` commands directly). This means:

- No README/CONTRIBUTING edits are required for `make` references (there are none).
- `AGENTS.md` currently has a "## Development Environment" section (lines 7–15) listing raw
  `uv run ruff check .` / `uv run mypy .` / `uv run pytest` commands. **Replace that section's
  bullet list** with the fleet-mandated Task Interface block, inserted as its own `##` section
  immediately after "## Development Environment"'s heading (keep the heading, replace the body):

Replace:
```markdown
## Development Environment

This project uses `uv` for Python dependency management. Always use `uv` to run Python commands:
- `uv run ruff check .` - Run linting
- `uv run ruff check . --fix` - Run linting with auto-fix
- `uv run mypy .` - Run type checking
- `uv run pytest` - Run tests
- `uv run python <script>` - Run any Python script
- `uv sync` - Sync dependencies
- `uv pip list` - List installed packages
```
with:
```markdown
## Development Environment

This project uses `uv` for Python dependency management, orchestrated through `just`.

## Task interface

This repo's task surface is a `justfile`. Discover it, don't guess it:

    just --list                        # human-readable
    just --dump --dump-format json     # machine-readable
    just --show <recipe>               # what a recipe actually runs

- `just check` is the full gate and is exactly what CI enforces. It must pass before you commit.
- Prefer `just <recipe>` over the underlying tool. If you are typing `pytest`, you want `just test`.
- Run `just` with stdin from /dev/null. Recipes marked `[confirm]` are destructive — stop and ask
  before running one; never pass `--yes` or `JUST_YES=1`.
- If a task you need does not exist, add a recipe with a `#` doc comment and a `[group(...)]`
  rather than running a bare command.
```
- `CLAUDE.md` is a 6-line pointer (`@AGENTS.md`) — no change needed, it already inherits the above.
- Do NOT paste the recipe list itself into `AGENTS.md` (§9 of the standard).

## 7. backlog/config.yml

Current line (`backlog/config.yml:4`):
```yaml
definition_of_done: ["uv run ruff check custom_components tests", "uv run mypy .", "uv run pytest"]
```
Replace with:
```yaml
definition_of_done: ["just check"]
```
Drive this through the `backlog` CLI, never hand-edit the YAML (per house rule) — e.g.
`backlog config set definition_of_done '["just check"]"` or the equivalent supported subcommand;
confirm the exact CLI invocation against `backlog --help` / `backlog config --help` at
implementation time since this task file cannot verify the installed CLI's exact flag surface.

## 8. Order of work

1. Create `justfile` at repo root (content in §2). Do not touch Makefile/scripts yet.
2. Run `just --fmt --check` — fix formatting. Run `just --list` — confirm all 7 mandatory + optional
   recipes show with correct groups and doc comments.
3. Run `just setup && just check` locally end to end. Fix any command-path mismatches (this repo's
   real `uv`/`ruff`/`mypy`/`bandit`/`pytest` invocations were sourced from `pyproject.toml` and the
   existing Makefile — they should work as-is, but verify: `bandit` needs `-r custom_components`
   exactly, no `-f json -o bandit-report.json` — that flag combo was for producing a report file for
   nothing downstream, drop it, plain text findings to stdout are what CI needs to fail on).
4. Edit `scripts/develop`'s trailing error message (`make install` → `just setup`), per §4. Leave
   the rest of the script untouched.
5. Edit `.github/workflows/tests.yml` per §5. Push to a branch, confirm both jobs go green with the
   new `just`-based steps before merging — do not switch CI and delete the Makefile in the same
   step.
6. Update `AGENTS.md` per §6.
7. Update `backlog/config.yml`'s `definition_of_done` per §7, via the `backlog` CLI.
8. Only once steps 1–7 are verified green (CI passing on the branch, `just check` green locally):
   `git rm Makefile scripts/setup scripts/lint`.
9. Final check: `git grep -n "make "` and `git grep -rn "scripts/setup\|scripts/lint"` across the
   repo return nothing (confirms no stray reference survives).

## 9. Traps specific to this repo

- **`bandit -f json -o bandit-report.json`** in the old Makefile wrote a report file and always
  exited 0-ish for CI purposes only if piped through something that ignored it — the new `just
  lint` runs bandit in plain mode so a finding fails the recipe (exit code propagates, §10 of the
  standard: "`just` is exit-code transparent"). This is intentional tightening — confirm it
  doesn't immediately break `check` on pre-existing bandit findings; if it does, that's real
  signal to fix, not a reason to silence bandit.
- **`ruff check --fix` in CI** (old `tests.yml`) was mutating in a read-only CI checkout — any fix
  it "applied" was silently discarded (no commit step). This masked drift: a repo could go red
  locally on `ruff check` (no `--fix`) while CI stayed green. The new `just fmt-check` / `just
  lint` (no `--fix`) exposes this correctly; expect this to surface pre-existing formatting/lint
  drift not previously visible in CI. Fix the drift, don't relax the recipe.
- **`scripts/develop` is long-running and interactive** (`uv run hass --config ... --debug`,
  starts a webserver on :8123 and blocks on Ctrl+C). `just run` wraps it directly with no
  `[script]`/background handling — this is correct per §6 ("KEEP as a file — wrap it in a recipe")
  but do not try to make `run` non-blocking or add health-check polling; that's scope creep.
- **`scripts/develop`'s own uv-missing fallback** already prints "Please run 'make install'" —
  this string is the one in-script edit this task requires (§4/§8 step 4); do not touch anything
  else in that script, its control flow (directory/secrets bootstrapping) is exactly why it's KEEP
  and not ABSORB.
- **No `uv.lock` verified committed** — confirm with `ls uv.lock` before assuming `deps-update` is
  irrelevant (§3 table, `update-deps` row). If a lockfile exists, `uv sync --all-extras` in `setup`
  already respects it; do not add `--frozen` unless a lockfile is confirmed present and the fleet
  standard's Python reference (§11: `uv sync --all-extras --frozen`) is being followed — verify
  first, this repo's Makefile never used `--frozen` and had no lockfile references anywhere.
- **`per-file-ignores` in `pyproject.toml` exempts `scripts/*` and `.claude/hooks/*` from ruff
  entirely, with a comment explaining CI only lints `custom_components tests`.** Do not widen
  `just lint`'s ruff target to include `scripts/` — that comment (`pyproject.toml:175-177`)
  explicitly documents this boundary; changing it is out of scope and would fight the existing
  per-file-ignore configuration for no reason.
- **`test filter=""` uses a shebang/script-style recipe**, not a plain line recipe — a plain
  `test filter="": uv run pytest -k "{{ if filter != \"\" { filter } else { \"\" } }}"` style
  ternary is exactly the kind of multi-line/conditional construct §10 warns fails with "extra
  leading whitespace" in line-based recipes. Keep the `#!/usr/bin/env bash` body form from §2
  verbatim.
- **`fetch_all_events.py` contains a live-looking API token** — do not `git rm` it as part of this
  task (not authorized, out of scope) and do not paste its contents anywhere. Flag it to Rob
  outside this task's diff.

## 10. Out of scope

Do not touch, in any way, as part of this task:
- `scripts/fetch_all_events.py` (§4, §9 — flag separately, do not modify/delete/wrap).
- `.github/workflows/hassfest` and `hacs` jobs inside `tests.yml` (GitHub-native `uses:` steps).
- `.github/workflows/actionlint.yml` — reusable `uses:` call only.
- `.github/workflows/bandit.yml` — third-party `uses: shundor/python-bandit-scan@...` SARIF
  upload workflow; unrelated execution path from `just lint`'s local bandit run.
- `.github/workflows/codeql.yml` — GitHub-native CodeQL.
- `.github/workflows/dependency-review.yml` — GitHub-native.
- `.github/workflows/release-please.yml` — GitHub-native; per fleet-wide standing instruction,
  release-please auth is broker-minted, never a stored PAT, and this workflow must stay
  self-contained (no cross-repo `uses:` on a `github-actions[bot]`-authored PR) — do not touch.
- `.github/workflows/scorecard.yml` — GitHub-native OpenSSF Scorecard.
- `.github/workflows/stale.yml`, `cleanup-draft-releases.yml`, `arm-automerge.yml` — GitHub-native
  housekeeping, no build/test/lint logic.
- `.github/workflows/trigger-docs-sync.yml` — GitHub-native, broker-token-based docs dispatch, no
  build/test/lint `run:` logic to migrate.
- `.github/workflows/zizmor.yml` — GitHub-native (not read in full during this inventory, but
  confirmed by name/pattern to be a workflow-linting-only job with no build/test/lint shell
  content relevant to `just`).
- `.pre-commit-config.yaml` — leave entirely as-is; it is not wired into `check` (§2 toolchain
  notes) and this task does not add or remove pre-commit hooks.
- `custom_components/`, `tests/`, all integration source and test code — no code changes.
- The Codecov/Codacy coverage-upload steps inside `tests.yml`'s `pytest` job — leave the `uses:`
  calls exactly as they are.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Top-level justfile exists implementing all seven mandatory recipes (default, setup, fmt, fmt-check, lint, test, check) plus docgen, run, build, typecheck, clean
- [ ] #2 just check passes locally and is exactly what CI's tests.yml lint-and-scan and pytest jobs enforce (fmt-check, lint, typecheck, test)
- [ ] #3 just --fmt --check passes
- [ ] #4 just --list shows a doc comment and correct [group(...)] for every public recipe
- [ ] #5 Makefile is deleted (git rm)
- [ ] #6 scripts/setup and scripts/lint are deleted; scripts/develop and scripts/generate_docs.py remain and are reachable via just run and just docgen respectively
- [ ] #7 scripts/fetch_all_events.py is untouched and not wrapped in any recipe
- [ ] #8 .github/workflows/tests.yml's lint-and-scan and pytest jobs call just recipes (setup, fmt-check, lint, typecheck, test) with a setup-just step pinned to just-version 1.58.0, and the ci-success job's needs list is unchanged
- [ ] #9 AGENTS.md's Development Environment section is replaced with the fleet Task interface block; no file in the repo references make or scripts/setup or scripts/lint
- [ ] #10 backlog/config.yml's definition_of_done is set to ["just check"] via the backlog CLI
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 uv run ruff check custom_components tests
- [ ] #2 uv run mypy .
- [ ] #3 uv run pytest
<!-- DOD:END -->

## Comments

<!-- COMMENTS:BEGIN -->
author: campaign-ordering
created: 2026-08-29 09:18
---
## Fleet ordering — WAVE 2. Starts after the Wave 0 pilot (`sf2loki` / SFL-0073) and the Wave 1 hubs land.

Within Wave 2 the order is free — these repos do not depend on each other. Batching by language is worthwhile so one lane reuses its Makefile-to-recipe mapping across similar repos.

Do not start before the pilot reports. The standard may be amended off the back of it, and picking this up early risks coding against a superseded seam.

**Provisioning `just` in CI.** Which mechanism depends on the runner, and the two must not be mixed:

| Runner | Mechanism |
| --- | --- |
| `arc-arm64` (m7kni self-hosted) | `just` is **baked into the runner image** by `m7kni/ci-tools` (`runner-image/Dockerfile`, `ARG JUST_VERSION`). Do **not** add `extractions/setup-just`, and delete the step if this repo already has one — it installs a second `just` earlier on `PATH` and turns the image pin into a lie. |
| GitHub-hosted (all `rknightion` repos) | `extractions/setup-just`, SHA-pinned, with an explicit `just-version:`. |

Both sides currently sit on **1.58.0** and are Renovate-managed. `ci-tools`' `Tool version drift` workflow fails if the Dockerfile `ARG` and the published image ever disagree, and lists any repo still carrying a second pin.

**While you are in the workflow files, check the hub pin.** On 2026-08-29 Renovate was unfrozen for `rknightion/.github` in `m7kni/renovate-config` — it had been `enabled: false` on the mistaken belief that callers tracked `@main`, which froze the fleet across 19 different hub SHAs (v1.3.1 June → v1.9.7 August) so that no hub fix ever propagated. Bumps now arrive as one grouped, CI-gated, automerged PR per repo. **A `uses:` whose comment is not a real `# vX.Y.Z` still cannot be bumped** (it resolves to a digest-only update, which the fleet rules disable) — if you find one, repair the comment as part of this task.
---
<!-- COMMENTS:END -->
