# AutoPi Home Assistant Integration

## Overview
This is a custom Home Assistant integration for the AutoPi cloud platform. It allows users to monitor their vehicles equipped with AutoPi devices through Home Assistant.

## Development Environment

This project uses `uv` for Python dependency management. Always use `uv` to run Python commands:
- `uv run ruff check .` - Run linting
- `uv run ruff check . --fix` - Run linting with auto-fix
- `uv run mypy .` - Run type checking
- `uv run pytest` - Run tests
- `uv run python <script>` - Run any Python script
- `uv sync` - Sync dependencies
- `uv pip list` - List installed packages

## Architecture

### Key Components
1. **Config Flow** (`config_flow.py`): Handles user authentication and vehicle selection
2. **API Client** (`client.py`): Manages all communication with the AutoPi REST API
3. **Coordinator** (`coordinator.py`): Implements the Home Assistant DataUpdateCoordinator pattern for efficient data fetching
4. **Entities** (`entities/`): Base classes for all AutoPi entities
5. **Sensors** (`sensor.py`): Vehicle count and individual vehicle sensors

### Data Flow
1. User enters API key through config flow
2. Config flow validates credentials and fetches available vehicles
3. User selects vehicles to monitor
4. Coordinator polls AutoPi API at configured intervals
5. Sensors update based on coordinator data

## API Integration

### Authentication
- Uses APIToken authentication with the AutoPi API key (format: `APIToken <token>`)
- API key is stored securely in the Home Assistant config entry

### Endpoints Used
- `/vehicle/v2/profile` - Fetches vehicle profile information
- `/logbook/v2/most_recent_positions/` - Fetches most recent positions for all devices (bulk API)

### Rate Limiting
- Implements exponential backoff retry logic
- Respects API rate limits with proper error handling

## Entity Structure

### Sensors
1. **Vehicle Count Sensor**: Shows total number of monitored vehicles
2. **Vehicle Sensor**: Individual sensor per vehicle showing license plate/name (displayed as "Status")
3. **API Calls Sensor**: Tracks total number of API calls made
4. **Failed API Calls Sensor**: Tracks number of failed API calls
5. **API Success Rate Sensor**: Shows percentage of successful API calls
6. **Update Duration Sensor**: Shows duration of last API update in seconds
7. **Altitude Sensor**: Vehicle altitude in meters
8. **Speed Sensor**: Vehicle speed in m/s (converts to user's preferred unit)
9. **Course Sensor**: Vehicle heading/direction in degrees
10. **GPS Satellites Sensor**: Number of GPS satellites in view
11. **Latitude Sensor**: Vehicle latitude (diagnostic)
12. **Longitude Sensor**: Vehicle longitude (diagnostic)

### Device Tracker
- **Vehicle Tracker**: GPS-based device tracker for each vehicle

### Attributes
Each vehicle entity includes:
- `vehicle_id`: Unique AutoPi vehicle ID
- `license_plate`: Vehicle registration number
- `vin`: Vehicle Identification Number
- `year`: Manufacturing year
- `type`: Vehicle type (ICE, EV, etc.)
- `battery_voltage`: Nominal battery voltage
- `devices`: List of associated AutoPi device IDs

## Configuration

### Config Entry Data
- `api_key`: AutoPi API authentication key
- `base_url`: API base URL (default: https://api.autopi.io)
- `selected_vehicles`: List of vehicle IDs to monitor
- `scan_interval`: Update interval in minutes

### Options
- `update_interval_fast`: Position update interval (1-60 minutes, default: 1)
- `update_interval_medium`: Vehicle status update interval (1-60 minutes, default: 5)
- `update_interval_slow`: Reserved for future use (1-60 minutes, default: 15)

## Error Handling

### Exception Hierarchy
- `AutoPiError`: Base exception (follows PEP-8 naming convention)
  - `AutoPiAuthenticationError`: Invalid API key
  - `AutoPiConnectionError`: Network/connection issues
  - `AutoPiAPIError`: API returned error response
  - `AutoPiRateLimitError`: Rate limit exceeded
  - `AutoPiTimeoutError`: Request timeout

### Recovery
- Authentication errors trigger reauth flow
- Connection errors are logged and retried
- Coordinator handles update failures gracefully
- Users can update their API key through the reauth flow without reconfiguring

## Logging

### Log Levels
- `INFO`: Integration setup, vehicle discovery, successful updates
- `WARNING`: No vehicles found, auth failures
- `ERROR`: API errors, connection failures
- `DEBUG`: Detailed API communication, entity initialization

### Third-party Library Suppression
Suppresses verbose logging from:
- `aiohttp`
- `async_timeout`

## Future Enhancements

### Additional Endpoints
Planned API endpoints to integrate:
- `/trips/v2` - Trip history and statistics
- `/telemetry/v2` - Real-time vehicle telemetry
- `/alerts/v2` - Vehicle alerts and notifications

### Additional Platforms
- **Binary Sensors**: Engine status, door status, connection status
- **Device Tracker**: GPS-based vehicle location tracking
- **Switches**: Remote vehicle controls (if supported)
- **Services**: Custom services for AutoPi-specific actions

### Features
- Multi-vehicle dashboard cards
- Historical data graphing
- Geofencing support
- Maintenance reminders
- Fuel/energy consumption tracking

## Development Guidelines

### Code Style
- Follows Home Assistant core code style
- Type hints throughout
- Comprehensive docstrings
- Proper error handling and logging

### Testing
- Unit tests for API client
- Integration tests for config flow
- Mock AutoPi API responses

### Best Practices
- Uses Home Assistant's DataUpdateCoordinator for efficient polling
- Implements proper device registry integration
- Follows Home Assistant entity naming conventions
- Supports config flow options for runtime configuration

## Troubleshooting

### Common Issues
1. **No vehicles showing**: Check API key permissions
2. **Update failures**: Verify network connectivity
3. **Missing attributes**: Some vehicles may not report all data

### Debug Mode
Enable debug logging:
```yaml
logger:
  default: info
  logs:
    custom_components.autopi: debug
```

## Resources
- AutoPi API Documentation: https://api.autopi.io/docs
- Home Assistant Developer Docs: https://developers.home-assistant.io
- Integration GitHub: https://github.com/rknightion/autopi-ha

## Tracker rules (non-negotiable)

Work is tracked in `backlog/` via the Backlog.md CLI. The queue is a query, not a file:
`backlog task list --plain` for open work, `backlog doc list --plain` for the durable docs.

- Read the **Agent fan-out protocol (canonical)** doc before designing a wave, and the **Wave
  operating model** doc for this project's own rules. `backlog doc list --plain` shows both.
- Closed GitHub issues predating the tracker are indexed in the **Closed GitHub issues index** doc.
  The issues themselves are still live on GitHub; that doc is a pointer, not a copy.

**`backlog/` is committed to a PUBLIC repo, so tasks and docs must never contain real account
identifiers or vehicle data** — no AutoPi API tokens, device UUIDs, vehicle IDs, VINs, registration
plates, GPS coordinates, email addresses or account IDs. Write the shape, not the instance:
`<device-uuid>`, `<vehicle-id>`, "the second vehicle on the account". Aggregate counts, field names,
response *shapes* and structural findings are fine. This repo has already been burned by it: the
now-deleted `todos.txt` carried a live `APIToken`, a device UUID and home coordinates into public
git history, where deleting the file does not unpublish them. Sweep before committing:

```bash
grep -rniE "APIToken +[0-9a-z]{16,}|[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}|(vehicle|device)_id=[0-9a-f]|-?[0-9]{1,3}\.[0-9]{5,}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}" backlog/ && echo "PII FOUND"
```

**Never use `--notes` or `--plan` bare.** They *silently replace* the whole section — an open
upstream bug that destroys another session's writes with no warning. Use `--append-notes` and
`--append-plan`. `.claude/hooks/backlog-guard.py` denies the bare forms; do not work around it.

**Finalize in one call**, so an interrupted agent cannot leave finished work looking unfinished:

```bash
backlog task edit APH-0007 --check-ac 1 --check-ac 2 -s Done
```

**Never hand-edit task, draft, doc, decision or milestone markdown.** Section boundaries are
HTML-comment markers; break one and the section is *silently dropped*, exit code 0, with the data
still in the file but invisible until the next write destroys it for real. There is no repair
command — `backlog doctor` only fixes duplicate task IDs. `backlog/config.yml` is the one explicit
exception: list-valued keys cannot be set through `backlog config set` and must be edited by hand.

**Never let two agents edit the same task.** v1.50.x fixed the lost-write race in the edit funnel
but *not* in reorder, draft saves, the TUI edit path, `doc update` or decision updates.

<!-- BACKLOG.MD GUIDELINES START -->
<!-- backlog.md-instructions-version: 1.50.1 -->
<CRITICAL_INSTRUCTION>

## Backlog.md Workflow

This project uses Backlog.md for task and project management.

**For every user request in this project, run `backlog instructions overview` before answering or taking action.**

Use the overview to decide whether to search, read, create, or update Backlog tasks.

Before task lifecycle actions, read the matching detailed guide:
- `backlog instructions task-creation` before creating or splitting tasks
- `backlog instructions task-execution` before planning, changing status or assignee, adding a plan or implementation notes, or implementing task work
- `backlog instructions task-finalization` before checking acceptance criteria, writing final summaries, or moving tasks to terminal statuses

Use `backlog <command> --help` before running unfamiliar commands. Help shows options, fields, and examples.

Do not edit Backlog task, draft, document, decision, or milestone markdown files directly. Use the `backlog` CLI so metadata, relationships, and history stay consistent.

</CRITICAL_INSTRUCTION>
<!-- BACKLOG.MD GUIDELINES END -->
