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