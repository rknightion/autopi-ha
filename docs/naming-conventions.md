---
title: Entity Naming
description: Understanding and customizing entity names in the AutoPi integration
---

# Entity Naming

This guide explains how the AutoPi integration names entities and how you can customize them.

## Default Naming Conventions

The AutoPi integration follows Home Assistant's naming best practices for consistent and intuitive entity names.

### Device Names

Each vehicle becomes a device with this naming pattern:

| Vehicle Info | Device Name | Example |
|--------------|-------------|---------|
| Call Name set | Uses call name | `My Tesla` |
| License plate only | Uses license plate | `ABC-123` |
| Vehicle ID only | Uses vehicle ID | `Vehicle abc123` |

### Entity Naming Structure

Entities follow Home Assistant's `has_entity_name` pattern:

```
{device_name} {entity_name}
```

Examples:
- Device: `My Tesla`, Entity name: `Speed` → `My Tesla Speed`
- Device: `ABC-123`, Entity name: `Altitude` → `ABC-123 Altitude`

### Entity ID Generation

Entity IDs are automatically generated from names:

| Entity Name | Entity ID | Notes |
|-------------|-----------|-------|
| `My Tesla Speed` | `sensor.my_tesla_speed` | Spaces become underscores |
| `ABC-123 GPS Satellites` | `sensor.abc_123_gps_satellites` | Special chars become underscores |
| `AutoPi Vehicle Count` | `sensor.autopi_vehicle_count` | Integration-level entities |

## Entity Categories

### Vehicle Entities

Each vehicle gets these entities:

#### Primary Entities
| Entity Name | Entity ID Pattern | Purpose |
|-------------|------------------|---------|
| `Status` | `sensor.{vehicle}_status` | Vehicle license plate/name |
| `Tracker` | `device_tracker.{vehicle}` | GPS location tracking |
| `Speed` | `sensor.{vehicle}_speed` | Current speed |
| `Altitude` | `sensor.{vehicle}_altitude` | Height above sea level |
| `Course` | `sensor.{vehicle}_course` | Direction of travel |
| `GPS Satellites` | `sensor.{vehicle}_gps_satellites` | Number of satellites |

#### Diagnostic Entities
| Entity Name | Entity ID Pattern | Purpose |
|-------------|------------------|---------|
| `Latitude` | `sensor.{vehicle}_latitude` | GPS latitude coordinate |
| `Longitude` | `sensor.{vehicle}_longitude` | GPS longitude coordinate |

### Integration Entities

Integration-wide entities with consistent naming:

| Entity Name | Entity ID | Category |
|-------------|-----------|----------|
| `AutoPi Vehicle Count` | `sensor.autopi_vehicle_count` | Diagnostic |
| `AutoPi API Calls` | `sensor.autopi_api_calls` | Diagnostic |
| `AutoPi Failed API Calls` | `sensor.autopi_failed_api_calls` | Diagnostic |
| `AutoPi API Success Rate` | `sensor.autopi_api_success_rate` | Diagnostic |
| `AutoPi Update Duration` | `sensor.autopi_update_duration` | Diagnostic |

## Customizing Entity Names

### Using Home Assistant UI

You can customize entity names through the Home Assistant interface:

1. **Navigate to Entity**:
   - Go to **Settings** → **Devices & Services**
   - Find **AutoPi** integration
   - Click on a device to see its entities

2. **Edit Entity**:
   - Click on an entity
   - Click the **Settings** icon (gear)
   - Modify **Name** field
   - Click **Update**

### Bulk Customization

For multiple entities, use the Entity Registry:

1. **Navigate to Entities**:
   - Go to **Settings** → **Devices & Services**
   - Click **Entities** tab
   - Filter by "autopi" domain

2. **Select and Edit**:
   - Select multiple entities
   - Use bulk edit functions
   - Apply consistent naming patterns

### YAML Configuration

While entities are created dynamically, you can use customizations:

```yaml
# configuration.yaml
homeassistant:
  customize:
    sensor.my_tesla_speed:
      friendly_name: "Tesla Current Speed"
      icon: mdi:speedometer-medium
    
    device_tracker.my_tesla:
      friendly_name: "Tesla Location"
      icon: mdi:car-electric
    
    sensor.my_tesla_gps_satellites:
      friendly_name: "Tesla GPS Quality"
```

## Naming Best Practices

### Consistent Patterns

Use consistent naming across all vehicles:

#### Pattern Examples
```yaml
# Speed sensors
sensor.family_car_speed
sensor.work_truck_speed
sensor.motorcycle_speed

# Device trackers  
device_tracker.family_car
device_tracker.work_truck
device_tracker.motorcycle
```

#### Avoid These Patterns
```yaml
# Inconsistent naming
sensor.car_speed           # Too generic
sensor.my_awesome_car_spd  # Abbreviations
sensor.vehicle_123_speed   # Technical IDs
```

### Descriptive Names

Make names meaningful for your household:

#### Good Examples
- `Family Car` instead of `Vehicle 1`
- `Dad's Truck` instead of `ABC-123`
- `Teen Driver Car` instead of `Honda Civic`

#### Context-Appropriate Names
- **Family use**: `Mom's Car`, `Kids' Van`
- **Fleet use**: `Delivery Truck 1`, `Service Van A`
- **Personal use**: `Daily Driver`, `Weekend Car`

### Special Characters

Handle special characters in vehicle names:

| Original Name | Recommended | Entity ID Result |
|---------------|-------------|------------------|
| `Mom's Car` | `Mom Car` | `sensor.mom_car_speed` |
| `Car #1` | `Car 1` | `sensor.car_1_speed` |
| `Work/Personal` | `Work Personal` | `sensor.work_personal_speed` |

## Troubleshooting Naming Issues

### Common Problems

#### Duplicate Entity IDs
**Symptoms**: Entities not appearing or numbered with `_2`, `_3`

**Causes**:
- Multiple vehicles with similar names
- Conflicts with existing entities
- Special character handling

**Solutions**:
1. Rename vehicles in AutoPi dashboard
2. Customize entity names in Home Assistant
3. Remove conflicting entities if safe

#### Unclear Entity Names
**Symptoms**: Hard to identify which vehicle an entity represents

**Solutions**:
1. Use descriptive vehicle names in AutoPi
2. Customize entity friendly names
3. Use consistent naming patterns

#### Entity ID Changes
**Symptoms**: Automations break after name changes

**Solutions**:
1. Update automations with new entity IDs
2. Use friendly names in automations when possible
3. Plan naming changes carefully

### Entity Registry Issues

#### Orphaned Entities
If entities remain after vehicle removal:

1. **Manual Cleanup**:
   - Go to **Settings** → **Devices & Services** → **Entities**
   - Filter for orphaned AutoPi entities
   - Remove unwanted entities

2. **Integration Reload**:
   - Reload the AutoPi integration
   - Check for proper cleanup

#### Lost Customizations
If entity customizations disappear:

1. **Backup Customizations**:
   ```yaml
   # Save to configuration.yaml
   homeassistant:
     customize: !include customize.yaml
   ```

2. **Restore from Backup**:
   - Use Home Assistant backup system
   - Restore entity registry if needed

## Advanced Naming Strategies

### Multi-Vehicle Households

For families with multiple vehicles:

#### Naming Strategy 1: User-Based
```
- Mom's Car
- Dad's Truck  
- Teen's Car
- Family Van
```

#### Naming Strategy 2: Purpose-Based
```
- Daily Driver
- Work Vehicle
- Weekend Car
- Emergency Backup
```

#### Naming Strategy 3: Model-Based
```
- Tesla Model 3
- Honda Pilot
- Toyota Prius
- Ford F-150
```

### Fleet Management

For business or fleet use:

#### Geographic Naming
```
- North Region Van
- South Region Truck
- Downtown Delivery
- Suburban Service
```

#### Functional Naming
```
- Delivery Vehicle 1
- Service Truck A
- Manager Vehicle
- Backup Unit
```

### Integration with Other Systems

#### Dashboard Organization
Group entities logically in dashboards:

```yaml
# Dashboard card
type: entities
title: Vehicle Speeds
entities:
  - sensor.family_car_speed
  - sensor.work_truck_speed
  - sensor.teen_car_speed
```

#### Automation Patterns
Use consistent naming in automations:

```yaml
# Template for all vehicles
- alias: "Vehicle Arrived Home"
  trigger:
    - platform: zone
      entity_id: 
        - device_tracker.family_car
        - device_tracker.work_truck
        - device_tracker.teen_car
      zone: zone.home
      event: enter
```

## Future Naming Features

### Planned Improvements

#### Smart Name Detection
- Automatic extraction of meaningful names from vehicle data
- Integration with vehicle manufacturer APIs
- Improved handling of special characters

#### Naming Templates
- Configurable naming patterns
- Consistent naming across all entities
- Bulk rename operations

#### Localization Support
- Multi-language entity names
- Regional naming conventions
- Cultural naming preferences

### Migration Support

When naming conventions change:
- Automatic entity ID migration
- Backward compatibility
- Clear migration documentation 