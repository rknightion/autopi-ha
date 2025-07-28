# Entity Reference

This page provides a comprehensive reference of all entities provided by the AutoPi integration.

## Sensors

The AutoPi integration provides several types of sensors to monitor your vehicles and the integration itself.

### Integration Sensors

These sensors provide information about the AutoPi integration itself:

| Entity | Description | Category | Device Class | Unit | State Class | Icon |
|--------|-------------|----------|--------------|------|-------------|------|
| FleetAlertCount | Sensor showing the total number of fleet alerts. | Diagnostic | - | alerts | Measurement | mdi:alert |
| APICalls | Sensor showing the total number of API calls across all coordinators. | Diagnostic | - | - | Total_Increasing | mdi:api |
| FailedAPICalls | Sensor showing the number of failed API calls across all coordinators. | Diagnostic | - | - | Total_Increasing | mdi:alert-circle |
| SuccessRate | Sensor showing the API success rate across all coordinators. | Diagnostic | - | % | Measurement | mdi:percent |
| UpdateDuration | Sensor showing the average duration of the last updates across all coordinators. | Diagnostic | - | s | Measurement | mdi:timer |
| TripCount | Sensor showing the total number of trips for a vehicle. | Diagnostic | - | trips | Total | mdi:map-marker-distance |
| LastTripDistance | Sensor showing the distance of the last trip. | Primary | - | km | Measurement | mdi:road-variant |
| DistanceSinceCodesClear | Distance since diagnostic codes cleared sensor. | Primary | - | - | - | - |

### Vehicle Status Sensors

These sensors provide general status information for each vehicle:

| Entity | Description | Category | Device Class | Unit | State Class | Icon |
|--------|-------------|----------|--------------|------|-------------|------|
| Count | Sensor showing the total number of vehicles. | Diagnostic | - | vehicles | Measurement | mdi:car-multiple |
| AutoPiVehicleSensor | Sensor representing an individual vehicle. | Primary | - | - | - | mdi:car |

### GPS/Position Sensors

These sensors provide GPS and position data for each vehicle:

| Entity | Description | Category | Device Class | Unit | State Class | Icon |
|--------|-------------|----------|--------------|------|-------------|------|
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
|--------|-------------|----------|--------------|------|-------------|------|
| BatteryChargeLevel | Battery charge level sensor. | Primary | - | - | - | - |
| BatteryVoltage | Battery voltage sensor. | Primary | - | - | - | - |
| BatteryCurrent | Battery current sensor. | Primary | - | - | - | - |
| BatteryLevel | Tracker battery level sensor. | Primary | - | - | - | - |
| BatteryVoltage | Vehicle system battery voltage sensor. | Primary | - | - | - | - |

### Engine & Performance Sensors

These sensors provide engine and performance data:

| Entity | Description | Category | Device Class | Unit | State Class | Icon |
|--------|-------------|----------|--------------|------|-------------|------|
| IgnitionState | Ignition state sensor. | Primary | - | - | - | - |
| Engine | Engine RPM sensor. | Primary | - | - | - | - |
| EngineLoad | Engine load sensor. | Primary | - | - | - | - |
| EngineRunTime | Engine run time sensor. | Primary | - | - | - | - |
| ThrottlePosition | Throttle position sensor. | Primary | - | - | - | - |
| OBDSpeed | OBD speed sensor. | Primary | - | - | - | - |

### Fuel Sensors

These sensors provide fuel consumption and level data:

| Entity | Description | Category | Device Class | Unit | State Class | Icon |
|--------|-------------|----------|--------------|------|-------------|------|
| FuelUsedGPS | Fuel used GPS sensor. | Primary | - | - | - | - |
| FuelRateGPS | Fuel rate GPS sensor. | Primary | - | - | - | - |
| FuelLevel | Fuel level sensor. | Primary | - | - | - | - |
| OEMFuelLevel | OEM fuel level sensor. | Primary | - | - | - | - |

### Distance & Odometer Sensors

These sensors provide distance and odometer readings:

| Entity | Description | Category | Device Class | Unit | State Class | Icon |
|--------|-------------|----------|--------------|------|-------------|------|
| TripCount | Sensor showing the total number of trips for a vehicle. | Diagnostic | - | trips | Total | mdi:map-marker-distance |
| LastTripDistance | Sensor showing the distance of the last trip. | Primary | - | km | Measurement | mdi:road-variant |
| TotalOdometer | Total odometer sensor. | Primary | - | - | - | - |
| TripOdometer | Trip odometer sensor. | Primary | - | - | - | - |
| DistanceSinceCodesClear | Distance since diagnostic codes cleared sensor. | Primary | - | - | - | - |

### Temperature Sensors

These sensors provide various temperature readings:

| Entity | Description | Category | Device Class | Unit | State Class | Icon |
|--------|-------------|----------|--------------|------|-------------|------|
| AmbientTemperature | Ambient air temperature sensor. | Primary | - | - | - | - |
| IntakeTemperature | Intake air temperature sensor. | Primary | - | - | - | - |
| CoolantTemperature | Engine coolant temperature sensor. | Primary | - | - | - | - |

### Motion & Tracking Sensors

These sensors provide motion and tracking data:

| Entity | Description | Category | Device Class | Unit | State Class | Icon |
|--------|-------------|----------|--------------|------|-------------|------|
| BatteryLevel | Tracker battery level sensor. | Primary | - | - | - | - |
| AccelerometerX | X-axis accelerometer sensor. | Primary | - | - | - | - |
| AccelerometerY | Y-axis accelerometer sensor. | Primary | - | - | - | - |
| AccelerometerZ | Z-axis accelerometer sensor. | Primary | - | - | - | - |
| Speed | Tracker-derived speed sensor. | Primary | - | - | - | - |

### Diagnostic Sensors

These sensors provide diagnostic information:

| Entity | Description | Category | Device Class | Unit | State Class | Icon |
|--------|-------------|----------|--------------|------|-------------|------|
| APICalls | Sensor showing the total number of API calls across all coordinators. | Diagnostic | - | - | Total_Increasing | mdi:api |
| FailedAPICalls | Sensor showing the number of failed API calls across all coordinators. | Diagnostic | - | - | Total_Increasing | mdi:alert-circle |
| SuccessRate | Sensor showing the API success rate across all coordinators. | Diagnostic | - | % | Measurement | mdi:percent |
| UpdateDuration | Sensor showing the average duration of the last updates across all coordinators. | Diagnostic | - | s | Measurement | mdi:timer |
| GSMSignal | GSM signal strength sensor. | Primary | - | - | - | - |
| DTCCount | Diagnostic trouble code count sensor. | Primary | - | - | - | - |

## Device Trackers

Device trackers provide GPS-based location tracking for your vehicles:

| Entity | Description | Category | Device Class | Unit | State Class | Icon |
|--------|-------------|----------|--------------|------|-------------|------|
| Device | Representation of an AutoPi vehicle tracker. | Primary | - | - | - | - |

## Binary Sensors

Binary sensors provide on/off state information:

No binary sensor entities are currently implemented.

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

