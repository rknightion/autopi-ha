# Entity Reference

This page provides a comprehensive reference of all entities provided by the AutoPi integration.

## Sensors

The AutoPi integration provides integration-level sensors and vehicle-level sensors. Data field sensors
are created dynamically based on the telemetry fields reported by each vehicle.

### Integration Sensors

These sensors provide information about the AutoPi integration itself:

| Entity | Description | Category | Device Class | Unit | State Class | Icon |
|----------|----------|----------|----------|----------|----------|----------|
| Fleet Alert Count | Sensor showing the total number of fleet alerts. | Diagnostic | - | alerts | Measurement | mdi:alert |
| Fleet Vehicle Summary | Sensor showing fleet vehicle activity summary. | Diagnostic | - | vehicles | Measurement | - |
| Update Duration | Sensor showing the average duration of the last updates across all coordinators. | Diagnostic | - | s | Measurement | mdi:timer |
| Vehicle Count | Sensor showing the total number of vehicles. | Diagnostic | - | vehicles | Measurement | mdi:car-multiple |

### Vehicle Status & Trip Sensors

These sensors provide general status information for each vehicle:

| Entity | Description | Category | Device Class | Unit | State Class | Icon |
|----------|----------|----------|----------|----------|----------|----------|
| Event Volume | Sensor showing event volume for a tag and window. | Diagnostic | - | events | Measurement | - |
| Geofence Count | Sensor showing geofence count for a vehicle. | Diagnostic | - | geofences | Measurement | mdi:map-marker |
| Last Charge Duration | Sensor showing duration of the last charge session. | Diagnostic | Duration | SECONDS | Measurement | mdi:timer |
| Last Communication | Sensor showing last communication timestamp. | Diagnostic | Timestamp | - | - | mdi:clock |
| Last Trip Distance | Sensor showing the distance of the last trip. | Primary | Distance | KILOMETERS | Measurement | mdi:road-variant |
| Location Count | Sensor showing location count for a vehicle. | Diagnostic | - | locations | Measurement | mdi:map-marker-radius |
| Trip Average Speed | Sensor showing average trip speed. | Primary | Speed | KILOMETERS_PER_HOUR | Measurement | mdi:speedometer |
| Trip Count | Sensor showing the total number of trips for a vehicle. | Diagnostic | - | trips | Total | mdi:map-marker-distance |
| Trip Lifetime Distance | Sensor showing total lifetime trip distance. | Primary | Distance | KILOMETERS | Total Increasing | mdi:road-variant |
| Vehicle Alert Count | Sensor showing open alerts for a vehicle. | Diagnostic | - | alerts | Measurement | mdi:alert |
| Vehicle DTC Count | Sensor showing DTC count for a vehicle. | Diagnostic | - | codes | Measurement | mdi:alert-circle |
| Vehicle Last DTC | Sensor showing last DTC code. | Diagnostic | - | - | - | mdi:car-wrench |
| Vehicle Sensor | Sensor representing an individual vehicle. | Primary | - | - | - | mdi:car |

### Data Field Sensors

These sensors are created when the vehicle reports the corresponding telemetry fields:

#### GPS/Position Sensors

| Entity | Description | Category | Device Class | Unit | State Class | Icon |
|----------|----------|----------|----------|----------|----------|----------|
| GPS Altitude | GPS altitude sensor. | Primary | Distance | METERS | Measurement | mdi:elevation-rise |
| GPS Course | GPS course/heading sensor. | Primary | - | ° | Measurement | mdi:compass |
| GPS Latitude | GPS latitude sensor. | Diagnostic | - | - | Measurement | mdi:latitude |
| GPS Longitude | GPS longitude sensor. | Diagnostic | - | - | Measurement | mdi:longitude |
| GPS Precision | GPS precision/position quality sensor. | Primary | Distance | METERS | Measurement | mdi:crosshairs-gps |
| GPS Satellites | GPS satellites sensor. | Primary | - | - | Measurement | mdi:satellite-variant |
| GPS Speed | GPS speed sensor. | Primary | Speed | METERS_PER_SECOND | Measurement | mdi:speedometer |

#### Battery Sensors

| Entity | Description | Category | Device Class | Unit | State Class | Icon |
|----------|----------|----------|----------|----------|----------|----------|
| Battery Charge Level | Battery charge level sensor. | Primary | Battery | PERCENTAGE | Measurement | mdi:battery |
| Battery Charging State | Battery charging state sensor. | Primary | - | - | - | mdi:battery-charging |
| Battery Current | Battery current sensor. | Primary | Current | AMPERE | Measurement | mdi:current-dc |
| Battery Voltage | Battery voltage sensor. | Primary | Voltage | VOLT | Measurement | mdi:lightning-bolt |
| External Voltage | External/aux voltage sensor. | Diagnostic | Voltage | VOLT | Measurement | mdi:flash |
| Tracker Battery Level | Tracker battery level sensor. | Diagnostic | Battery | PERCENTAGE | Measurement | mdi:battery |
| Vehicle Battery Voltage | Vehicle system battery voltage sensor. | Primary | Voltage | VOLT | Measurement | mdi:car-battery |

#### Engine & Performance Sensors

| Entity | Description | Category | Device Class | Unit | State Class | Icon |
|----------|----------|----------|----------|----------|----------|----------|
| Engine | Engine RPM sensor. | Primary | - | rpm | Measurement | mdi:engine |
| Engine Load | Engine load sensor. | Primary | - | PERCENTAGE | Measurement | mdi:gauge |
| Engine Run Time | Engine run time sensor. | Primary | Duration | SECONDS | Measurement | mdi:timer |
| Ignition State | Ignition state sensor. | Primary | - | - | - | mdi:key |
| OBD Speed | OBD speed sensor. | Primary | Speed | KILOMETERS_PER_HOUR | Measurement | mdi:speedometer |
| Throttle Position | Throttle position sensor. | Primary | - | PERCENTAGE | Measurement | mdi:gas-pedal |

#### Fuel Sensors

| Entity | Description | Category | Device Class | Unit | State Class | Icon |
|----------|----------|----------|----------|----------|----------|----------|
| Fuel Level | Fuel level sensor. | Primary | - | PERCENTAGE | Measurement | mdi:gas-station |
| Fuel Rate ECU | Instantaneous fuel rate sensor from ECU. | Primary | Volume Flow Rate | LITERS_PER_HOUR | Measurement | mdi:fuel |
| Fuel Rate GPS | Fuel rate GPS sensor. | Primary | - | L/h | Measurement | mdi:fuel |
| Fuel Used GPS | Fuel used GPS sensor. | Primary | Volume | LITERS | Total Increasing | mdi:fuel |
| OEM Fuel Level | OEM fuel level sensor. | Primary | Volume Storage | LITERS | Measurement | mdi:fuel |

#### Distance & Odometer Sensors

| Entity | Description | Category | Device Class | Unit | State Class | Icon |
|----------|----------|----------|----------|----------|----------|----------|
| Distance Since Codes Clear | Distance since diagnostic codes cleared sensor. | Diagnostic | Distance | KILOMETERS | Total Increasing | mdi:road-variant |
| OEM Total Mileage | OEM total mileage sensor. | Primary | Distance | KILOMETERS | Total Increasing | mdi:counter |
| Total Odometer | Total odometer sensor. | Primary | Distance | KILOMETERS | Total Increasing | mdi:counter |
| Trip Odometer | Trip odometer sensor. | Primary | Distance | KILOMETERS | Total Increasing | mdi:map-marker-distance |

#### Temperature Sensors

| Entity | Description | Category | Device Class | Unit | State Class | Icon |
|----------|----------|----------|----------|----------|----------|----------|
| Ambient Temperature | Ambient air temperature sensor. | Primary | Temperature | CELSIUS | Measurement | mdi:thermometer |
| Coolant Temperature | Engine coolant temperature sensor. | Primary | Temperature | CELSIUS | Measurement | mdi:thermometer |
| Intake Temperature | Intake air temperature sensor. | Primary | Temperature | CELSIUS | Measurement | mdi:thermometer |

#### Motion & Tracking Sensors

| Entity | Description | Category | Device Class | Unit | State Class | Icon |
|----------|----------|----------|----------|----------|----------|----------|
| Accelerometer X | X-axis accelerometer sensor. | Primary | - | g | Measurement | mdi:axis-x-arrow |
| Accelerometer Y | Y-axis accelerometer sensor. | Primary | - | g | Measurement | mdi:axis-y-arrow |
| Accelerometer Z | Z-axis accelerometer sensor. | Primary | - | g | Measurement | mdi:axis-z-arrow |
| Tracker Speed | Tracker-derived speed sensor. | Primary | Speed | KILOMETERS_PER_HOUR | Measurement | mdi:speedometer |

#### Diagnostic Sensors

| Entity | Description | Category | Device Class | Unit | State Class | Icon |
|----------|----------|----------|----------|----------|----------|----------|
| DTC Count | Diagnostic trouble code count sensor. | Diagnostic | - | - | Measurement | mdi:alert-circle |
| GSM Signal | GSM signal strength sensor. | Diagnostic | - | PERCENTAGE | Measurement | mdi:signal |
| Timezone Offset | Timezone offset sensor. | Diagnostic | - | - | - | mdi:map-clock |


## Data Field Sensor Reference

This table shows all data field sensors with their corresponding AutoPi field IDs:

| Entity | Field ID | Description | Category | Device Class | Unit | State Class | Icon |
|----------|----------|----------|----------|----------|----------|----------|----------|
| Accelerometer X | std.accelerometer_axis_x.value | X-axis accelerometer sensor. | Primary | - | g | Measurement | mdi:axis-x-arrow |
| Accelerometer Y | std.accelerometer_axis_y.value | Y-axis accelerometer sensor. | Primary | - | g | Measurement | mdi:axis-y-arrow |
| Accelerometer Z | std.accelerometer_axis_z.value | Z-axis accelerometer sensor. | Primary | - | g | Measurement | mdi:axis-z-arrow |
| Ambient Temperature | obd.ambient_air_temp.value | Ambient air temperature sensor. | Primary | Temperature | CELSIUS | Measurement | mdi:thermometer |
| Battery Charge Level | obd.bat.level | Battery charge level sensor. | Primary | Battery | PERCENTAGE | Measurement | mdi:battery |
| Battery Charging State | obd.bat.state | Battery charging state sensor. | Primary | - | - | - | mdi:battery-charging |
| Battery Current | std.battery_current.value | Battery current sensor. | Primary | Current | AMPERE | Measurement | mdi:current-dc |
| Battery Voltage | obd.bat.voltage | Battery voltage sensor. | Primary | Voltage | VOLT | Measurement | mdi:lightning-bolt |
| Coolant Temperature | obd.coolant_temp.value | Engine coolant temperature sensor. | Primary | Temperature | CELSIUS | Measurement | mdi:thermometer |
| DTC Count | obd.number_of_dtc.value | Diagnostic trouble code count sensor. | Diagnostic | - | - | Measurement | mdi:alert-circle |
| Distance Since Codes Clear | obd.distance_since_codes_clear.value | Distance since diagnostic codes cleared sensor. | Diagnostic | Distance | KILOMETERS | Total Increasing | mdi:road-variant |
| Engine | obd.rpm.value | Engine RPM sensor. | Primary | - | rpm | Measurement | mdi:engine |
| Engine Load | obd.engine_load.value | Engine load sensor. | Primary | - | PERCENTAGE | Measurement | mdi:gauge |
| Engine Run Time | obd.run_time.value | Engine run time sensor. | Primary | Duration | SECONDS | Measurement | mdi:timer |
| External Voltage | std.external_voltage.value | External/aux voltage sensor. | Diagnostic | Voltage | VOLT | Measurement | mdi:flash |
| Fuel Level | obd.fuel_level.value | Fuel level sensor. | Primary | - | PERCENTAGE | Measurement | mdi:gas-station |
| Fuel Rate ECU | obd.fuel_rate.value | Instantaneous fuel rate sensor from ECU. | Primary | Volume Flow Rate | LITERS_PER_HOUR | Measurement | mdi:fuel |
| Fuel Rate GPS | std.fuel_rate_gps.value | Fuel rate GPS sensor. | Primary | - | L/h | Measurement | mdi:fuel |
| Fuel Used GPS | std.fuel_used_gps.value | Fuel used GPS sensor. | Primary | Volume | LITERS | Total Increasing | mdi:fuel |
| GPS Altitude | track.pos.alt | GPS altitude sensor. | Primary | Distance | METERS | Measurement | mdi:elevation-rise |
| GPS Course | track.pos.cog | GPS course/heading sensor. | Primary | - | ° | Measurement | mdi:compass |
| GPS Latitude | track.pos.loc | GPS latitude sensor. | Diagnostic | - | - | Measurement | mdi:latitude |
| GPS Longitude | track.pos.loc | GPS longitude sensor. | Diagnostic | - | - | Measurement | mdi:longitude |
| GPS Precision | track.pos.pr | GPS precision/position quality sensor. | Primary | Distance | METERS | Measurement | mdi:crosshairs-gps |
| GPS Satellites | track.pos.nsat | GPS satellites sensor. | Primary | - | - | Measurement | mdi:satellite-variant |
| GPS Speed | track.pos.sog | GPS speed sensor. | Primary | Speed | METERS_PER_SECOND | Measurement | mdi:speedometer |
| GSM Signal | std.gsm_signal.value | GSM signal strength sensor. | Diagnostic | - | PERCENTAGE | Measurement | mdi:signal |
| Ignition State | std.ignition.value | Ignition state sensor. | Primary | - | - | - | mdi:key |
| Intake Temperature | obd.intake_temp.value | Intake air temperature sensor. | Primary | Temperature | CELSIUS | Measurement | mdi:thermometer |
| OBD Speed | obd.speed.value | OBD speed sensor. | Primary | Speed | KILOMETERS_PER_HOUR | Measurement | mdi:speedometer |
| OEM Fuel Level | obd.obd_oem_fuel_level.value | OEM fuel level sensor. | Primary | Volume Storage | LITERS | Measurement | mdi:fuel |
| OEM Total Mileage | obd.obd_oem_total_mileage.value | OEM total mileage sensor. | Primary | Distance | KILOMETERS | Total Increasing | mdi:counter |
| Throttle Position | obd.throttle_pos.value | Throttle position sensor. | Primary | - | PERCENTAGE | Measurement | mdi:gas-pedal |
| Timezone Offset | std.tz_offset.value | Timezone offset sensor. | Diagnostic | - | - | - | mdi:map-clock |
| Total Odometer | std.total_odometer.value | Total odometer sensor. | Primary | Distance | KILOMETERS | Total Increasing | mdi:counter |
| Tracker Battery Level | std.battery_level.value | Tracker battery level sensor. | Diagnostic | Battery | PERCENTAGE | Measurement | mdi:battery |
| Tracker Speed | std.speed.value | Tracker-derived speed sensor. | Primary | Speed | KILOMETERS_PER_HOUR | Measurement | mdi:speedometer |
| Trip Odometer | std.trip_odometer.value | Trip odometer sensor. | Primary | Distance | KILOMETERS | Total Increasing | mdi:map-marker-distance |
| Vehicle Battery Voltage | std.battery_voltage.value | Vehicle system battery voltage sensor. | Primary | Voltage | VOLT | Measurement | mdi:car-battery |

## Device Trackers

Device trackers provide GPS-based location tracking for your vehicles:

| Entity | Description | Category | Device Class | Unit | State Class | Icon |
|----------|----------|----------|----------|----------|----------|----------|
| Device Tracker | Representation of an AutoPi vehicle tracker. | Primary | - | - | - | mdi:car |

## Binary Sensors

Binary sensors provide on/off state information:

| Entity | Field ID | Description | Category | Device Class | Unit | State Class | Icon |
|----------|----------|----------|----------|----------|----------|----------|----------|
| Battery Charging State | obd.bat.state | Battery charging binary sensor. | Primary | Battery Charging | - | - | mdi:battery-charging |
| Charging In Progress | - | Charging in progress binary sensor. | Primary | Battery Charging | - | - | mdi:battery-charging |
| Ignition Running | std.ignition.value | Ignition/engine running binary sensor. | Primary | Running | - | - | mdi:key |
| Movement | - | Vehicle movement binary sensor. | Primary | Moving | - | - | mdi:car-traction-control |
| Tracker Online | - | Tracker online/offline binary sensor. | Primary | Connectivity | - | - | mdi:access-point |

## Events

Event entities emit Home Assistant events for vehicle activity:

| Entity | Description | Category | Event Types |
|----------|----------|----------|----------|
| DTC Event | Event entity for DTC events. | Diagnostic | dtc |
| RFID Event | Event entity for RFID events. | Diagnostic | rfid_event |
| Simplified Event | Event entity for simplified AutoPi events. | Diagnostic | simplified_event |
| Vehicle Event | Event entity for AutoPi vehicle events. | Diagnostic | charging, charging_slow, discharging, critical_level, start, stop, engine_start, engine_stop, trip_start, trip_end, standstill, moving, alert, warning, error, unknown, unkown |

## Base Classes

The AutoPi integration uses the following base classes for entity implementation:

### AutoPiEntity

Base entity for AutoPi integration.

**Inherits from:** CoordinatorEntity, Entity

**Key Attributes:**
- `_attr_has_entity_name`: True

### AutoPiVehicleEntity

Base entity for a specific AutoPi vehicle.

**Inherits from:** AutoPiEntity

**Properties:**
- `vehicle`: Get the vehicle data.
- `device_info`: Return device information.
- `available`: Return if entity is available.
- `extra_state_attributes`: Return extra state attributes.

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

### AutoPiDataFieldBinarySensor

Base class for data field derived binary sensors.

**Inherits from:** AutoPiVehicleEntity, BinarySensorEntity

**Properties:**
- `available`: Return if entity is available.
- `extra_state_attributes`: Return extra state attributes.


## Entity Attributes

This section details the attributes available on each entity type.

### Vehicle Entity Attributes

Vehicle-based entities include these attributes:

| Attribute | Type | Description |
|-----------|------|-------------|
| `vehicle_id` | str | Unique AutoPi vehicle ID |
| `license_plate` | str | Vehicle registration number |
| `vin` | str | Vehicle Identification Number |
| `year` | int | Manufacturing year |
| `type` | str | Vehicle type (ICE, EV, etc.) |
| `battery_voltage` | float | Nominal battery voltage |
| `make_id` | str | AutoPi make identifier |
| `model_id` | str | AutoPi model identifier |
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
| `auto_zero_enabled` | bool | Whether auto-zero is available for this metric |

#### Auto-Zero Enabled Sensors

Sensors with auto-zero support include these additional attributes:

| Attribute | Type | Description |
|-----------|------|-------------|
| `auto_zero_active` | bool | Whether the value is currently zeroed |
| `auto_zero_last_zeroed` | datetime | When the metric was last zeroed |
| `auto_zero_cooldown_until` | datetime | When auto-zero can trigger again |

> Note: Some entities add extra attributes specific to their data (alerts, charging, events, etc.).
> Check the entity state in Home Assistant for the full list of available attributes.

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
- `location_accuracy`: Position accuracy in meters


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

- **Battery**: Battery level or charging state
- **Current**: Electrical current
- **Distance**: Distance and altitude measurements
- **Duration**: Time durations
- **Speed**: Vehicle speed
- **Temperature**: Temperature readings
- **Timestamp**: Time-based sensors
- **Connectivity**: Tracker connectivity (binary)
- **Moving**: Vehicle movement (binary)

## State Classes

Entities use appropriate state classes for statistics and energy tracking:

- **Measurement**: Current state values
- **Total Increasing**: Cumulative counters
- **Total**: Reset-able totals

