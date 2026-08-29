set shell := ["bash", "-euo", "pipefail", "-c"]

# show the task surface
default:
    @just --list

# install toolchain and dependencies into the repo-local environment
setup:
    uv sync --all-extras --locked
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

# run static analysis
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

# run the test suite, optionally filtered with `filter=...`
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

# run the full local gate
[group('check')]
check: fmt-check lint typecheck test

# update locked dependencies
[group('check')]
deps-update:
    uv lock --upgrade

# regenerate entity documentation from code
[group('gen')]
docgen:
    uv run python scripts/generate_docs.py

# start a local Home Assistant instance for manual testing
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
[confirm('remove build/dist/coverage/cache artifacts?')]
[group('dev')]
clean:
    rm -rf build/ dist/ *.egg-info .coverage htmlcov/ .pytest_cache/ .mypy_cache/ .ruff_cache/ coverage.xml bandit-report.json
    find . -type d -name "__pycache__" -exec rm -rf {} +
