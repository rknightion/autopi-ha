# Entity Reference

This page provides a comprehensive reference of all entities provided by the AutoPi integration.

## Sensors

The AutoPi integration provides several types of sensors to monitor your vehicles and the integration itself.

### Integration Sensors

These sensors provide information about the AutoPi integration itself:

| Entity | Description | Category | Device Class | Unit | State Class | Icon |
|----------|----------|----------|----------|----------|----------|----------|
| FleetAlertCount | Sensor showing the total number of fleet alerts. | Diagnostic | - | alerts | Measurement | mdi:alert |
| UpdateDuration | Sensor showing the average duration of the last updates across all coordinators. | Diagnostic | - | s | Measurement | mdi:timer |
| TripCount | Sensor showing the total number of trips for a vehicle. | Diagnostic | - | trips | Total | mdi:map-marker-distance |
| LastTripDistance | Sensor showing the distance of the last trip. | Primary | Distance | KILOMETERS | Measurement | mdi:road-variant |
| DistanceSinceCodesClear | Distance since diagnostic codes cleared sensor. | Primary | - | - | - | - |

### Vehicle Status Sensors

These sensors provide general status information for each vehicle:

| Entity | Description | Category | Device Class | Unit | State Class | Icon |
|----------|----------|----------|----------|----------|----------|----------|
| Count | Sensor showing the total number of vehicles. | Diagnostic | - | vehicles | Measurement | mdi:car-multiple |
| AutoPiVehicleSensor | Sensor representing an individual vehicle. | Primary | - | - | - | mdi:car |

### GPS/Position Sensors

These sensors provide GPS and position data for each vehicle:

| Entity | Description | Category | Device Class | Unit | State Class | Icon |
|----------|----------|----------|----------|----------|----------|----------|
| GPSAltitude | GPS altitude sensor. | Primary | - | - | - | - |
| GPSSpeed | GPS speed sensor. | Primary | - | - | - | - |
| GPSCourse | GPS course/heading sensor. | Primary | - | - | - | - |
| GPSSatellites | GPS satellites sensor. | Primary | - | - | - | - |
| GPSLatitude | GPS latitude sensor. | Primary | - | - | - | - |
| GPSLongitude | GPS longitude sensor. | Primary | - | - | - | - |
| FuelUsedGPS | Fuel used GPS sensor. | Primary | - | - | - | - |
| FuelRateGPS | Fuel rate GPS sensor. | Primary | - | - | - | - |

### Battery Sensors

These sensors provide battery information for vehicles and devices:

| Entity | Description | Category | Device Class | Unit | State Class | Icon |
|----------|----------|----------|----------|----------|----------|----------|
| BatteryChargeLevel | Battery charge level sensor. | Primary | - | - | - | - |
| BatteryVoltage | Battery voltage sensor. | Primary | - | - | - | - |
| BatteryCurrent | Battery current sensor. | Primary | - | - | - | - |
| BatteryLevel | Tracker battery level sensor. | Primary | - | - | - | - |
| BatteryVoltage | Vehicle system battery voltage sensor. | Primary | - | - | - | - |

### Engine & Performance Sensors

These sensors provide engine and performance data:

| Entity | Description | Category | Device Class | Unit | State Class | Icon |
|----------|----------|----------|----------|----------|----------|----------|
| IgnitionState | Ignition state sensor. | Primary | - | - | - | - |
| Engine | Engine RPM sensor. | Primary | - | - | - | - |
| EngineLoad | Engine load sensor. | Primary | - | - | - | - |
| EngineRunTime | Engine run time sensor. | Primary | - | - | - | - |
| ThrottlePosition | Throttle position sensor. | Primary | - | - | - | - |
| OBDSpeed | OBD speed sensor. | Primary | - | - | - | - |

### Fuel Sensors

These sensors provide fuel consumption and level data:

| Entity | Description | Category | Device Class | Unit | State Class | Icon |
|----------|----------|----------|----------|----------|----------|----------|
| FuelUsedGPS | Fuel used GPS sensor. | Primary | - | - | - | - |
| FuelRateGPS | Fuel rate GPS sensor. | Primary | - | - | - | - |
| FuelLevel | Fuel level sensor. | Primary | - | - | - | - |
| OEMFuelLevel | OEM fuel level sensor. | Primary | - | - | - | - |

### Distance & Odometer Sensors

These sensors provide distance and odometer readings:

| Entity | Description | Category | Device Class | Unit | State Class | Icon |
|----------|----------|----------|----------|----------|----------|----------|
| TripCount | Sensor showing the total number of trips for a vehicle. | Diagnostic | - | trips | Total | mdi:map-marker-distance |
| LastTripDistance | Sensor showing the distance of the last trip. | Primary | Distance | KILOMETERS | Measurement | mdi:road-variant |
| TotalOdometer | Total odometer sensor. | Primary | - | - | - | - |
| TripOdometer | Trip odometer sensor. | Primary | - | - | - | - |
| DistanceSinceCodesClear | Distance since diagnostic codes cleared sensor. | Primary | - | - | - | - |

### Temperature Sensors

These sensors provide various temperature readings:

| Entity | Description | Category | Device Class | Unit | State Class | Icon |
|----------|----------|----------|----------|----------|----------|----------|
| AmbientTemperature | Ambient air temperature sensor. | Primary | - | - | - | - |
| IntakeTemperature | Intake air temperature sensor. | Primary | - | - | - | - |
| CoolantTemperature | Engine coolant temperature sensor. | Primary | - | - | - | - |

### Motion & Tracking Sensors

These sensors provide motion and tracking data:

| Entity | Description | Category | Device Class | Unit | State Class | Icon |
|----------|----------|----------|----------|----------|----------|----------|
| BatteryLevel | Tracker battery level sensor. | Primary | - | - | - | - |
| AccelerometerX | X-axis accelerometer sensor. | Primary | - | - | - | - |
| AccelerometerY | Y-axis accelerometer sensor. | Primary | - | - | - | - |
| AccelerometerZ | Z-axis accelerometer sensor. | Primary | - | - | - | - |
| Speed | Tracker-derived speed sensor. | Primary | - | - | - | - |

### Diagnostic Sensors

These sensors provide diagnostic information:

| Entity | Description | Category | Device Class | Unit | State Class | Icon |
|----------|----------|----------|----------|----------|----------|----------|
| UpdateDuration | Sensor showing the average duration of the last updates across all coordinators. | Diagnostic | - | s | Measurement | mdi:timer |
| GSMSignal | GSM signal strength sensor. | Primary | - | - | - | - |
| DTCCount | Diagnostic trouble code count sensor. | Primary | - | - | - | - |

## Data Field Sensor Reference

This table shows all data field sensors with their corresponding AutoPi field IDs:

| Entity | Field ID | Description | Category | Device Class | Unit | State Class | Icon |
|----------|----------|----------|----------|----------|----------|----------|----------|
| BatteryChargeLevel | obd.bat.level | Battery charge level sensor. | Primary | - | - | - | - |
| BatteryVoltage | obd.bat.voltage | Battery voltage sensor. | Primary | - | - | - | - |
| BatteryCurrent | std.battery_current.value | Battery current sensor. | Primary | - | - | - | - |
| BatteryLevel | std.battery_level.value | Tracker battery level sensor. | Primary | - | - | - | - |
| BatteryVoltage | std.battery_voltage.value | Vehicle system battery voltage sensor. | Primary | - | - | - | - |
| AccelerometerX | std.accelerometer_axis_x.value | X-axis accelerometer sensor. | Primary | - | - | - | - |
| AccelerometerY | std.accelerometer_axis_y.value | Y-axis accelerometer sensor. | Primary | - | - | - | - |
| AccelerometerZ | std.accelerometer_axis_z.value | Z-axis accelerometer sensor. | Primary | - | - | - | - |
| TotalOdometer | std.total_odometer.value | Total odometer sensor. | Primary | - | - | - | - |
| TripOdometer | std.trip_odometer.value | Trip odometer sensor. | Primary | - | - | - | - |
| DistanceSinceCodesClear | obd.distance_since_codes_clear.value | Distance since diagnostic codes cleared sensor. | Primary | - | - | - | - |
| FuelUsedGPS | std.fuel_used_gps.value | Fuel used GPS sensor. | Primary | - | - | - | - |
| FuelRateGPS | std.fuel_rate_gps.value | Fuel rate GPS sensor. | Primary | - | - | - | - |
| FuelLevel | obd.fuel_level.value | Fuel level sensor. | Primary | - | - | - | - |
| OEMFuelLevel | obd.obd_oem_fuel_level.value | OEM fuel level sensor. | Primary | - | - | - | - |
| IgnitionState | std.ignition.value | Ignition state sensor. | Primary | - | - | - | - |
| Engine | obd.rpm.value | Engine RPM sensor. | Primary | - | - | - | - |
| EngineLoad | obd.engine_load.value | Engine load sensor. | Primary | - | - | - | - |
| EngineRunTime | obd.run_time.value | Engine run time sensor. | Primary | - | - | - | - |
| ThrottlePosition | obd.throttle_pos.value | Throttle position sensor. | Primary | - | - | - | - |
| OBDSpeed | obd.speed.value | OBD speed sensor. | Primary | - | - | - | - |
| Speed | std.speed.value | Tracker-derived speed sensor. | Primary | - | - | - | - |
| AmbientTemperature | obd.ambient_air_temp.value | Ambient air temperature sensor. | Primary | - | - | - | - |
| IntakeTemperature | obd.intake_temp.value | Intake air temperature sensor. | Primary | - | - | - | - |
| CoolantTemperature | obd.coolant_temp.value | Engine coolant temperature sensor. | Primary | - | - | - | - |
| GSMSignal | std.gsm_signal.value | GSM signal strength sensor. | Primary | - | - | - | - |
| DTCCount | obd.number_of_dtc.value | Diagnostic trouble code count sensor. | Primary | - | - | - | - |

## Device Trackers

Device trackers provide GPS-based location tracking for your vehicles:

| Entity | Description | Category | Device Class | Unit | State Class | Icon |
|----------|----------|----------|----------|----------|----------|----------|
| Device | Representation of an AutoPi vehicle tracker. | Primary | - | - | - | - |

## Binary Sensors

Binary sensors provide on/off state information:

No binary sensor entities are currently implemented.

## Base Classes

The AutoPi integration uses the following base classes for entity implementation:

### AutoPiDataFieldSensorBase

Base class for AutoPi data field sensors.

**Inherits from:** AutoPiVehicleEntity, SensorEntity

**Properties:**
- `native_value`: Return the sensor value.
- `available`: Return if entity is available.
- `extra_state_attributes`: Return extra state attributes.

### AutoPiDataFieldSensor

Data field sensor without auto-zero support.

**Inherits from:** AutoPiDataFieldSensorBase

### AutoPiAutoZeroDataFieldSensor

Data field sensor with auto-zero support and state restoration.

**Inherits from:** AutoPiDataFieldSensorBase, RestoreEntity

**Properties:**
- `native_value`: Return the sensor value.


## Entity Attributes

This section details the attributes available on each entity type.

### Common Attributes

All AutoPi entities inherit these common attributes:

| Attribute | Type | Description |
|-----------|------|-------------|
| `vehicle_id` | str | Unique AutoPi vehicle ID |
| `license_plate` | str | Vehicle registration number |
| `vin` | str | Vehicle Identification Number |
| `year` | int | Manufacturing year |
| `type` | str | Vehicle type (ICE, EV, etc.) |
| `battery_voltage` | float | Nominal battery voltage |
| `devices` | list[str] | List of associated AutoPi device IDs |

### Data Field Sensors

Data field sensors provide real-time vehicle telemetry with these additional attributes:

| Attribute | Type | Description |
|-----------|------|-------------|
| `frequency` | float | Update frequency in Hz |
| `last_seen` | datetime | Last time data was received |
| `field_id` | str | AutoPi field identifier |
| `data_type` | str | Data value type |
| `description` | str | Field description (if available) |
| `data_age_seconds` | int | Time since last update |

#### Auto-Zero Enabled Sensors

Sensors with auto-zero support include these additional attributes:

| Attribute | Type | Description |
|-----------|------|-------------|
| `auto_zero_enabled` | bool | Whether auto-zero is available for this metric |
| `auto_zero_active` | bool | Whether the value is currently zeroed |
| `auto_zero_last_zeroed` | datetime | When the metric was last zeroed |
| `auto_zero_cooldown_until` | datetime | When auto-zero can trigger again |

### Position Sensors

GPS and position sensors include:

| Attribute | Type | Description |
|-----------|------|-------------|
| `latitude` | float | Current latitude |
| `longitude` | float | Current longitude |
| `accuracy` | float | Position accuracy in meters |
| `satellites` | int | Number of GPS satellites |
| `last_position_update` | datetime | Last position update time |

### Integration Status Sensors

Integration monitoring sensors include:

| Attribute | Type | Description |
|-----------|------|-------------|
| `total_calls` | int | Total API calls made |
| `failed_calls` | int | Number of failed API calls |
| `success_rate` | float | API success percentage |
| `average_duration` | float | Average update duration |

## Entity Properties

Many entities expose additional properties that can be accessed programmatically:

### Sensor Properties

- `native_value`: The raw sensor value before any unit conversion
- `native_unit_of_measurement`: The sensor's native unit
- `device_class`: Home Assistant device class for UI representation
- `state_class`: Statistical state class (measurement, total, etc.)
- `available`: Whether the entity has recent valid data

### Device Tracker Properties

- `latitude`: Current GPS latitude
- `longitude`: Current GPS longitude
- `gps_accuracy`: Position accuracy in meters
- `battery_level`: Device battery percentage


## Entity Naming

All entities follow Home Assistant's entity naming conventions:

- **Integration entities**: Named with "AutoPi" prefix (e.g., "AutoPi Vehicle Count")
- **Vehicle entities**: Named with the vehicle name as prefix (e.g., "My Car Speed")
- **Unique IDs**: Generated using entry ID and entity-specific suffixes

## Entity Categories

Entities are categorized as follows:

- **Primary**: Main functional entities shown in default views
- **Diagnostic**: Technical entities for monitoring integration health

## Device Classes

Where applicable, entities use standard Home Assistant device classes for consistent representation and unit conversion:

- **Distance**: For altitude measurements
- **Speed**: For vehicle speed
- **Temperature**: For temperature readings (future)
- **Battery**: For battery-related sensors (future)

## State Classes

Entities use appropriate state classes for statistics and energy tracking:

- **Measurement**: Current state values
- **Total Increasing**: Cumulative counters
- **Total**: Reset-able totals

