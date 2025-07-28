# AutoPi Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/rknightion/autopi-ha.svg?style=flat-square)](https://github.com/rknightion/autopi-ha/releases)
[![License](https://img.shields.io/github/license/rknightion/autopi-ha.svg?style=flat-square)](LICENSE)
[![Tests](https://github.com/rknightion/autopi-ha/workflows/Tests/badge.svg)](https://github.com/rknightion/autopi-ha/actions/workflows/tests.yml)
[![FOSSA Status](https://app.fossa.com/api/projects/git%2Bgithub.com%2Frknightion%2Fautopi-ha.svg?type=shield)](https://app.fossa.com/projects/git%2Bgithub.com%2Frknightion%2Fautopi-ha?ref=badge_shield)
[![Documentation](https://img.shields.io/badge/docs-mkdocs-blue.svg)](https://autopi.ha-components.m7kni.com)

![AutoPi Logo](docs/images/logo.png)

This custom integration allows you to monitor your AutoPi vehicle tracking devices through Home Assistant. AutoPi combines OBD-II diagnostic data with GPS tracking to provide comprehensive vehicle monitoring and analytics.

## Features

- 🚗 **Vehicle Diagnostic Data**
  - Engine parameters (RPM, coolant temperature, intake air temperature)
  - Fuel system status and consumption
  - Vehicle speed and odometer readings
  - Engine load and throttle position
  - Battery voltage and electrical system health
  - Diagnostic trouble codes (DTCs)
  - Emissions data (O2 sensor readings, catalyst efficiency)

- 📍 **GPS Tracking & Location**
  - Real-time vehicle location
  - Trip tracking and history
  - Geofencing capabilities
  - Speed monitoring and alerts
  - Route optimization data

- 🔄 **Automatic Device Discovery** - Automatically discovers all AutoPi devices in your account
- ⚙️ **Flexible Configuration**
  - Select specific vehicles to monitor or monitor all
  - Configurable update interval (default: 5 minutes for real-time vehicle data)
  - Auto-discovery can be enabled/disabled
  - Configurable discovery interval for new devices
- 📊 **Real-time Updates** - Fetches latest vehicle data at your configured interval
- 🏢 **Multi-Vehicle Support** - Monitors multiple vehicles across your AutoPi account
- 📱 **Device-Centric Design** - Each AutoPi device is registered as a device with its metrics as entities

## Device and Entity Structure

This integration follows Home Assistant best practices:
- **Devices**: Each physical AutoPi device/vehicle is registered as a device in Home Assistant
- **Entities**: Each metric from a vehicle (speed, RPM, location, etc.) is a separate entity
- This allows you to:
  - Assign vehicles to different areas/zones
  - View all metrics from a vehicle in one place
  - Create automations based on specific vehicle conditions
  - Disable individual metrics you don't need

## Prerequisites

- Home Assistant 2024.1.0 or newer
- AutoPi account with API access
- At least one AutoPi device installed in a vehicle

## Installation

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=rknightion&repository=autopi-ha)

### HACS Installation (Recommended)

1. Open HACS in your Home Assistant instance
2. Click on "Integrations"
3. Click the three dots in the top right corner and select "Custom repositories"
4. Add `https://github.com/rknightion/autopi-ha` as a custom repository
5. Select "Integration" as the category
6. Click "Add"
7. Search for "AutoPi" and install it
8. Restart Home Assistant

### Manual Installation

1. Download the latest release from the [releases page](https://github.com/rknightion/autopi-ha/releases)
2. Extract the `custom_components/autopi` folder to your Home Assistant's `custom_components` directory
3. Restart Home Assistant

## Configuration

### Getting your AutoPi API Key

1. Log in to your [AutoPi Cloud](https://my.autopi.io)
2. Navigate to your account settings
3. Go to "API Access" or "Developer Settings"
4. Generate a new API key or use an existing one

### Adding the Integration

1. Go to Settings → Devices & Services in Home Assistant
2. Click "Add Integration"
3. Search for "AutoPi"
4. Enter your API key when prompted
5. Select your vehicles from the dropdown or leave empty to monitor all
6. Configure update interval and auto-discovery settings

### Configuration Options

After setup, you can modify options by clicking "Configure" on the integration:
- **Update Interval**: How often to fetch vehicle data (minimum 60 seconds, default 300 seconds/5 minutes)
- **Enable Auto-Discovery**: Automatically discover and add new AutoPi devices
- **Device Discovery Interval**: How often to scan for new devices when auto-discovery is enabled

## Documentation

📚 **[Full Documentation](https://autopi.ha-components.m7kni.com)** - Comprehensive guides, API reference, and troubleshooting

## Supported Data Types

### Currently Supported
- **OBD-II Diagnostic Data**
  - Engine RPM, speed, throttle position
  - Coolant temperature, intake air temperature
  - Fuel system status, fuel consumption
  - Battery voltage, engine load
  - Diagnostic trouble codes (DTCs)
- **GPS & Location Data**
  - Real-time coordinates, altitude
  - Trip data, mileage tracking
  - Speed monitoring
- **Device Health & Status**
  - AutoPi device connectivity
  - Signal strength, power status

### Planned Support
- Advanced trip analytics
- Predictive maintenance alerts
- Fleet management features

## Entity Naming

Entities are created with the following naming pattern:
- `sensor.{vehicle_name}_{data_type}`
- `binary_sensor.{vehicle_name}_{status_type}`
- `device_tracker.{vehicle_name}`

For example:
- `sensor.my_car_rpm`
- `sensor.my_car_coolant_temperature`
- `sensor.my_car_fuel_level`
- `device_tracker.my_car`
- `binary_sensor.my_car_engine_running`

## Attributes

Each sensor entity includes the following attributes:
- `device_id`: AutoPi device ID
- `vehicle_id`: Vehicle identifier
- `last_updated`: Timestamp of last data reading
- `unit_system`: Imperial or metric units

## Examples

### Automation Example

```yaml
automation:
  - alias: "Low Fuel Alert"
    trigger:
      - platform: numeric_state
        entity_id: sensor.my_car_fuel_level
        below: 10
    action:
      - service: notify.mobile_app
        data:
          title: "Low Fuel Warning!"
          message: "Your car fuel level is below 10%"

  - alias: "Vehicle Started"
    trigger:
      - platform: state
        entity_id: binary_sensor.my_car_engine_running
        to: "on"
    action:
      - service: notify.mobile_app
        data:
          title: "Vehicle Started"
          message: "Your car engine has been started"
```

### Dashboard Card Example

```yaml
type: entities
title: Vehicle Status
entities:
  - entity: sensor.my_car_rpm
    name: Engine RPM
  - entity: sensor.my_car_coolant_temperature
    name: Coolant Temp
  - entity: sensor.my_car_fuel_level
    name: Fuel Level
  - entity: binary_sensor.my_car_engine_running
    name: Engine Status
  - entity: device_tracker.my_car
    name: Location
```

## Debugging and Troubleshooting

### Enable Debug Logging

To enable debug logging for this integration, add the following to your `configuration.yaml`:

```yaml
logger:
  default: warning
  logs:
    custom_components.autopi: debug
```

This will show detailed information about:
- Device discovery
- API calls and responses
- Entity creation
- Update intervals
- Any errors or warnings

### Common Issues

#### No devices found
- Verify your API key has access to your AutoPi account
- Check that you have AutoPi devices registered to your account
- Ensure the devices are online and reporting data
- Check debug logs for specific error messages

#### Authentication errors
- Regenerate your API key in the AutoPi Cloud
- Remove and re-add the integration with the new key

#### Missing vehicle data
- Some vehicles don't support all OBD-II parameters
- Check the vehicle compatibility in AutoPi Cloud
- Verify the device has been reporting data recently
- Enable debug logging to see what metrics are being received

#### Slow updates
- AutoPi devices may have varying update frequencies based on configuration
- Check your configured update interval in the integration options
- Note that more frequent polling won't get newer data if the devices haven't updated

### Testing Locally

For development and testing:

1. **Clone the repository**
   ```bash
   git clone https://github.com/rknightion/autopi-ha.git
   cd autopi-ha
   ```

2. **Set up development environment**
   ```bash
   # Install UV if you haven't already
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Install dependencies
   uv sync

   # Install pre-commit hooks
   uv run pre-commit install
   ```

3. **Run tests**
   ```bash
   uv run pytest
   ```

4. **Test in Home Assistant**
   - Copy the `custom_components/autopi` folder to your Home Assistant config directory
   - Restart Home Assistant
   - Add the integration through the UI
   - Monitor logs for any issues

5. **Validate with hassfest**
   ```bash
   uv run python -m script.hassfest
   ```

## Development

For development setup and guidelines, see [CONTRIBUTING.md](CONTRIBUTING.md).

### Quick Start

```bash
# Clone the repository
git clone https://github.com/rknightion/autopi-ha.git
cd autopi-ha

# Install UV if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Set up development environment
uv sync
uv run pre-commit install

# Run tests
uv run pytest

# Run linters and formatting
uv run ruff check custom_components tests
uv run ruff format custom_components tests
```

## Contributing

We welcome contributions! Please see our [Development Guide](docs/development.md) for detailed information on setting up your development environment and contributing to the project.

### Quick Start for Developers

1. Fork the repository
2. Create a feature branch
3. Follow the guidelines in [docs/development.md](docs/development.md)
4. Submit a pull request

For detailed instructions, see [docs/development.md](docs/development.md).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

[![FOSSA Status](https://app.fossa.com/api/projects/git%2Bgithub.com%2Frknightion%2Fautopi-ha.svg?type=large)](https://app.fossa.com/projects/git%2Bgithub.com%2Frknightion%2Fautopi-ha?ref=badge_large)

## Disclaimer

This integration is not affiliated with, endorsed by, or sponsored by AutoPi.io ApS. All product and company names are trademarks or registered trademarks of their respective holders.
