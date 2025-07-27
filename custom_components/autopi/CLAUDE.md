# AutoPi Integration Component

## Component Structure

This directory contains the main AutoPi Home Assistant integration implementation.

### Core Files

#### `__init__.py`
- Main integration setup and teardown
- Manages the data update coordinator lifecycle
- Handles config entry setup and platform forwarding
- Implements options update listener

#### `config_flow.py`
- User-facing configuration interface
- Two-step flow: API key validation → Vehicle selection
- Options flow for runtime configuration (scan interval)
- Comprehensive error handling with user-friendly messages

#### `coordinator.py`
- Centralized data fetching using DataUpdateCoordinator pattern
- Manages API client instance
- Filters vehicles based on user selection
- Handles authentication errors and triggers reauth

#### `client.py`
- Low-level AutoPi API client
- Implements retry logic with exponential backoff
- Comprehensive error handling and logging
- Type-safe API response handling

#### `sensor.py`
- Vehicle count sensor (diagnostic entity)
- Individual vehicle sensors
- Proper entity naming and device association

### Supporting Files

#### `const.py`
- All integration constants
- Configuration keys
- API endpoints
- Default values and limits

#### `exceptions.py`
- Custom exception hierarchy
- Specific exceptions for different error scenarios
- Enables precise error handling throughout

#### `types.py`
- TypedDict definitions for API responses
- Data classes for internal representation
- Type safety throughout the integration

#### `strings.json`
- User-facing strings for config flow
- Supports internationalization
- Error messages and descriptions

#### `manifest.json`
- Integration metadata
- Dependencies and requirements
- Home Assistant integration configuration

### Subdirectories

#### `entities/`
- Base entity classes
- Shared entity logic
- Device info generation

#### `config/` (future)
- Configuration schemas
- Migration logic
- Validation helpers

#### `data/` (future)
- Data transformers
- API response processing

#### `devices/` (future)
- Device-specific implementations
- Model-specific features

#### `hubs/` (future)
- Hub implementations for different AutoPi services
- Service-specific logic

#### `services/` (future)
- Custom Home Assistant services
- Service handlers

#### `utils/` (future)
- Helper functions
- Caching logic
- Performance monitoring

## Data Flow

1. **Setup Phase**
   - User initiates config flow
   - API key validation
   - Vehicle discovery and selection
   - Config entry creation

2. **Runtime Phase**
   - Coordinator polls API on interval
   - Data distributed to entities
   - Entities update their state
   - Home Assistant updates UI

3. **Error Handling**
   - API errors caught by client
   - Coordinator handles update failures
   - Authentication errors trigger reauth
   - User notified of persistent issues

## Adding New Features

### Adding a New Sensor
1. Define new sensor class in `sensor.py`
2. Add to entity list in `async_setup_entry`
3. Update `strings.json` with entity names
4. Add constants to `const.py` if needed

### Adding a New API Endpoint
1. Add endpoint constant to `const.py`
2. Implement method in `client.py`
3. Add TypedDict for response in `types.py`
4. Update coordinator if needed

### Adding a New Platform
1. Create new platform file (e.g., `binary_sensor.py`)
2. Add platform to `PLATFORMS` in `const.py`
3. Implement `async_setup_entry`
4. Create entity classes

## Best Practices

### API Communication
- Always use the client class
- Never make direct API calls from entities
- Handle all possible error cases
- Log API interactions at debug level

### Entity Implementation
- Extend base entity classes
- Use proper device association
- Include comprehensive attributes
- Follow Home Assistant naming conventions

### Error Handling
- Use specific exceptions
- Log errors appropriately
- Provide user-friendly error messages
- Implement graceful degradation

### Performance
- Use DataUpdateCoordinator for polling
- Minimize API calls
- Cache data when appropriate
- Use efficient data structures

## Testing

### Manual Testing
1. Add integration through UI
2. Verify vehicle discovery
3. Check sensor updates
4. Test error scenarios
5. Verify options flow

### Unit Testing
- Mock API responses
- Test error handling
- Verify data transformations
- Check entity state calculations

### Integration Testing
- Test with real API (dev account)
- Verify long-running stability
- Check memory usage
- Monitor API call frequency