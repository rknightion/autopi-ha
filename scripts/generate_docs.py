#!/usr/bin/env python3
"""Auto-generate entity documentation for the AutoPi integration."""

import ast
import re
from pathlib import Path
from typing import Any


def extract_class_info(file_path: Path) -> list[dict[str, Any]]:
    """Extract class information from a Python file."""
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return []

    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        print(f"Syntax error in {file_path}: {e}")
        return []

    classes = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            class_info = {
                "name": node.name,
                "docstring": ast.get_docstring(node),
                "attributes": {},
                "methods": {},
                "properties": {},
                "base_classes": [base.id if hasattr(base, "id") else str(base) for base in node.bases],
                "file": file_path.name,
                "init_params": []
            }

            # Extract __init__ parameters
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == "__init__":
                    # Skip self and common params
                    skip_params = {"self", "coordinator", "vehicle_id"}
                    for arg in item.args.args:
                        if arg.arg not in skip_params:
                            param_info = {"name": arg.arg, "type": None, "default": None}
                            
                            # Try to get type annotation
                            if arg.annotation:
                                if isinstance(arg.annotation, ast.Name):
                                    param_info["type"] = arg.annotation.id
                                elif isinstance(arg.annotation, ast.Constant):
                                    param_info["type"] = str(arg.annotation.value)
                                    
                            class_info["init_params"].append(param_info)

            # Extract class attributes and their values
            for item in node.body:
                if isinstance(item, ast.Assign):
                    for target in item.targets:
                        if isinstance(target, ast.Name):
                            attr_name = target.id
                            attr_value = None

                            # Try to extract the value
                            if isinstance(item.value, ast.Constant):
                                attr_value = item.value.value
                            elif isinstance(item.value, ast.Name):
                                attr_value = item.value.id
                            elif isinstance(item.value, ast.Attribute):
                                # Handle things like SensorDeviceClass.SPEED
                                attr_value = f"{item.value.value.id}.{item.value.attr}" if hasattr(item.value.value, "id") else str(item.value)
                            elif isinstance(item.value, ast.Str):
                                attr_value = item.value.s

                            class_info["attributes"][attr_name] = attr_value

                # Extract method and property information
                elif isinstance(item, ast.FunctionDef):
                    method_docstring = ast.get_docstring(item)
                    is_property = any(isinstance(d, ast.Name) and d.id == "property" for d in item.decorator_list)
                    
                    method_info = {
                        "docstring": method_docstring,
                        "property": is_property,
                        "returns": None
                    }
                    
                    # Try to extract return type from annotation
                    if item.returns:
                        if isinstance(item.returns, ast.Name):
                            method_info["returns"] = item.returns.id
                        elif isinstance(item.returns, ast.Constant):
                            method_info["returns"] = str(item.returns.value)
                    
                    if is_property:
                        class_info["properties"][item.name] = method_info
                    else:
                        class_info["methods"][item.name] = method_info

            classes.append(class_info)

    return classes

def get_entity_description(class_info: dict[str, Any]) -> str:
    """Generate a description for an entity class."""
    docstring = class_info.get("docstring", "")
    if docstring:
        # Extract first line of docstring
        first_line = docstring.split("\n")[0].strip()
        if first_line:
            return first_line

    # Fallback: generate from class name
    name = class_info["name"]
    if "Vehicle" in name and "Sensor" in name:
        sensor_type = name.replace("AutoPiVehicle", "").replace("Sensor", "")
        return f"Sensor for vehicle {sensor_type.lower()}"
    elif "Sensor" in name:
        sensor_type = name.replace("AutoPi", "").replace("Sensor", "")
        return f"Sensor for {sensor_type.lower()}"
    elif "Tracker" in name:
        return "GPS-based device tracker for vehicle location"

    return "AutoPi entity"

def get_entity_category(class_info: dict[str, Any]) -> str:
    """Determine entity category."""
    entity_category = class_info["attributes"].get("_attr_entity_category")
    if entity_category == "EntityCategory.DIAGNOSTIC":
        return "Diagnostic"
    return "Primary"

def get_device_class(class_info: dict[str, Any]) -> str | None:
    """Get device class if specified."""
    device_class = class_info["attributes"].get("_attr_device_class")
    if device_class:
        # Clean up the device class name
        if "." in device_class:
            return device_class.split(".")[-1].title()
        return device_class
    return None

def get_unit_of_measurement(class_info: dict[str, Any]) -> str | None:
    """Get unit of measurement if specified."""
    unit = class_info["attributes"].get("_attr_native_unit_of_measurement")
    if unit:
        # Clean up unit names
        if "." in unit:
            return unit.split(".")[-1]
        return unit
    return None

def get_state_class(class_info: dict[str, Any]) -> str | None:
    """Get state class if specified."""
    state_class = class_info["attributes"].get("_attr_state_class")
    if state_class:
        if "." in state_class:
            return state_class.split(".")[-1].title()
        return state_class
    return None

def get_icon(class_info: dict[str, Any]) -> str | None:
    """Get icon if specified."""
    return class_info["attributes"].get("_attr_icon")

def extract_field_id_mapping(file_path: Path) -> dict[str, str]:
    """Extract field ID to sensor class mapping from data_field_sensors.py."""
    mapping = {}
    
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
        
        # Find the FIELD_ID_TO_SENSOR_CLASS dictionary
        match = re.search(r'FIELD_ID_TO_SENSOR_CLASS[^{]*{([^}]+)}', content, re.DOTALL)
        if match:
            dict_content = match.group(1)
            # Extract field_id: ClassName pairs
            pairs = re.findall(r'"([^"]+)":\s*(\w+)', dict_content)
            for field_id, class_name in pairs:
                mapping[class_name] = field_id
    except Exception as e:
        print(f"Failed to extract field ID mapping: {e}")
    
    return mapping

def get_all_attributes(class_info: dict[str, Any], all_classes: list[dict[str, Any]]) -> dict[str, Any]:
    """Get all attributes including inherited ones."""
    attributes = {}
    
    # Get attributes from base classes recursively
    for base_name in class_info.get("base_classes", []):
        for cls in all_classes:
            if cls["name"] == base_name:
                base_attrs = get_all_attributes(cls, all_classes)
                attributes.update(base_attrs)
                break
    
    # Add this class's attributes (overwrites inherited ones)
    attributes.update(class_info.get("attributes", {}))
    
    return attributes

def get_all_properties(class_info: dict[str, Any], all_classes: list[dict[str, Any]]) -> dict[str, Any]:
    """Get all properties including inherited ones."""
    properties = {}
    
    # Get properties from base classes recursively
    for base_name in class_info.get("base_classes", []):
        for cls in all_classes:
            if cls["name"] == base_name:
                base_props = get_all_properties(cls, all_classes)
                properties.update(base_props)
                break
    
    # Add this class's properties
    properties.update(class_info.get("properties", {}))
    
    return properties

def generate_entity_attributes_table(entities: list[dict[str, Any]], all_classes: list[dict[str, Any]]) -> str:
    """Generate a detailed attributes table for entities."""
    if not entities:
        return ""
    
    # Collect all unique attributes across all entities
    all_attrs = set()
    entity_attrs = {}
    
    for entity in entities:
        attrs = get_all_attributes(entity, all_classes)
        entity_attrs[entity["name"]] = attrs
        all_attrs.update(attrs.keys())
    
    # Filter out private attributes
    public_attrs = [attr for attr in sorted(all_attrs) if not attr.startswith("_")]
    
    if not public_attrs:
        return "No public attributes defined.\n"
    
    # Create table
    table = "| Entity | " + " | ".join(public_attrs) + " |\n"
    table += "|--------|" + "|".join(["--------" for _ in public_attrs]) + "|\n"
    
    for entity in entities:
        attrs = entity_attrs.get(entity["name"], {})
        name = entity["name"].replace("AutoPi", "").replace("Vehicle", "").replace("Sensor", "").replace("Tracker", "")
        if not name:
            name = entity["name"]
        
        row = f"| {name} |"
        for attr in public_attrs:
            value = attrs.get(attr, "-")
            if value and isinstance(value, str) and len(value) > 20:
                value = value[:17] + "..."
            row += f" {value} |"
        
        table += row + "\n"
    
    return table

def generate_entity_table(entities: list[dict[str, Any]], entity_type: str, include_field_id: bool = False, field_id_mapping: dict[str, str] = None) -> str:
    """Generate a markdown table for entities."""
    if not entities:
        return f"No {entity_type.lower()} entities are currently implemented.\n"

    # Create table header
    headers = ["Entity", "Description", "Category", "Device Class", "Unit", "State Class", "Icon"]
    if include_field_id:
        headers.insert(1, "Field ID")
    
    table = "| " + " | ".join(headers) + " |\n"
    table += "|" + "|".join(["-" * 10 for _ in headers]) + "|\n"

    for entity in entities:
        name = entity["name"].replace("AutoPi", "").replace("Vehicle", "").replace("Sensor", "").replace("Tracker", "")
        if not name:
            name = entity["name"]

        description = get_entity_description(entity)
        category = get_entity_category(entity)
        device_class = get_device_class(entity) or "-"
        unit = get_unit_of_measurement(entity) or "-"
        state_class = get_state_class(entity) or "-"
        icon = get_icon(entity) or "-"
        
        # Extract field_id from mapping if available
        field_id = "-"
        if include_field_id and field_id_mapping:
            field_id = field_id_mapping.get(entity["name"], "-")

        row_data = [name, description, category, device_class, unit, state_class, icon]
        if include_field_id:
            row_data.insert(1, field_id)
            
        table += "| " + " | ".join(row_data) + " |\n"

    return table

def main():
    """Generate entity documentation."""
    # Get the integration path
    integration_path = Path(__file__).parent.parent / "custom_components" / "autopi"

    # Extract information from platform files
    sensor_entities = []
    device_tracker_entities = []
    binary_sensor_entities = []

    # Process all Python files containing sensor definitions
    all_classes = []  # Keep track of all classes for base class analysis
    base_classes = []  # Specifically track base classes
    
    # Main sensor.py file
    sensor_file = integration_path / "sensor.py"
    if sensor_file.exists():
        classes = extract_class_info(sensor_file)
        all_classes.extend(classes)
        sensor_entities.extend([cls for cls in classes if "Sensor" in cls["name"] and cls["name"] != "SensorEntity"])

    # Position sensors
    position_sensor_file = integration_path / "position_sensors.py"
    if position_sensor_file.exists():
        classes = extract_class_info(position_sensor_file)
        all_classes.extend(classes)
        sensor_entities.extend([cls for cls in classes if "Sensor" in cls["name"] and cls["name"] != "SensorEntity"])

    # Data field sensors
    data_field_sensor_file = integration_path / "data_field_sensors.py"
    field_id_mapping = {}
    if data_field_sensor_file.exists():
        classes = extract_class_info(data_field_sensor_file)
        all_classes.extend(classes)
        # Extract field ID mapping
        field_id_mapping = extract_field_id_mapping(data_field_sensor_file)
        # Include base classes in documentation
        for cls in classes:
            if "Sensor" in cls["name"] and cls["name"] != "SensorEntity":
                if cls["name"] in ["AutoPiDataFieldSensorBase", "AutoPiDataFieldSensor", "AutoPiAutoZeroDataFieldSensor"]:
                    base_classes.append(cls)
                else:
                    sensor_entities.append(cls)

    # Process device_tracker.py
    tracker_file = integration_path / "device_tracker.py"
    if tracker_file.exists():
        classes = extract_class_info(tracker_file)
        all_classes.extend(classes)
        device_tracker_entities = [cls for cls in classes if "Tracker" in cls["name"]]

    # Process binary_sensor.py
    binary_sensor_file = integration_path / "binary_sensor.py"
    if binary_sensor_file.exists():
        classes = extract_class_info(binary_sensor_file)
        all_classes.extend(classes)
        binary_sensor_entities = [cls for cls in classes if "BinarySensor" in cls["name"]]

    # Generate documentation
    docs_content = """# Entity Reference

This page provides a comprehensive reference of all entities provided by the AutoPi integration.

## Sensors

The AutoPi integration provides several types of sensors to monitor your vehicles and the integration itself.

### Integration Sensors

These sensors provide information about the AutoPi integration itself:

"""

    # Filter integration-level sensors (non-vehicle specific)
    integration_sensors = [s for s in sensor_entities if "Vehicle" not in s["name"] and not any(x in s["name"] for x in ["GPS", "Battery", "Accelerometer", "Odometer", "Fuel", "Engine", "Throttle", "OBD", "Tracker", "Temperature", "Coolant", "GSM", "DTC", "Ignition"])]
    docs_content += generate_entity_table(integration_sensors, "Integration")

    docs_content += """
### Vehicle Status Sensors

These sensors provide general status information for each vehicle:

"""

    # Filter vehicle status sensors
    vehicle_status_sensors = [s for s in sensor_entities if "AutoPiVehicleSensor" in s["name"] or ("Vehicle" in s["name"] and "Count" in s["name"])]
    docs_content += generate_entity_table(vehicle_status_sensors, "Vehicle Status")

    docs_content += """
### GPS/Position Sensors

These sensors provide GPS and position data for each vehicle:

"""

    # Filter GPS/position sensors
    gps_sensors = [s for s in sensor_entities if "GPS" in s["name"]]
    docs_content += generate_entity_table(gps_sensors, "GPS/Position")

    docs_content += """
### Battery Sensors

These sensors provide battery information for vehicles and devices:

"""

    # Filter battery sensors
    battery_sensors = [s for s in sensor_entities if "Battery" in s["name"] or "Voltage" in s["name"] and "Vehicle" not in s["name"]]
    docs_content += generate_entity_table(battery_sensors, "Battery")

    docs_content += """
### Engine & Performance Sensors

These sensors provide engine and performance data:

"""

    # Filter engine/performance sensors
    engine_sensors = [s for s in sensor_entities if any(x in s["name"] for x in ["Engine", "Throttle", "OBD", "Load", "Ignition"])]
    docs_content += generate_entity_table(engine_sensors, "Engine & Performance")

    docs_content += """
### Fuel Sensors

These sensors provide fuel consumption and level data:

"""

    # Filter fuel sensors
    fuel_sensors = [s for s in sensor_entities if "Fuel" in s["name"]]
    docs_content += generate_entity_table(fuel_sensors, "Fuel")

    docs_content += """
### Distance & Odometer Sensors

These sensors provide distance and odometer readings:

"""

    # Filter distance/odometer sensors
    distance_sensors = [s for s in sensor_entities if any(x in s["name"] for x in ["Odometer", "Distance", "Trip"]) and "Fuel" not in s["name"]]
    docs_content += generate_entity_table(distance_sensors, "Distance & Odometer")

    docs_content += """
### Temperature Sensors

These sensors provide various temperature readings:

"""

    # Filter temperature sensors
    temp_sensors = [s for s in sensor_entities if any(x in s["name"] for x in ["Temperature", "Coolant", "Intake", "Ambient"])]
    docs_content += generate_entity_table(temp_sensors, "Temperature")

    docs_content += """
### Motion & Tracking Sensors

These sensors provide motion and tracking data:

"""

    # Filter motion/tracking sensors
    motion_sensors = [s for s in sensor_entities if any(x in s["name"] for x in ["Accelerometer", "TrackerSpeed", "TrackerBattery"])]
    docs_content += generate_entity_table(motion_sensors, "Motion & Tracking")

    docs_content += """
### Diagnostic Sensors

These sensors provide diagnostic information:

"""

    # Filter diagnostic sensors
    diagnostic_sensors = [s for s in sensor_entities if any(x in s["name"] for x in ["GSM", "DTC", "API", "Success", "Duration", "Failed"])]
    docs_content += generate_entity_table(diagnostic_sensors, "Diagnostic")

    # Add data field sensor reference
    if field_id_mapping:
        docs_content += """
## Data Field Sensor Reference

This table shows all data field sensors with their corresponding AutoPi field IDs:

"""
        # Get all data field sensors
        data_field_sensors = [s for s in sensor_entities if s["file"] == "data_field_sensors.py"]
        docs_content += generate_entity_table(data_field_sensors, "Data Field", include_field_id=True, field_id_mapping=field_id_mapping)

    docs_content += """
## Device Trackers

Device trackers provide GPS-based location tracking for your vehicles:

"""

    docs_content += generate_entity_table(device_tracker_entities, "Device Tracker")

    docs_content += """
## Binary Sensors

Binary sensors provide on/off state information:

"""

    docs_content += generate_entity_table(binary_sensor_entities, "Binary Sensor")

    # Add base classes section
    if base_classes:
        docs_content += """
## Base Classes

The AutoPi integration uses the following base classes for entity implementation:

"""
        for base_class in base_classes:
            docs_content += f"### {base_class['name']}\n\n"
            if base_class.get('docstring'):
                docs_content += f"{base_class['docstring']}\n\n"
            
            # Show inheritance
            if base_class.get('base_classes'):
                docs_content += f"**Inherits from:** {', '.join(base_class['base_classes'])}\n\n"
            
            # Show important attributes
            attrs = base_class.get('attributes', {})
            important_attrs = {k: v for k, v in attrs.items() if k.startswith('_attr_')}
            if important_attrs:
                docs_content += "**Key Attributes:**\n"
                for attr, value in important_attrs.items():
                    docs_content += f"- `{attr}`: {value}\n"
                docs_content += "\n"
            
            # Show important properties
            props = base_class.get('properties', {})
            if props:
                docs_content += "**Properties:**\n"
                for prop, info in props.items():
                    if info.get('docstring'):
                        docs_content += f"- `{prop}`: {info['docstring'].split('\\n')[0]}\n"
                    else:
                        docs_content += f"- `{prop}`\n"
                docs_content += "\n"

    docs_content += """
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

"""

    docs_content += """
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

"""

    # Write the documentation
    docs_path = Path(__file__).parent.parent / "docs" / "entities.md"
    docs_path.parent.mkdir(exist_ok=True)

    with open(docs_path, "w", encoding="utf-8") as f:
        f.write(docs_content)

    print(f"Generated entity documentation: {docs_path}")
    print(f"Found {len(sensor_entities)} sensors, {len(device_tracker_entities)} device trackers, {len(binary_sensor_entities)} binary sensors")

    # Print detailed breakdown of sensor types
    sensor_files = {}
    for sensor in sensor_entities:
        file_name = sensor.get("file", "unknown")
        if file_name not in sensor_files:
            sensor_files[file_name] = 0
        sensor_files[file_name] += 1

    print("\nSensor breakdown by file:")
    for file_name, count in sorted(sensor_files.items()):
        print(f"  {file_name}: {count} sensors")

if __name__ == "__main__":
    main()
