# Makefile for AutoPi Home Assistant Integration

.PHONY: help install test lint format clean pre-commit hassfest docs check-all coverage test-file test-watch validate

# Default target
help:
	@echo "Available commands:"
	@echo "  make install      Install all dependencies (runtime and dev)"
	@echo "  make test         Run all tests with coverage"
	@echo "  make test-file    Run specific test file (usage: make test-file FILE=tests/test_sensor.py)"
	@echo "  make test-watch   Watch for changes and run tests"
	@echo "  make lint         Run all linters (ruff, mypy, bandit)"
	@echo "  make format       Format code with ruff"
	@echo "  make clean        Remove build artifacts and cache files"
	@echo "  make coverage     Generate HTML coverage report"
	@echo "  make pre-commit   Run pre-commit hooks on all files"
	@echo "  make validate     Run all local validations"
	@echo "  make docs         Build documentation"
	@echo "  make docgen       Generate entity documentation from code"
	@echo "  make check-all    Run all checks (lint, test, validate)"

# Install dependencies
install:
	uv sync --all-extras
	uv run pre-commit install
	@echo "Development environment setup complete!"

# Run tests with coverage
test:
	uv run pytest \
		--cov=custom_components.autopi \
		--cov-report=term-missing:skip-covered \
		--cov-report=html \
		--cov-report=xml \
		--cov-fail-under=10 \
		-vv

# Run specific test file or test
test-file:
ifdef FILE
	uv run pytest $(FILE) -vv
else
	@echo "Usage: make test-file FILE=tests/test_sensor.py"
endif

# Run specific test by name pattern
test-match:
ifdef MATCH
	uv run pytest -k "$(MATCH)" -vv
else
	@echo "Usage: make test-match MATCH=test_pattern"
endif

# Watch for changes and run tests
test-watch:
	@command -v watchmedo >/dev/null 2>&1 || (echo "Installing watchdog..." && uv add --dev watchdog)
	uv run watchmedo shell-command \
		--patterns="*.py" \
		--recursive \
		--command='clear && uv run pytest -x' \
		custom_components tests

# Run tests with debug output
test-debug:
	uv run pytest -vv -s --log-cli-level=DEBUG

# Run all linters
lint: lint-ruff lint-mypy lint-bandit

# Individual linters
lint-ruff:
	uv run ruff check custom_components tests

lint-mypy:
	uv run mypy custom_components \
		--ignore-missing-imports \
		--install-types \
		--non-interactive

lint-bandit:
	uv run bandit -r custom_components -f json -o bandit-report.json

# Format code with ruff
format:
	uv run ruff format custom_components tests
	uv run ruff check --fix custom_components tests

# Type check only
type-check:
	uv run mypy custom_components

# Clean build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf **/__pycache__/
	rm -f coverage.xml
	rm -f bandit-report.json
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete

# Generate coverage report
coverage:
	uv run pytest --cov=custom_components.autopi --cov-report=html
	@echo "Coverage report generated in htmlcov/index.html"
	@if command -v open >/dev/null 2>&1; then \
		open htmlcov/index.html; \
	elif command -v xdg-open >/dev/null 2>&1; then \
		xdg-open htmlcov/index.html; \
	else \
		echo "Please open htmlcov/index.html in your browser"; \
	fi

# Run pre-commit hooks
pre-commit:
	uv run pre-commit run --all-files

# Update pre-commit hooks
pre-commit-update:
	uv run pre-commit autoupdate

# Validate integration (hassfest runs in CI)
validate: lint pre-commit
	@echo "✅ Local validation complete!"
	@echo "Note: hassfest validation runs in CI. Push to a branch to see results."
	@echo "GitHub Actions will run:"
	@echo "  - hassfest (Home Assistant integration validation)"
	@echo "  - HACS validation"
	@echo "  - Full test suite"

# Build documentation
docs:
	@echo "Documentation is in README.md and CONTRIBUTING.md"
	@echo "API docs: https://rknightion.github.io/autopi-ha/"

# Generate entity documentation from code
docgen:
	uv run python scripts/generate_docs.py
	@echo "✅ Entity documentation generated!"

# Run all checks
check-all: lint test validate
	@echo "✅ All checks passed!"

# Development server (for testing with Home Assistant)
dev-server:
	@echo "To test with Home Assistant:"
	@echo "1. Copy custom_components/autopi to your HA config directory"
	@echo "2. Restart Home Assistant"
	@echo "3. Add the integration via UI"

# Create a release
release:
	@echo "Creating release..."
	@if [ "$$(uname)" = "Darwin" ]; then \
		read -p "Version number (e.g., 0.1.0): " version; \
		sed -i '' "s/\"version\": \".*\"/\"version\": \"$$version\"/" custom_components/autopi/manifest.json; \
	else \
		read -p "Version number (e.g., 0.1.0): " version; \
		sed -i "s/\"version\": \".*\"/\"version\": \"$$version\"/" custom_components/autopi/manifest.json; \
	fi; \
	git add custom_components/autopi/manifest.json; \
	git commit -m "chore: bump version to $$version"; \
	git tag -a "v$$version" -m "Release version $$version"; \
	echo "Release v$$version created. Push with: git push && git push --tags"

# Update dependencies
update-deps:
	uv lock --upgrade
	uv pip list --outdated

# Security check
security:
	uv run bandit -r custom_components
	@if uv pip show safety >/dev/null 2>&1; then \
		uv run safety check; \
	else \
		echo "Tip: Install safety with 'uv add --dev safety' for vulnerability scanning"; \
	fi

# Type stubs
stubs:
	uv run stubgen custom_components -o stubs/

# Docker commands for testing
docker-build:
	docker build -t autopi-ha .

docker-test:
	docker run --rm autopi-ha make test

# Initialize new component (helper for adding new platforms)
new-platform:
	@read -p "Platform name (e.g., switch, climate): " platform; \
	cp custom_components/autopi/sensor.py custom_components/autopi/$$platform.py; \
	echo "Created custom_components/autopi/$$platform.py"; \
	echo "Remember to:"
	echo "  1. Update PLATFORMS in __init__.py"
	echo "  2. Implement the platform-specific logic"
	echo "  3. Add tests in tests/test_$$platform.py"

# Create integration package for distribution
package:
	@echo "Creating integration package..."
	@rm -rf dist/
	@mkdir -p dist/
	@cd custom_components && zip -r ../dist/autopi.zip autopi/ -x "*.pyc" "*/__pycache__/*" "*.pyc" "*/.DS_Store"
	@echo "Package created: dist/autopi.zip"
	@echo "Size: $$(du -h dist/autopi.zip | cut -f1)"

# Quick setup for new contributors
setup: install
	@echo "🎉 Development environment ready!"
	@echo ""
	@echo "Quick start commands:"
	@echo "  make test        - Run tests"
	@echo "  make lint        - Check code quality"
	@echo "  make format      - Auto-format code"
	@echo "  make validate    - Run all checks"
	@echo ""
	@echo "See 'make help' for all commands"

# Check Python version
check-python:
	@python_version=$$(uv run python --version 2>&1 | cut -d' ' -f2); \
	required_version="3.12"; \
	if [ "$$(printf '%s\n' "$$required_version" "$$python_version" | sort -V | head -n1)" != "$$required_version" ]; then \
		echo "⚠️  Python $$python_version found, but $$required_version+ is required"; \
		exit 1; \
	else \
		echo "✅ Python $$python_version is compatible"; \
	fi

# Install git hooks
install-hooks:
	uv run pre-commit install
	uv run pre-commit install --hook-type commit-msg
	@echo "Git hooks installed!"