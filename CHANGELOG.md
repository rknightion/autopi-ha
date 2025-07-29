# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### ✨ Features
- Add `auto_zero_enabled` attribute to all sensors indicating auto-zero support
- Add `auto_zero_last_zeroed`, `auto_zero_cooldown_until`, and `auto_zero_active` attributes for auto-zeroed metrics
- Add warning in configuration that auto-zero feature requires 1-minute polling interval

### 🔧 Changes
- Simplify update interval configuration to single interval (remove multi-tier system)
- Update documentation URL from rknightion.github.io to m7kni.io
- Consolidate all data fetching to use same update interval

### 🐛 Bug Fixes
- Fix pytest warnings for unawaited coroutines
- Fix datetime.utcnow() deprecation warnings
- Fix codespell configuration for intentional API typos

### 📚 Documentation
- Update configuration docs to reflect single update interval
- Add auto-zero polling interval requirement to documentation
- Document new auto-zero entity attributes


## [0.3.2] - 2025-07-28


### 🐛 Bug Fixes
- update GSM signal scaling from 0-31 to 1-5 range


## [0.3.1] - 2025-07-28


### 🐛 Bug Fixes
- handle None values in trip end positions
- improve error handling and trip parsing resilience

### 🧰 Maintenance
5cbd6fc chore(deps): downgrade homeassistant-stubs and update pymdown-extensions
773d192 chore(deps): update dependency homeassistant-stubs to v2025.7.4

### 📋 Other Changes
- Merge remote-tracking branch 'origin/renovate/homeassistant-stubs-2025.x'
- enhance(autopi): improve event handling and categorization


## [0.3.0] - 2025-07-28


### 🚗 Vehicle Features
- firing events on startup to avoid replaying old events


## [0.2.1] - 2025-07-28


### 📋 Other Changes
- Add fleet alerts and device events functionality
- Add trip tracking functionality to AutoPi integration
- Update README.md
- add logo


## [0.2.0] - 2025-07-28


### 🚗 Vehicle Features
- add error and abort messages to AutoPi strings
- Add API key update functionality to options flow

### 🐛 Bug Fixes
- improve versioning logic and remove redundant UI text
- improve git commit handling and code formatting
- name
- improve GitHub workflows for authentication and reliability
- update authentication method from Bearer to APIToken

### 🧰 Maintenance
2838042 refactor: replace position API with data fields API for richer vehicle metrics
55448a5 chore: docs
63974d6 chore: change project license from MIT to Apache-2.0
560f8ef ci: enhance GitHub Actions security and variable handling
87d0558 ci: add GitHub workflows and repository configuration

### 📚 Documentation
- fix documentation links and update Cloudflare deployment

### 📋 Other Changes
- Add vehicle position tracking with tiered update intervals
- Add AutoPi API documentation for Home Assistant integration
- Add pre-commit hooks and code quality tools
- Implement initial AutoPi Home Assistant integration
- initial commit
- Initial commit


---

For releases prior to v0.2.0, see the [GitHub Releases page](https://github.com/rknightion/autopi-ha/releases).
