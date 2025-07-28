#!/usr/bin/env python3
"""Auto-generate entity documentation for the AutoPi integration."""

import ast
import inspect
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

def extract_class_info(file_path: Path) -> List[Dict[str, Any]]:
    """Extract class information from a Python file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
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
                'name': node.name,
                'docstring': ast.get_docstring(node),
                'attributes': {},
                'methods': {},
                'base_classes': [base.id if hasattr(base, 'id') else str(base) for base in node.bases],
                'file': file_path.name
            }
            
            # Extract class attributes and their values
            for item in node.body:
                if isinstance(item, ast.Assign):
                    for target in item.targets:
                        if isinstance(target, ast.Name) and target.id.startswith('_attr_'):
                            attr_name = target.id
                            attr_value = None
                            
                            # Try to extract the value
                            if isinstance(item.value, ast.Constant):
                                attr_value = item.value.value
                            elif isinstance(item.value, ast.Str):
                                attr_value = item.value.s
                            elif isinstance(item.value, ast.Name):
                                attr_value = item.value.id
                            elif isinstance(item.value, ast.Attribute):
                                # Handle things like SensorDeviceClass.SPEED
                                attr_value = f"{item.value.value.id}.{item.value.attr}" if hasattr(item.value.value, 'id') else str(item.value)
                            
                            class_info['attributes'][attr_name] = attr_value
                
                # Extract method information
                elif isinstance(item, ast.FunctionDef):
                    method_docstring = ast.get_docstring(item)
                    if item.name in ['name', 'native_value', 'device_class', 'state_class', 'unit_of_measurement', 'icon']:
                        class_info['methods'][item.name] = {
                            'docstring': method_docstring,
                            'property': any(isinstance(d, ast.Name) and d.id == 'property' for d in item.decorator_list)
                        }
            
            classes.append(class_info)
    
    return classes

def get_entity_description(class_info: Dict[str, Any]) -> str:
    """Generate a description for an entity class."""
    docstring = class_info.get('docstring', '')
    if docstring:
        # Extract first line of docstring
        first_line = docstring.split('\n')[0].strip()
        if first_line:
            return first_line
    
    # Fallback: generate from class name
    name = class_info['name']
    if 'Vehicle' in name and 'Sensor' in name:
        sensor_type = name.replace('AutoPiVehicle', '').replace('Sensor', '')
        return f"Sensor for vehicle {sensor_type.lower()}"
    elif 'Sensor' in name:
        sensor_type = name.replace('AutoPi', '').replace('Sensor', '')
        return f"Sensor for {sensor_type.lower()}"
    elif 'Tracker' in name:
        return "GPS-based device tracker for vehicle location"
    
    return "AutoPi entity"

def get_entity_category(class_info: Dict[str, Any]) -> str:
    """Determine entity category."""
    entity_category = class_info['attributes'].get('_attr_entity_category')
    if entity_category == 'EntityCategory.DIAGNOSTIC':
        return "Diagnostic"
    return "Primary"

def get_device_class(class_info: Dict[str, Any]) -> Optional[str]:
    """Get device class if specified."""
    device_class = class_info['attributes'].get('_attr_device_class')
    if device_class:
        # Clean up the device class name
        if '.' in device_class:
            return device_class.split('.')[-1].title()
        return device_class
    return None

def get_unit_of_measurement(class_info: Dict[str, Any]) -> Optional[str]:
    """Get unit of measurement if specified."""
    unit = class_info['attributes'].get('_attr_native_unit_of_measurement')
    if unit:
        # Clean up unit names
        if '.' in unit:
            return unit.split('.')[-1]
        return unit
    return None

def get_state_class(class_info: Dict[str, Any]) -> Optional[str]:
    """Get state class if specified."""
    state_class = class_info['attributes'].get('_attr_state_class')
    if state_class:
        if '.' in state_class:
            return state_class.split('.')[-1].title()
        return state_class
    return None

def get_icon(class_info: Dict[str, Any]) -> Optional[str]:
    """Get icon if specified."""
    return class_info['attributes'].get('_attr_icon')

def generate_entity_table(entities: List[Dict[str, Any]], entity_type: str) -> str:
    """Generate a markdown table for entities."""
    if not entities:
        return f"No {entity_type.lower()} entities are currently implemented.\n"
    
    # Create table header
    table = f"| Entity | Description | Category | Device Class | Unit | State Class | Icon |\n"
    table += f"|--------|-------------|----------|--------------|------|-------------|------|\n"
    
    for entity in entities:
        name = entity['name'].replace('AutoPi', '').replace('Vehicle', '').replace('Sensor', '').replace('Tracker', '')
        if not name:
            name = entity['name']
        
        description = get_entity_description(entity)
        category = get_entity_category(entity)
        device_class = get_device_class(entity) or "-"
        unit = get_unit_of_measurement(entity) or "-"
        state_class = get_state_class(entity) or "-"
        icon = get_icon(entity) or "-"
        
        table += f"| {name} | {description} | {category} | {device_class} | {unit} | {state_class} | {icon} |\n"
    
    return table

def main():
    """Generate entity documentation."""
    # Get the integration path
    integration_path = Path(__file__).parent.parent / "custom_components" / "autopi"
    
    # Extract information from platform files
    sensor_entities = []
    device_tracker_entities = []
    binary_sensor_entities = []
    
    # Process sensor.py
    sensor_file = integration_path / "sensor.py"
    if sensor_file.exists():
        classes = extract_class_info(sensor_file)
        sensor_entities = [cls for cls in classes if 'Sensor' in cls['name'] and cls['name'] != 'SensorEntity']
    
    # Process device_tracker.py
    tracker_file = integration_path / "device_tracker.py"
    if tracker_file.exists():
        classes = extract_class_info(tracker_file)
        device_tracker_entities = [cls for cls in classes if 'Tracker' in cls['name']]
    
    # Process binary_sensor.py
    binary_sensor_file = integration_path / "binary_sensor.py"
    if binary_sensor_file.exists():
        classes = extract_class_info(binary_sensor_file)
        binary_sensor_entities = [cls for cls in classes if 'BinarySensor' in cls['name']]
    
    # Generate documentation
    docs_content = """# Entity Reference

This page provides a comprehensive reference of all entities provided by the AutoPi integration.

## Sensors

The AutoPi integration provides several types of sensors to monitor your vehicles and the integration itself.

### Integration Sensors

These sensors provide information about the AutoPi integration itself:

"""
    
    # Filter integration-level sensors (non-vehicle specific)
    integration_sensors = [s for s in sensor_entities if 'Vehicle' not in s['name']]
    docs_content += generate_entity_table(integration_sensors, "Integration")
    
    docs_content += """
### Vehicle Sensors

These sensors provide information specific to each vehicle:

"""
    
    # Filter vehicle-specific sensors
    vehicle_sensors = [s for s in sensor_entities if 'Vehicle' in s['name']]
    docs_content += generate_entity_table(vehicle_sensors, "Vehicle")
    
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
    
    with open(docs_path, 'w', encoding='utf-8') as f:
        f.write(docs_content)
    
    print(f"Generated entity documentation: {docs_path}")
    print(f"Found {len(sensor_entities)} sensors, {len(device_tracker_entities)} device trackers, {len(binary_sensor_entities)} binary sensors")

if __name__ == "__main__":
    main() 