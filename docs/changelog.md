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
