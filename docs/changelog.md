---
layout: default
title: Changelog
description: Release history and changelog for the AutoPi Home Assistant Integration
---

# Changelog

All notable changes to this project are documented here. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

<div class="alert alert-info" role="alert">
  <i class="bi bi-info-circle me-2"></i>
  <strong>Note:</strong> This changelog is automatically updated from our <a href="{{ site.repository }}/blob/main/CHANGELOG.md">main CHANGELOG.md</a> when releases are published.
</div>


## [Unreleased]


## [0.7.2] - 2025-08-26


### 🐛 Bug Fixes
- update dependency aiohttp to v3.12.15

### 🧰 Maintenance
92840d9 chore(deps): lock file maintenance
a0d0040 chore(deps): update actions/ai-inference action to v2.0.1 (#40)
66745b7 chore(deps): update actions/checkout action to v5
605c1ac chore(deps): update actions/ai-inference action to v2
c4275a1 chore(deps): update dependency mypy to v1.17.1
beed3a5 chore(deps): pin dependencies
fdfbf62 chore(deps): update codecov/codecov-action action to v5.5.0
28f77f0 chore(deps): update astral-sh/setup-uv action to v6.6.0
819c19b chore(deps): update zizmorcore/zizmor-action action to v0.1.2
1777970 chore(deps): update actions/dependency-review-action action to v4.7.2
36ebbef chore(deps): update actions/ai-inference action to v1.2.8
f317284 chore(deps): update home-assistant/actions digest to 72e1db9
f1691a9 chore(deps): update hacs/action digest to 885037d
9309664 chore(deps): update actions/checkout action to v4.3.0
a49bd8d chore(deps): update github/codeql-action action to v3.29.11
38686ec chore(deps): update dependency ruff to v0.12.10
51d3302 chore(deps): lock file maintenance
e5e65a0 chore(deps): update dependency homeassistant-stubs to v2025.8.3
40c237d chore(deps): update dependency pytest-homeassistant-custom-component to v0.13.272
7269409 refactor: improve error handling and logging practices

### 📋 Other Changes
- Merge pull request #39 from rknightion/renovate/lock-file-maintenance
- Merge pull request #36 from rknightion/renovate/actions-ai-inference-2.x
- Merge pull request #19 from rknightion/renovate/actions-checkout-5.x
- Merge pull request #9 from rknightion/renovate/mypy-1.x
- Merge pull request #38 from rknightion/renovate/lock-file-maintenance
- Merge pull request #37 from rknightion/renovate/pin-dependencies
- Merge pull request #35 from rknightion/renovate/codecov-codecov-action-5.x
- Merge pull request #31 from rknightion/renovate/astral-sh-setup-uv-6.x
- Merge pull request #30 from rknightion/renovate/zizmorcore-zizmor-action-0.x
- Merge pull request #28 from rknightion/renovate/actions-dependency-review-action-4.x
- Merge pull request #27 from rknightion/renovate/home-assistant-actions-digest
- Merge pull request #21 from rknightion/renovate/hacs-action-digest
- Merge pull request #18 from rknightion/renovate/actions-checkout-4.x
- Merge pull request #13 from rknightion/renovate/actions-ai-inference-1.x
- Merge pull request #8 from rknightion/renovate/aiohttp-3.x
- Merge pull request #7 from rknightion/renovate/github-codeql-action-3.x
- Merge pull request #6 from rknightion/renovate/ruff-0.x
- Merge pull request #10 from rknightion/renovate/pytest-homeassistant-custom-component-0.x
- Merge pull request #16 from rknightion/renovate/homeassistant-stubs-2025.x
- migrate fully to renovate
- update pr automerge
- Merge remote-tracking branch 'origin/main'
- prepare for hacs submission


## [0.7.1] - 2025-08-09


### 🐛 Bug Fixes
- units of measturement

### 📋 Other Changes
- docs


## [0.7.0] - 2025-08-03


### 🚗 Vehicle Features
- add auto-removal of deleted vehicles

### 📋 Other Changes
- Merge remote-tracking branch 'origin/main'


## [0.6.0] - 2025-08-03


### 🚗 Vehicle Features
- implement automatic vehicle discovery

### 📋 Other Changes
- add robots


## [0.5.0] - 2025-07-30


### 🚗 Vehicle Features
- enhance auto-zero debugging capabilities

### 🐛 Bug Fixes
- update dependency aiohttp to v3.12.15

### 🧰 Maintenance
7fe4413 chore: remove broken test
0f1c7ea refactor(auto-zero): simplify stale data detection mechanism
c7fb8db refactor: remove event type definitions from string files
679d588 chore: deps
dd9be17 chore(deps): update dependency pytest-homeassistant-custom-component to v0.13.264
f47d240 chore(deps): update dependency homeassistant-stubs to v2025.7.4

### 📋 Other Changes
- Revert "Merge remote-tracking branch 'origin/renovate/aiohttp-3.x'"
- Merge remote-tracking branch 'origin/renovate/aiohttp-3.x'
- Merge remote-tracking branch 'origin/renovate/pytest-homeassistant-custom-component-0.x'
- Merge remote-tracking branch 'origin/renovate/homeassistant-stubs-2025.x'


## [0.4.0] - 2025-07-29


### 🚗 Vehicle Features
- add state persistence for zeroed metrics
- add event types for vehicle events

### 🐛 Bug Fixes
- implement comprehensive error handling and logging

### 🧰 Maintenance
8f2dd93 refactor: simplify update interval configuration to use single unified interval
e351c26 refactor: split AutoPiDataFieldSensor for better auto-zero support
3a3055b chore: trigger build
fcb2218 chore: trigger build
c720bff ci: add workflow to trigger documentation sync
58d8508 chore: update project name and custom domain pattern

### 📚 Documentation
- expand entity documentation with comprehensive sensor categories
- update

### 📋 Other Changes
- Add auto-zero functionality for stale vehicle metrics
- build
- fix
- trigger pipeline
- fix missing /
- fix mkdocs site URL
- handle base route
- use redirects not routes
- add www route
- fix route


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

## Support

- **Questions**: Check our [FAQ](faq) or see the troubleshooting section on the [main page](/)
- **Issues**: Report bugs on [GitHub Issues]({{ site.repository }}/issues)
- **Discussions**: Join the conversation on [GitHub Discussions]({{ site.repository }}/discussions)

## Links

- **[Full Changelog]({{ site.repository }}/blob/main/CHANGELOG.md)** - Complete technical changelog
- **[Releases]({{ site.repository }}/releases)** - Download specific versions
- **[Release Notes]({{ site.repository }}/releases)** - Detailed release information
