---
title: Vehicle Data
description: Understanding vehicle data, attributes, and sensor readings from AutoPi devices
---

# Vehicle Data

This guide explains the vehicle data provided by the AutoPi integration and how to interpret sensor readings.

## Vehicle Information

Each monitored vehicle provides comprehensive information stored as device and entity attributes.

### Basic Vehicle Attributes

| Attribute | Description | Example | Notes |
|-----------|-------------|---------|-------|
| `vehicle_id` | Unique AutoPi vehicle identifier | `abc123` | Internal ID, not user-friendly |
| `name` | Vehicle display name | `My Tesla` | User-defined in AutoPi dashboard |
| `license_plate` | Vehicle registration number | `ABC-123` | May be empty if not configured |
| `vin` | Vehicle Identification Number | `1HGBH41...` | 17-character VIN |
| `year` | Manufacturing year | `2022` | Integer value |
| `type` | Vehicle type classification | `ICE`, `EV`, `HYBRID` | AutoPi classification |
| `make_id` | Manufacturer identifier | `tesla` | AutoPi internal make ID |
| `model_id` | Model identifier | `model_3` | AutoPi internal model ID |
| `battery_voltage` | Nominal battery voltage | `12` | Vehicle electrical system voltage |

### Extended Attributes

Additional attributes may be available depending on your vehicle and AutoPi device configuration:

| Attribute | Description | Availability |
|-----------|-------------|--------------|
| `make` | Manufacturer name | Common |
| `model` | Vehicle model name | Common |
| `trim` | Specific trim/version | Limited |
| `engine_size` | Engine displacement | ICE vehicles |
| `fuel_type` | Primary fuel type | Most vehicles |
| `transmission` | Transmission type | Limited |

## Position Data

Real-time position and movement data from GPS and vehicle sensors.

### GPS Location

| Field | Description | Unit | Accuracy |
|-------|-------------|------|----------|
| `latitude` | GPS latitude coordinate | Decimal degrees | ±3-5 meters |
| `longitude` | GPS longitude coordinate | Decimal degrees | ±3-5 meters |
| `altitude` | Height above sea level | Meters | ±10-20 meters |
| `location_accuracy` | GPS accuracy estimate | Meters | Variable |

### Movement Data

| Field | Description | Unit | Notes |
|-------|-------------|------|-------|
| `speed` | Current vehicle speed | m/s | Converted by HA to preferred unit |
| `course` | Direction of travel | Degrees (0-360) | 0° = North, 90° = East |
| `num_satellites` | GPS satellites in view | Count | More = better accuracy |

### Position Timestamps

All position data includes timestamp information:
- **UTC Time**: All timestamps in UTC
- **Precision**: Usually sub-second accuracy
- **Age**: How old the position data is

## Data Interpretation

### Understanding GPS Accuracy

GPS accuracy depends on several factors:

#### Excellent Accuracy (1-3 meters)
- Clear sky view
- 8+ satellites
- No interference
- Stationary or slow-moving

#### Good Accuracy (3-10 meters)
- Partial sky view
- 5-7 satellites
- Light interference
- Normal driving conditions

#### Poor Accuracy (10+ meters)
- Obstructed view (tunnels, parking garages)
- Few satellites (<5)
- Heavy interference
- Urban canyon effects

### Speed Interpretation

Speed data comes from GPS calculations:

- **At Rest**: Speed may show small values (0.1-0.5 m/s) due to GPS noise
- **Low Speed**: More accurate for speeds >5 km/h
- **High Speed**: Generally very accurate for highway speeds
- **Unit Conversion**: Home Assistant converts to your preferred units

### Course/Direction

Direction interpretation:
- **0°**: True North
- **90°**: East
- **180°**: South
- **270°**: West
- **Accuracy**: Most accurate when moving >10 km/h

## Data Availability

### When Data is Available

Position data is available when:
- Vehicle is powered on (ignition or auxiliary power)
- AutoPi device has cellular connectivity
- GPS has sufficient satellite lock
- API endpoints are accessible

### Data Gaps

Common reasons for missing data:
- **Vehicle Off**: Engine off and no auxiliary power
- **No Connectivity**: Cellular signal issues
- **GPS Blocked**: Underground parking, dense urban areas
- **Device Issues**: AutoPi device malfunction
- **API Issues**: Temporary service problems

### Historical Data

The integration provides real-time data. For historical analysis:
- Use Home Assistant's built-in recorder
- Configure appropriate retention periods
- Consider database size for high-frequency updates

## Sensor State Classes

Understanding Home Assistant sensor classifications:

### Measurement Sensors
- **Current Values**: Speed, altitude, course
- **Updates**: Real-time measurements
- **History**: Shows trends over time
- **Statistics**: Supports min/max/average

### Total Increasing Counters
- **API Calls**: Cumulative count of API requests
- **Persistence**: Survives restarts
- **Reset**: Only reset on integration reload

### Diagnostic Entities
- **Purpose**: Technical monitoring
- **Visibility**: Hidden by default in some views
- **Importance**: Critical for troubleshooting

## Entity Availability

Entities become unavailable when:

### Connection Issues
- No internet connectivity
- AutoPi API unavailable
- Authentication failures

### Data Issues
- Vehicle hasn't reported recent data
- GPS lock lost for extended period
- Device connectivity problems

### Integration Issues
- Configuration errors
- Coordinator update failures
- Rate limit exceeded

## Troubleshooting Data Issues

### Missing Position Data

1. **Check Vehicle Status**:
   - Is the vehicle powered on?
   - Is the AutoPi device LED showing connectivity?

2. **Verify GPS**:
   - Move vehicle to open area
   - Wait for GPS lock (can take 2-5 minutes)

3. **Check AutoPi Dashboard**:
   - Log in to app.autopi.io
   - Verify device is online
   - Check recent positions

### Inaccurate Data

1. **GPS Accuracy**:
   - Check `num_satellites` sensor
   - Verify `location_accuracy` attribute
   - Consider environmental factors

2. **Timing Issues**:
   - Check timestamp of last update
   - Verify integration update intervals
   - Look for pattern in data gaps

### Entity Unavailable

1. **Integration Health**:
   - Check API success rate sensor
   - Review failed API calls count
   - Monitor update duration

2. **Configuration**:
   - Verify API token is valid
   - Check vehicle is still selected
   - Confirm network connectivity

## Data Usage and Privacy

### API Usage

Monitor your API usage:
- Use diagnostic sensors to track calls
- Optimize update intervals for your needs
- Consider AutoPi plan limitations

### Privacy Considerations

Vehicle location data is sensitive:
- **Encryption**: Data encrypted in Home Assistant
- **Access Control**: Limit who can view vehicle entities
- **Retention**: Configure recorder settings appropriately
- **External Access**: Secure remote access to Home Assistant

### Data Retention

Configure Home Assistant recorder:

```yaml
# configuration.yaml
recorder:
  purge_keep_days: 30  # Adjust as needed
  exclude:
    entities:
      # Optionally exclude high-frequency sensors
      - sensor.my_car_latitude
      - sensor.my_car_longitude
```

## Advanced Data Usage

### Automations

Use vehicle data in automations:

#### Arrival Detection
```yaml
trigger:
  - platform: zone
    entity_id: device_tracker.my_car
    zone: zone.home
    event: enter
```

#### Speed Monitoring
```yaml
trigger:
  - platform: numeric_state
    entity_id: sensor.my_car_speed
    above: 100  # km/h
```

#### Low GPS Quality Alert
```yaml
trigger:
  - platform: numeric_state
    entity_id: sensor.my_car_gps_satellites
    below: 4
```

### Templates

Create custom sensors:

#### Distance from Home
```yaml
sensor:
  - platform: template
    sensors:
      car_distance_home:
        friendly_name: "Car Distance from Home"
        unit_of_measurement: "km"
        value_template: >
          {{ distance(states.device_tracker.my_car.attributes.latitude,
                      states.device_tracker.my_car.attributes.longitude,
                      states.zone.home.attributes.latitude,
                      states.zone.home.attributes.longitude) }}
```

#### Speed in MPH
```yaml
sensor:
  - platform: template
    sensors:
      car_speed_mph:
        friendly_name: "Car Speed (MPH)"
        unit_of_measurement: "mph"
        value_template: >
          {{ (states('sensor.my_car_speed') | float * 2.237) | round(1) }}
```

## Future Data Features

Planned enhancements for vehicle data:

### OBD-II Data
- Engine diagnostics
- Fuel consumption
- RPM and engine load
- Diagnostic trouble codes

### Trip Information
- Trip start/end detection
- Distance and duration
- Average speed
- Fuel efficiency

### Advanced Analytics
- Driving behavior analysis
- Maintenance predictions
- Performance trends
- Cost tracking 