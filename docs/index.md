---
title: AutoPi Home Assistant Integration
description: Monitor and track your vehicles with AutoPi cloud platform integration for Home Assistant
image: assets/social-card.png
---

# AutoPi Home Assistant Integration

The AutoPi Home Assistant integration allows you to monitor and track your vehicles equipped with AutoPi devices through Home Assistant. This integration provides real-time vehicle data, GPS tracking, and comprehensive diagnostics.

<!-- TODO: Add hero image ![AutoPi Integration](images/autopi-hero.png) -->

## Features

### 🚗 Vehicle Monitoring
- **Real-time Status**: Monitor vehicle connectivity and status
- **Location Tracking**: GPS-based device tracking with high accuracy
- **Vehicle Diagnostics**: Access OBD-II data and vehicle health information

### 📊 Comprehensive Sensors
- **Position Sensors**: Altitude, speed, course, GPS satellites
- **Vehicle Information**: License plate, VIN, make/model details
- **Integration Health**: API call statistics and success rates

### ⚡ Optimized Performance
- **Smart Update Intervals**: Configurable fast, medium, and slow update cycles
- **Efficient API Usage**: Bulk API calls and intelligent error handling
- **Minimal Resource Usage**: Optimized for Home Assistant performance

### 🔧 Easy Configuration
- **GUI Configuration**: Simple setup through Home Assistant UI
- **Vehicle Selection**: Choose which vehicles to monitor
- **Flexible Options**: Customize update intervals and behavior

## Quick Start

1. **Installation**: Install via HACS or manual installation
2. **Configuration**: Add integration through Home Assistant UI
3. **API Key**: Enter your AutoPi API token
4. **Vehicle Selection**: Choose vehicles to monitor
5. **Enjoy**: Monitor your vehicles in Home Assistant!

## What You Get

### Entities Per Vehicle
- **Device Tracker**: GPS location tracking
- **Status Sensor**: Current vehicle status
- **Position Sensors**: Speed, altitude, course, GPS satellites
- **Location Sensors**: Latitude/longitude (diagnostic)

### Integration-Wide Entities
- **Vehicle Count**: Total monitored vehicles
- **API Statistics**: Calls, failures, success rate
- **Performance Metrics**: Update duration tracking

## Supported AutoPi Features

The integration currently supports:

- ✅ **Vehicle Profile Data**: Basic vehicle information
- ✅ **GPS Position Data**: Real-time location and movement
- ✅ **Multiple Vehicles**: Monitor unlimited vehicles
- ✅ **Device Tracking**: Home Assistant map integration
- 🔄 **OBD-II Data**: Coming in future releases
- 🔄 **Trip History**: Coming in future releases
- 🔄 **Alerts & Events**: Coming in future releases

## System Requirements

- **Home Assistant**: 2023.1.0 or later
- **AutoPi Account**: Active AutoPi cloud account
- **API Access**: AutoPi API token with vehicle access
- **Python**: 3.11+ (handled by Home Assistant)

## Getting Help

- **Documentation**: Comprehensive guides and references
- **GitHub Issues**: Bug reports and feature requests
- **Community**: Home Assistant Community forums
- **Support**: AutoPi support for account issues

---

## Next Steps

Ready to get started? Choose your installation method:

<div class="grid cards" markdown>

-   :material-download-box:{ .lg .middle } **HACS Installation**

    ---

    Install easily through the Home Assistant Community Store

    [:octicons-arrow-right-24: Install via HACS](installation.md#hacs-installation)

-   :material-file-download:{ .lg .middle } **Manual Installation**

    ---

    Download and install manually for custom setups

    [:octicons-arrow-right-24: Manual Installation](installation.md#manual-installation)

-   :material-cog:{ .lg .middle } **Configuration**

    ---

    Set up your API connection and select vehicles

    [:octicons-arrow-right-24: Configuration Guide](configuration.md)

-   :material-book-open:{ .lg .middle } **Developer Guide**

    ---

    Contribute to the project or build custom features

    [:octicons-arrow-right-24: Development](development.md)

</div>

## Community & Support

Join our community and get help:

- **GitHub**: [rknightion/autopi-ha](https://github.com/rknightion/autopi-ha)
- **Issues**: [Report bugs or request features](https://github.com/rknightion/autopi-ha/issues)
- **Discussions**: [Community discussions](https://github.com/rknightion/autopi-ha/discussions)
- **AutoPi**: [Official AutoPi website](https://autopi.io) 
