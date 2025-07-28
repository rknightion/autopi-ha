---
title: FAQ
description: Frequently asked questions about the AutoPi Home Assistant integration
---

# Frequently Asked Questions

This page answers common questions about the AutoPi Home Assistant integration.

## Installation and Setup

### Q: How do I install the AutoPi integration?

**A:** The integration can be installed via HACS (recommended) or manually:

1. **HACS Installation**:
   - Add `https://github.com/rknightion/autopi-ha` as a custom repository
   - Search for "AutoPi" in HACS integrations
   - Install and restart Home Assistant

2. **Manual Installation**:
   - Download the latest release from GitHub
   - Extract to `custom_components/autopi/`
   - Restart Home Assistant

See the [Installation Guide](installation.md) for detailed instructions.

### Q: Where do I get an AutoPi API token?

**A:** Log in to [app.autopi.io](https://app.autopi.io) and navigate to **Account Settings** → **API Tokens**. Create a new token with at least read permissions for vehicles and position data.

### Q: The integration doesn't appear in my integration list. What's wrong?

**A:** Common causes and solutions:

1. **Files not in correct location**: Ensure files are in `config/custom_components/autopi/`
2. **Home Assistant not restarted**: Restart HA after installation
3. **File permissions**: Ensure HA can read the files
4. **Check logs**: Look for loading errors in Home Assistant logs

### Q: Can I monitor vehicles from multiple AutoPi accounts?

**A:** Currently, each integration instance supports one AutoPi account. You can add multiple instances of the integration if you have multiple accounts, but each will need its own API token.

## Configuration

### Q: How many vehicles can I monitor?

**A:** There's no hard limit in the integration. You can monitor all vehicles associated with your AutoPi account. However, consider API usage limits and update frequency when monitoring many vehicles.

### Q: What's the difference between update intervals?

**A:** The integration uses three update rings:

- **Fast (default 1 min)**: Position data (GPS, speed, altitude)
- **Medium (default 5 min)**: Vehicle status and profile data
- **Slow (default 15 min)**: Reserved for future features

### Q: Can I set different update intervals for different vehicles?

**A:** Currently, update intervals apply to all vehicles in an integration instance. This is by design to optimize API usage with bulk operations.

### Q: My vehicle doesn't appear in the setup. Why?

**A:** Possible reasons:

1. **API token permissions**: Ensure your token has vehicle read access
2. **Vehicle offline**: Check if the vehicle is online in the AutoPi dashboard
3. **Account issues**: Verify the vehicle is properly registered to your account

## Entities and Data

### Q: What entities are created for each vehicle?

**A:** Each vehicle gets:

- **Device tracker**: GPS location tracking
- **Status sensor**: Shows license plate or vehicle name
- **Position sensors**: Speed, altitude, course, GPS satellites
- **Diagnostic sensors**: Latitude, longitude (hidden by default)

See the [Entity Reference](entities.md) for complete details.

### Q: Why don't I see all the entities mentioned in the documentation?

**A:** Entity availability depends on:

1. **Vehicle connectivity**: Vehicle must be online and reporting data
2. **GPS lock**: Position sensors require GPS signal
3. **API access**: Your AutoPi plan may limit certain data
4. **Device capabilities**: Not all AutoPi devices report all data types

### Q: Can I hide the diagnostic entities?

**A:** Yes, diagnostic entities are hidden by default in most Home Assistant views. You can also:

1. Use entity customization to change visibility
2. Configure the recorder to exclude them from history
3. Hide them in specific dashboard cards

### Q: Why is my vehicle showing as "unavailable"?

**A:** Entities become unavailable when:

- Vehicle hasn't reported data recently
- AutoPi API is unreachable
- Authentication issues with API token
- GPS signal is lost for extended periods

Check the integration's diagnostic sensors for API health information.

## Performance and API Usage

### Q: How many API calls does the integration make?

**A:** This depends on your configuration:

```
Daily API calls = (Number of vehicles × 1440 minutes) / Update interval
```

Examples:
- 1 vehicle, 5-minute updates: ~288 calls/day
- 3 vehicles, 1-minute updates: ~4,320 calls/day

The integration optimizes with bulk API calls where possible.

### Q: I'm getting rate limit errors. What should I do?

**A:** Rate limiting solutions:

1. **Increase update intervals**: Reduce API call frequency
2. **Check AutoPi plan**: Verify your plan's API limits
3. **Monitor usage**: Use diagnostic sensors to track API calls
4. **Wait it out**: Rate limits usually reset automatically

### Q: Does the integration work when my vehicle is parked/off?

**A:** This depends on your AutoPi device configuration:

- **Ignition mode**: Only works when vehicle is running
- **Always-on mode**: Works continuously (drains vehicle battery)
- **Smart mode**: Activates based on movement or schedule

Check your AutoPi device settings for power management options.

## Troubleshooting

### Q: My GPS coordinates seem inaccurate. Is this normal?

**A:** GPS accuracy varies based on:

- **Satellite count**: More satellites = better accuracy
- **Environment**: Buildings, tunnels, trees can affect signal
- **Vehicle movement**: More accurate when moving
- **Weather**: Atmospheric conditions can impact accuracy

Typical accuracy is 3-5 meters in good conditions, 10+ meters in poor conditions.

### Q: Vehicle speed shows small values when parked. Why?

**A:** This is normal GPS behavior. GPS has inherent noise that can show speeds of 0.1-0.5 m/s even when stationary. Consider this in automations by using thresholds above the noise level.

### Q: Integration stops updating after some time. How do I fix this?

**A:** Common causes and solutions:

1. **API token expired**: Check token validity in AutoPi dashboard
2. **Network issues**: Verify Home Assistant's internet connectivity
3. **AutoPi service down**: Check AutoPi status page
4. **Integration bug**: Check logs and consider restarting the integration

### Q: Can I access historical trip data?

**A:** Currently, the integration provides real-time data only. Historical trip data is planned for future releases. For now, use Home Assistant's recorder to maintain historical sensor data.

## Features and Limitations

### Q: Does the integration support OBD-II data?

**A:** OBD-II data support is planned for future releases. Currently, the integration focuses on GPS tracking and basic vehicle information.

### Q: Can I control my vehicle through the integration?

**A:** The current integration is read-only for safety and security reasons. Remote control features may be considered for future releases based on AutoPi API capabilities.

### Q: Does the integration work with all AutoPi devices?

**A:** The integration should work with all AutoPi devices that:

- Connect to the AutoPi cloud service
- Report GPS position data
- Are accessible via the AutoPi REST API

### Q: Can I use this integration without an internet connection?

**A:** No, the integration requires internet connectivity to communicate with the AutoPi cloud API. Local-only operation is not currently supported.

## Privacy and Security

### Q: What data does the integration store?

**A:** The integration stores:

- Your encrypted API token in Home Assistant's config
- Recent vehicle position and status data
- API usage statistics

Historical data retention depends on your Home Assistant recorder configuration.

### Q: Is my location data secure?

**A:** Security measures include:

- **Encryption**: API tokens are encrypted in Home Assistant
- **HTTPS**: All API communication uses HTTPS
- **Local storage**: Data stays within your Home Assistant instance
- **No cloud**: No data is sent to third-party services (except AutoPi)

### Q: Can I exclude location data from recordings?

**A:** Yes, configure the recorder to exclude position sensors:

```yaml
recorder:
  exclude:
    entities:
      - sensor.my_car_latitude
      - sensor.my_car_longitude
```

## Development and Contributions

### Q: Can I contribute to the project?

**A:** Yes! Contributions are welcome:

- **Bug reports**: Create issues on GitHub
- **Feature requests**: Suggest new features
- **Code contributions**: Submit pull requests
- **Documentation**: Help improve documentation

See the [Contributing Guide](contributing.md) for details.

### Q: How do I report a bug?

**A:** When reporting bugs, include:

1. **Home Assistant version**
2. **Integration version**
3. **Steps to reproduce**
4. **Error logs** (enable debug logging)
5. **Expected vs. actual behavior**

Submit reports on [GitHub Issues](https://github.com/rknightion/autopi-ha/issues).

### Q: Can I request new features?

**A:** Absolutely! Feature requests are welcomed on GitHub. Popular requests include:

- OBD-II diagnostics
- Trip history and analytics
- Geofencing alerts
- Maintenance reminders
- Fuel consumption tracking

## Integration Comparison

### Q: How does this compare to other vehicle tracking integrations?

**A:** The AutoPi integration offers:

**Advantages**:
- Purpose-built for AutoPi devices
- Optimized API usage
- Comprehensive vehicle data
- Active development and support

**Considerations**:
- Requires AutoPi hardware
- Cloud-dependent operation
- Limited to AutoPi's API capabilities

### Q: Can I use this alongside other vehicle integrations?

**A:** Yes, the AutoPi integration can coexist with other vehicle tracking integrations. Each will create its own entities and devices.

## Future Plans

### Q: What features are planned for future releases?

**A:** Planned features include:

- **OBD-II data**: Engine diagnostics, fuel consumption
- **Trip analytics**: Distance, duration, efficiency
- **Maintenance tracking**: Service reminders, diagnostics
- **Advanced alerts**: Geofencing, speed monitoring
- **Enhanced automation**: Smart scheduling, presence detection

### Q: How often is the integration updated?

**A:** Updates are released based on:

- Bug fixes and security patches (as needed)
- Feature releases (monthly/quarterly)
- AutoPi API changes (as required)

Follow the GitHub repository for update notifications.

### Q: Will the integration support local-only operation?

**A:** Local operation would require AutoPi to provide local API access. This is not currently available but may be considered if AutoPi adds local connectivity options.

## Getting Help

### Q: Where can I get help with issues?

**A:** Help resources:

1. **Documentation**: Start with this documentation
2. **GitHub Issues**: Search existing issues
3. **Community Forums**: Home Assistant community
4. **AutoPi Support**: For device-specific issues

### Q: How do I enable debug logging?

**A:** Add to your `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.autopi: debug
```

This provides detailed information for troubleshooting.

### Q: The integration is working, but I want to optimize it. Any tips?

**A:** Optimization tips:

1. **Monitor API usage**: Use diagnostic sensors
2. **Adjust intervals**: Balance freshness with efficiency
3. **Use automations**: Leverage vehicle data for smart home scenarios
4. **Regular maintenance**: Keep API tokens current
5. **Plan for growth**: Consider future vehicle additions

See the [API Optimization Guide](api-optimization.md) for detailed recommendations. 