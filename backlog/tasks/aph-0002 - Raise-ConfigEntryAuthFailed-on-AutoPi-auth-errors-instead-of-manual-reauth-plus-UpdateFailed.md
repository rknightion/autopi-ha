---
id: APH-0002
title: >-
  Raise ConfigEntryAuthFailed on AutoPi auth errors instead of manual reauth
  plus UpdateFailed
status: To Do
assignee: []
created_date: '2026-11-07T18:57:00Z'
labels: []
dependencies: []
priority: medium
type: bug
ordinal: 2000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
custom_components/autopi/coordinator.py (about line 703-709, except AutoPiAuthenticationError in _async_update_data) calls self.config_entry.async_start_reauth(self.hass) and then raises UpdateFailed. Home Assistant's DataUpdateCoordinator contract is to raise ConfigEntryAuthFailed, which starts one reauth flow and stops polling; the current code re-triggers reauth on every poll interval while the entry is failing. Found by a Kodus rules-research pass on 2026-11-07, confirmed by reading the code.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Authentication errors in _async_update_data raise ConfigEntryAuthFailed and no longer call async_start_reauth directly
- [ ] #2 A test proves an auth failure triggers a single reauth flow and does not raise UpdateFailed
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 just check
<!-- DOD:END -->
