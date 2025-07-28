# Entity Reference

This page provides a comprehensive reference of all entities provided by the AutoPi integration.

## Sensors

The AutoPi integration provides several types of sensors to monitor your vehicles and the integration itself.

### Integration Sensors

These sensors provide information about the AutoPi integration itself:

| Entity | Description | Category | Device Class | Unit | State Class | Icon |
|--------|-------------|----------|--------------|------|-------------|------|
| APICalls | Sensor showing the total number of API calls. | Diagnostic | - | - | Total_Increasing | mdi:api |
| FailedAPICalls | Sensor showing the number of failed API calls. | Diagnostic | - | - | Total_Increasing | mdi:alert-circle |
| SuccessRate | Sensor showing the API success rate. | Diagnostic | - | % | Measurement | mdi:percent |
| UpdateDuration | Sensor showing the duration of the last update. | Diagnostic | - | s | Measurement | mdi:timer |

### Vehicle Sensors

These sensors provide information specific to each vehicle:

| Entity | Description | Category | Device Class | Unit | State Class | Icon |
|--------|-------------|----------|--------------|------|-------------|------|
| Count | Sensor showing the total number of vehicles. | Diagnostic | - | vehicles | Measurement | mdi:car-multiple |
| AutoPiVehicleSensor | Sensor representing an individual vehicle. | Primary | - | - | - | mdi:car |
| Altitude | Sensor representing a vehicle's altitude. | Primary | Distance | METERS | Measurement | mdi:elevation-rise |
| Speed | Sensor representing a vehicle's speed. | Primary | Speed | METERS_PER_SECOND | Measurement | mdi:speedometer |
| Course | Sensor representing a vehicle's course (direction). | Primary | - | ° | Measurement | mdi:compass |
| Satellites | Sensor representing the number of GPS satellites. | Primary | - | - | Measurement | mdi:satellite-variant |
| Latitude | Sensor representing a vehicle's latitude. | Diagnostic | - | - | Measurement | mdi:latitude |
| Longitude | Sensor representing a vehicle's longitude. | Diagnostic | - | - | Measurement | mdi:longitude |

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

