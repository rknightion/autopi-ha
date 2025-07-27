# AutoPi Entity Base Classes

## Overview

This directory contains the base entity classes for the AutoPi integration. All AutoPi entities should extend these base classes to ensure consistent behavior and proper integration with Home Assistant.

## Base Classes

### `AutoPiEntity`
The root base class for all AutoPi entities. Extends both `CoordinatorEntity` and `Entity`.

**Key Features:**
- Automatic coordinator integration
- Standardized unique ID generation
- Proper entity naming (`has_entity_name = True`)
- Debug logging for entity lifecycle

**Usage:**
```python
class MyAutoPiSensor(AutoPiEntity, SensorEntity):
    def __init__(self, coordinator, unique_suffix):
        super().__init__(coordinator, unique_suffix)
```

### `AutoPiVehicleEntity`
Base class for entities associated with a specific vehicle. Extends `AutoPiEntity`.

**Key Features:**
- Vehicle-specific device association
- Automatic device_info generation
- Vehicle data property access
- Rich attribute set with vehicle details
- Availability based on vehicle data presence

**Provided Attributes:**
- `vehicle_id`: AutoPi vehicle ID
- `license_plate`: Vehicle registration
- `vin`: Vehicle Identification Number
- `year`: Manufacturing year
- `type`: Vehicle type (ICE, EV, etc.)
- `battery_voltage`: Nominal battery voltage
- `make_id`: Manufacturer ID
- `model_id`: Model ID
- `devices`: Associated AutoPi device IDs

**Usage:**
```python
class VehicleSensor(AutoPiVehicleEntity, SensorEntity):
    def __init__(self, coordinator, vehicle_id):
        super().__init__(coordinator, vehicle_id, "sensor_type")
```

## Device Registry Integration

Vehicle entities automatically create devices in the Home Assistant device registry with:
- **Identifiers**: `(DOMAIN, f"vehicle_{vehicle_id}")`
- **Name**: Vehicle's `callName` or license plate
- **Manufacturer**: "AutoPi"
- **Model**: "{type} Vehicle" (e.g., "ICE Vehicle")
- **Configuration URL**: Link to AutoPi dashboard

## Entity Naming Convention

Entities use Home Assistant's entity naming system:
- Base name comes from the device (vehicle name)
- Entity-specific name set via `_attr_name` or `name` property
- Results in names like "Kiabbz Temperature" for a vehicle named "Kiabbz"

## Adding New Entity Types

### Step 1: Choose Base Class
- Use `AutoPiEntity` for integration-wide entities
- Use `AutoPiVehicleEntity` for vehicle-specific entities

### Step 2: Implement Required Properties
```python
class NewVehicleEntity(AutoPiVehicleEntity, EntityBaseClass):
    def __init__(self, coordinator, vehicle_id):
        super().__init__(coordinator, vehicle_id, "unique_suffix")
        self._attr_name = "Entity Name"  # Optional if using default
    
    @property
    def native_value(self):
        """Return the state value."""
        if vehicle := self.vehicle:
            return vehicle.some_property
        return None
```

### Step 3: Override Additional Properties as Needed
- `icon`: Entity icon
- `unit_of_measurement`: For numeric entities
- `device_class`: For standard entity types
- `state_class`: For statistical entities

## Best Practices

### Initialization
- Always call super().__init__() with proper parameters
- Set unique_id suffix that clearly identifies the entity type
- Use debug logging for troubleshooting

### Data Access
- Always check if vehicle data exists before accessing
- Use the provided `vehicle` property for safe access
- Return None when data is unavailable

### Attributes
- Extend `extra_state_attributes` rather than replacing
- Include only relevant attributes
- Consider attribute data size

### Availability
- Leverage the built-in availability logic
- Additional availability checks can be added if needed

## Future Enhancements

### Planned Base Classes
- `AutoPiDeviceEntity`: For AutoPi device-specific entities
- `AutoPiTripEntity`: For trip-related entities
- `AutoPiAlertEntity`: For alert/notification entities

### Additional Features
- Entity categories (diagnostic, config)
- Entity registry options
- Custom device classes
- Enhanced attribute management