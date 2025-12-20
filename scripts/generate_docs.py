#!/usr/bin/env python3
"""Auto-generate entity documentation for the AutoPi integration."""

import ast
import re
from pathlib import Path
from typing import Any

SUPER_INIT_ATTR_MAP = {
    "device_class": "_attr_device_class",
    "unit_of_measurement": "_attr_native_unit_of_measurement",
    "state_class": "_attr_state_class",
    "entity_category": "_attr_entity_category",
    "icon": "_attr_icon",
}

ACRONYMS = {
    "Dtc": "DTC",
    "Ecu": "ECU",
    "Gps": "GPS",
    "Gsm": "GSM",
    "Obd": "OBD",
    "Rfid": "RFID",
}


def ast_value(node: ast.AST | None) -> Any:
    """Convert an AST node into a simple Python value or string."""
    if node is None:
        return None
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = ast_value(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    if isinstance(node, ast.List):
        return [ast_value(item) for item in node.elts]
    if isinstance(node, ast.Tuple):
        return [ast_value(item) for item in node.elts]
    if isinstance(node, ast.Dict):
        return {
            ast_value(key): ast_value(value)
            for key, value in zip(node.keys, node.values)
        }
    if hasattr(ast, "unparse"):
        try:
            return ast.unparse(node)
        except Exception:
            pass
    return str(node)


def base_class_name(node: ast.AST) -> str:
    """Extract a readable base class name."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return ast_value(node)
    if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name):
        return node.value.id
    return ast_value(node)


def extract_simple_return_value(func_node: ast.FunctionDef) -> Any | None:
    """Extract a simple constant return value from a property."""
    disallowed = (ast.If, ast.For, ast.While, ast.Try, ast.With, ast.Match)
    for node in func_node.body:
        if isinstance(node, disallowed):
            return None

    returns = [node for node in func_node.body if isinstance(node, ast.Return)]
    if len(returns) != 1:
        return None

    return_node = returns[0]
    if return_node.value is None:
        return None
    if isinstance(return_node.value, (ast.Constant, ast.Name, ast.Attribute)):
        return ast_value(return_node.value)
    return None


def is_super_init_call(node: ast.Call) -> bool:
    """Return True if this is a super().__init__(...) call."""
    return (
        isinstance(node.func, ast.Attribute)
        and node.func.attr == "__init__"
        and isinstance(node.func.value, ast.Call)
        and isinstance(node.func.value.func, ast.Name)
        and node.func.value.func.id == "super"
    )


def split_camel_case(name: str) -> list[str]:
    """Split CamelCase words while keeping acronyms intact."""
    return re.findall(r"[A-Z]+(?=[A-Z][a-z]|[0-9]|$)|[A-Z]?[a-z]+|[0-9]+", name)


def humanize_entity_name(class_name: str, entity_type: str) -> str:
    """Convert class name to a human-readable label."""
    name = class_name
    if name.startswith("AutoPi"):
        name = name[len("AutoPi") :]

    words = [ACRONYMS.get(word, word) for word in split_camel_case(name)]

    if entity_type == "event" and words and words[-1] == "Entity":
        words = words[:-1]

    if entity_type in {"sensor", "binary_sensor"} and words and words[-1] == "Sensor":
        if words != ["Vehicle", "Sensor"]:
            words = words[:-1]

    if entity_type == "binary_sensor" and words and words[-1] == "Binary":
        words = words[:-1]

    return " ".join(words) if words else class_name


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
                "base_classes": [base_class_name(base) for base in node.bases],
                "file": file_path.name,
                "init_params": [],
                "super_init_calls": [],
                "field_id": None,
            }

            # Extract __init__ parameters
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == "__init__":
                    param_names = {arg.arg for arg in item.args.args}
                    class_info["init_param_names"] = param_names
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

                    init_attributes: dict[str, Any] = {}
                    for init_node in ast.walk(item):
                        if isinstance(init_node, ast.Assign):
                            for target in init_node.targets:
                                if (
                                    isinstance(target, ast.Attribute)
                                    and isinstance(target.value, ast.Name)
                                    and target.value.id == "self"
                                ):
                                    if isinstance(init_node.value, ast.Name):
                                        if init_node.value.id in param_names:
                                            continue
                                        if not init_node.value.id.isupper():
                                            continue
                                    init_attributes[target.attr] = ast_value(
                                        init_node.value
                                    )
                        elif isinstance(init_node, ast.AnnAssign):
                            target = init_node.target
                            if (
                                isinstance(target, ast.Attribute)
                                and isinstance(target.value, ast.Name)
                                and target.value.id == "self"
                            ):
                                if isinstance(init_node.value, ast.Name):
                                    if init_node.value.id in param_names:
                                        continue
                                    if not init_node.value.id.isupper():
                                        continue
                                init_attributes[target.attr] = ast_value(
                                    init_node.value
                                )
                        elif isinstance(init_node, ast.Call) and is_super_init_call(
                            init_node
                        ):
                            super_args = [ast_value(arg) for arg in init_node.args]
                            super_kwargs = {}
                            for kw in init_node.keywords:
                                if not kw.arg:
                                    continue
                                if isinstance(kw.value, ast.Name) and not kw.value.id.isupper():
                                    if kw.value.id in param_names:
                                        continue
                                    # Skip non-constant names (likely local variables)
                                    continue
                                super_kwargs[kw.arg] = ast_value(kw.value)
                            class_info["super_init_calls"].append(
                                {"args": super_args, "keywords": super_kwargs}
                            )
                            for key, attr_name in SUPER_INIT_ATTR_MAP.items():
                                if key in super_kwargs and not (
                                    isinstance(super_kwargs[key], str)
                                    and super_kwargs[key] in param_names
                                ):
                                    init_attributes[attr_name] = super_kwargs[key]

                    class_info["init_attributes"] = init_attributes

            # Extract class attributes and their values
            for item in node.body:
                if isinstance(item, ast.Assign):
                    for target in item.targets:
                        if isinstance(target, ast.Name):
                            attr_name = target.id
                            class_info["attributes"][attr_name] = ast_value(item.value)

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
                        if item.name == "native_unit_of_measurement":
                            return_value = extract_simple_return_value(item)
                            if return_value is not None:
                                class_info.setdefault("property_overrides", {})[
                                    "_attr_native_unit_of_measurement"
                                ] = return_value
                    else:
                        class_info["methods"][item.name] = method_info

            if class_info.get("init_attributes"):
                class_info["attributes"].update(class_info["init_attributes"])
            if class_info.get("property_overrides"):
                class_info["attributes"].update(class_info["property_overrides"])

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


def get_all_base_classes(
    class_info: dict[str, Any], all_classes: list[dict[str, Any]]
) -> set[str]:
    """Get all base classes including inherited ones."""
    bases: set[str] = set()
    for base_name in class_info.get("base_classes", []):
        bases.add(base_name)
        for cls in all_classes:
            if cls["name"] == base_name:
                bases.update(get_all_base_classes(cls, all_classes))
                break
    return bases


def class_inherits(
    class_info: dict[str, Any], base_name: str, all_classes: list[dict[str, Any]]
) -> bool:
    """Check if a class inherits from a base class."""
    return base_name in get_all_base_classes(class_info, all_classes)


def format_enum_value(value: str) -> str:
    """Format enum-like values for display."""
    formatted = value.split(".")[-1] if "." in value else value
    return formatted.replace("_", " ").title()


def get_entity_category(
    class_info: dict[str, Any], all_classes: list[dict[str, Any]]
) -> str:
    """Determine entity category."""
    entity_category = get_all_attributes(class_info, all_classes).get(
        "_attr_entity_category"
    )
    if entity_category and "DIAGNOSTIC" in str(entity_category):
        return "Diagnostic"
    return "Primary"


def get_device_class(
    class_info: dict[str, Any], all_classes: list[dict[str, Any]]
) -> str | None:
    """Get device class if specified."""
    device_class = get_all_attributes(class_info, all_classes).get(
        "_attr_device_class"
    )
    if device_class:
        return format_enum_value(str(device_class))
    return None


def get_unit_of_measurement(
    class_info: dict[str, Any], all_classes: list[dict[str, Any]]
) -> str | None:
    """Get unit of measurement if specified."""
    unit = get_all_attributes(class_info, all_classes).get(
        "_attr_native_unit_of_measurement"
    )
    if unit:
        # Clean up unit names
        if isinstance(unit, str) and "." in unit:
            return unit.split(".")[-1]
        return str(unit)
    return None


def get_state_class(
    class_info: dict[str, Any], all_classes: list[dict[str, Any]]
) -> str | None:
    """Get state class if specified."""
    state_class = get_all_attributes(class_info, all_classes).get("_attr_state_class")
    if state_class:
        return format_enum_value(str(state_class))
    return None


def get_icon(
    class_info: dict[str, Any], all_classes: list[dict[str, Any]]
) -> str | None:
    """Get icon if specified."""
    return get_all_attributes(class_info, all_classes).get("_attr_icon")


def get_event_types(
    class_info: dict[str, Any], all_classes: list[dict[str, Any]]
) -> list[str]:
    """Get event types if specified."""
    value = get_all_attributes(class_info, all_classes).get("_attr_event_types")
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, str):
        return [value]
    return []


def get_entity_platform(
    class_info: dict[str, Any], all_classes: list[dict[str, Any]]
) -> str | None:
    """Return the Home Assistant platform for an entity class."""
    bases = get_all_base_classes(class_info, all_classes)
    if "SensorEntity" in bases:
        return "sensor"
    if "BinarySensorEntity" in bases:
        return "binary_sensor"
    if "TrackerEntity" in bases:
        return "device_tracker"
    if "EventEntity" in bases:
        return "event"
    return None


def categorize_data_field_sensor(class_info: dict[str, Any]) -> str:
    """Categorize data field sensors based on field IDs and names."""
    field_id = str(class_info.get("field_id", "")).lower()
    name = class_info["name"].lower()

    if field_id.startswith("track.pos.") or name.startswith("gps"):
        return "GPS/Position"

    if any(
        key in field_id
        for key in ["obd.bat.", "std.battery", "battery", "external_voltage"]
    ):
        return "Battery"

    if "fuel" in field_id or "fuel" in name:
        return "Fuel"

    if any(key in field_id for key in ["odometer", "mileage", "distance", "trip"]):
        return "Distance & Odometer"

    if any(
        key in field_id
        for key in ["ambient_air_temp", "intake_temp", "coolant_temp", "temp"]
    ) or "temperature" in name:
        return "Temperature"

    if any(key in field_id for key in ["accelerometer", "std.speed"]):
        return "Motion & Tracking"

    if any(
        key in field_id
        for key in [
            "obd.rpm",
            "engine_load",
            "run_time",
            "throttle_pos",
            "obd.speed",
            "ignition",
        ]
    ):
        return "Engine & Performance"

    if any(key in field_id for key in ["gsm_signal", "tz_offset", "number_of_dtc"]) or any(
        key in name for key in ["gsm", "dtc", "timezone"]
    ):
        return "Diagnostic"

    return "Other"

def extract_field_id_mapping(file_path: Path, mapping_name: str) -> dict[str, str]:
    """Extract field ID to class mapping from a mapping dict in a file."""
    mapping: dict[str, str] = {}

    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        tree = ast.parse(content)
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == mapping_name:
                        if isinstance(node.value, ast.Dict):
                            for key_node, value_node in zip(
                                node.value.keys, node.value.values
                            ):
                                field_id = ast_value(key_node)
                                if isinstance(value_node, ast.Name):
                                    mapping[value_node.id] = str(field_id)
                                elif isinstance(value_node, (ast.Tuple, ast.List)):
                                    for element in value_node.elts:
                                        if isinstance(element, ast.Name):
                                            mapping[element.id] = str(field_id)
                        return mapping
    except Exception as e:
        print(f"Failed to extract field ID mapping from {file_path}: {e}")

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

def get_field_id(
    class_info: dict[str, Any], field_id_mapping: dict[str, str] | None
) -> str | None:
    """Get field ID from class info or mapping."""
    if class_info.get("field_id"):
        return str(class_info["field_id"])
    if field_id_mapping:
        return field_id_mapping.get(class_info["name"])
    return None


def generate_entity_table(
    entities: list[dict[str, Any]],
    entity_type: str,
    all_classes: list[dict[str, Any]],
    entity_platform: str,
    include_field_id: bool = False,
    field_id_mapping: dict[str, str] | None = None,
) -> str:
    """Generate a markdown table for entities."""
    if not entities:
        return f"No {entity_type.lower()} entities are currently implemented.\n"

    # Create table header
    headers = ["Entity", "Description", "Category", "Device Class", "Unit", "State Class", "Icon"]
    if include_field_id:
        headers.insert(1, "Field ID")

    table = "| " + " | ".join(headers) + " |\n"
    table += "|" + "|".join(["-" * 10 for _ in headers]) + "|\n"

    for entity in sorted(
        entities, key=lambda item: humanize_entity_name(item["name"], entity_platform)
    ):
        name = humanize_entity_name(entity["name"], entity_platform)

        description = get_entity_description(entity)
        category = get_entity_category(entity, all_classes)
        device_class = get_device_class(entity, all_classes) or "-"
        unit = get_unit_of_measurement(entity, all_classes) or "-"
        state_class = get_state_class(entity, all_classes) or "-"
        icon = get_icon(entity, all_classes) or "-"

        # Extract field_id from mapping if available
        field_id = "-"
        if include_field_id:
            field_id = get_field_id(entity, field_id_mapping) or "-"

        row_data = [name, description, category, device_class, unit, state_class, icon]
        if include_field_id:
            row_data.insert(1, field_id)

        table += "| " + " | ".join(row_data) + " |\n"

    return table


def generate_event_table(
    entities: list[dict[str, Any]], all_classes: list[dict[str, Any]]
) -> str:
    """Generate a markdown table for event entities."""
    if not entities:
        return "No event entities are currently implemented.\n"

    headers = ["Entity", "Description", "Category", "Event Types"]
    table = "| " + " | ".join(headers) + " |\n"
    table += "|" + "|".join(["-" * 10 for _ in headers]) + "|\n"

    for entity in sorted(
        entities, key=lambda item: humanize_entity_name(item["name"], "event")
    ):
        name = humanize_entity_name(entity["name"], "event")
        description = get_entity_description(entity)
        category = get_entity_category(entity, all_classes)
        event_types = get_event_types(entity, all_classes)
        event_types_str = ", ".join(event_types) if event_types else "-"
        table += f"| {name} | {description} | {category} | {event_types_str} |\n"

    return table


def main():
    """Generate entity documentation."""
    # Get the integration path
    integration_path = Path(__file__).parent.parent / "custom_components" / "autopi"

    sensor_file = integration_path / "sensor.py"
    position_sensor_file = integration_path / "position_sensors.py"
    data_field_sensor_file = integration_path / "data_field_sensors.py"
    tracker_file = integration_path / "device_tracker.py"
    binary_sensor_file = integration_path / "binary_sensor.py"
    event_file = integration_path / "event.py"
    base_entity_file = integration_path / "entities" / "base.py"

    files_to_process = [
        sensor_file,
        position_sensor_file,
        data_field_sensor_file,
        tracker_file,
        binary_sensor_file,
        event_file,
        base_entity_file,
    ]

    all_classes: list[dict[str, Any]] = []
    for file_path in files_to_process:
        if file_path.exists():
            all_classes.extend(extract_class_info(file_path))

    field_id_mapping: dict[str, str] = {}
    if data_field_sensor_file.exists():
        field_id_mapping.update(
            extract_field_id_mapping(
                data_field_sensor_file, "FIELD_ID_TO_SENSOR_CLASS"
            )
        )
    if position_sensor_file.exists():
        field_id_mapping.update(
            extract_field_id_mapping(
                position_sensor_file, "POSITION_FIELD_TO_SENSOR_CLASS"
            )
        )

    excluded_entities = {
        "AutoPiEntity",
        "AutoPiVehicleEntity",
        "AutoPiDataFieldSensorBase",
        "AutoPiDataFieldSensor",
        "AutoPiAutoZeroDataFieldSensor",
        "AutoPiDataFieldBinarySensor",
    }

    for cls in all_classes:
        if cls.get("field_id"):
            continue
        if class_inherits(cls, "AutoPiDataFieldSensorBase", all_classes) or class_inherits(
            cls, "AutoPiDataFieldBinarySensor", all_classes
        ):
            param_names = cls.get("init_param_names", set())
            for call in cls.get("super_init_calls", []):
                args = call.get("args", [])
                if (
                    len(args) >= 3
                    and isinstance(args[2], str)
                    and args[2] not in param_names
                ):
                    cls["field_id"] = args[2]
                    break
        if not cls.get("field_id"):
            mapped_field = field_id_mapping.get(cls["name"])
            if mapped_field:
                cls["field_id"] = mapped_field

    sensor_entities: list[dict[str, Any]] = []
    binary_sensor_entities: list[dict[str, Any]] = []
    device_tracker_entities: list[dict[str, Any]] = []
    event_entities: list[dict[str, Any]] = []

    for cls in all_classes:
        if cls["name"] in excluded_entities:
            continue
        platform = get_entity_platform(cls, all_classes)
        if platform == "sensor":
            sensor_entities.append(cls)
        elif platform == "binary_sensor":
            binary_sensor_entities.append(cls)
        elif platform == "device_tracker":
            device_tracker_entities.append(cls)
        elif platform == "event":
            event_entities.append(cls)

    base_class_order = [
        "AutoPiEntity",
        "AutoPiVehicleEntity",
        "AutoPiDataFieldSensorBase",
        "AutoPiDataFieldSensor",
        "AutoPiAutoZeroDataFieldSensor",
        "AutoPiDataFieldBinarySensor",
    ]
    base_classes = [
        cls for name in base_class_order for cls in all_classes if cls["name"] == name
    ]

    data_field_sensors = [
        s
        for s in sensor_entities
        if class_inherits(s, "AutoPiDataFieldSensorBase", all_classes)
    ]
    data_field_names = {sensor["name"] for sensor in data_field_sensors}

    integration_sensors = [
        s
        for s in sensor_entities
        if not class_inherits(s, "AutoPiVehicleEntity", all_classes)
    ]
    vehicle_status_sensors = [
        s
        for s in sensor_entities
        if class_inherits(s, "AutoPiVehicleEntity", all_classes)
        and s["name"] not in data_field_names
    ]

    data_field_categories: dict[str, list[dict[str, Any]]] = {}
    for sensor in data_field_sensors:
        category = categorize_data_field_sensor(sensor)
        data_field_categories.setdefault(category, []).append(sensor)

    docs_content = """# Entity Reference

This page provides a comprehensive reference of all entities provided by the AutoPi integration.

## Sensors

The AutoPi integration provides integration-level sensors and vehicle-level sensors. Data field sensors
are created dynamically based on the telemetry fields reported by each vehicle.

### Integration Sensors

These sensors provide information about the AutoPi integration itself:

"""

    docs_content += generate_entity_table(
        integration_sensors, "Integration", all_classes, "sensor"
    )

    docs_content += """
### Vehicle Status & Trip Sensors

These sensors provide general status information for each vehicle:

"""

    docs_content += generate_entity_table(
        vehicle_status_sensors, "Vehicle Status", all_classes, "sensor"
    )

    docs_content += """
### Data Field Sensors

These sensors are created when the vehicle reports the corresponding telemetry fields:

"""

    data_field_category_order = [
        "GPS/Position",
        "Battery",
        "Engine & Performance",
        "Fuel",
        "Distance & Odometer",
        "Temperature",
        "Motion & Tracking",
        "Diagnostic",
        "Other",
    ]
    for category in data_field_category_order:
        sensors = data_field_categories.get(category, [])
        if not sensors:
            continue
        docs_content += f"#### {category} Sensors\n\n"
        docs_content += generate_entity_table(
            sensors, category, all_classes, "sensor"
        )
        docs_content += "\n"

    if data_field_sensors:
        docs_content += """
## Data Field Sensor Reference

This table shows all data field sensors with their corresponding AutoPi field IDs:

"""
        docs_content += generate_entity_table(
            data_field_sensors,
            "Data Field",
            all_classes,
            "sensor",
            include_field_id=True,
            field_id_mapping=field_id_mapping,
        )

    docs_content += """
## Device Trackers

Device trackers provide GPS-based location tracking for your vehicles:

"""

    docs_content += generate_entity_table(
        device_tracker_entities, "Device Tracker", all_classes, "device_tracker"
    )

    docs_content += """
## Binary Sensors

Binary sensors provide on/off state information:

"""

    docs_content += generate_entity_table(
        binary_sensor_entities,
        "Binary Sensor",
        all_classes,
        "binary_sensor",
        include_field_id=True,
        field_id_mapping=field_id_mapping,
    )

    docs_content += """
## Events

Event entities emit Home Assistant events for vehicle activity:

"""

    docs_content += generate_event_table(event_entities, all_classes)

    if base_classes:
        docs_content += """
## Base Classes

The AutoPi integration uses the following base classes for entity implementation:

"""
        for base_class in base_classes:
            docs_content += f"### {base_class['name']}\n\n"
            if base_class.get("docstring"):
                docs_content += f"{base_class['docstring']}\n\n"

            if base_class.get("base_classes"):
                docs_content += f"**Inherits from:** {', '.join(base_class['base_classes'])}\n\n"

            attrs = base_class.get("attributes", {})
            important_attrs = {
                k: v
                for k, v in attrs.items()
                if k.startswith("_attr_") and k != "_attr_unique_id"
            }
            if important_attrs:
                docs_content += "**Key Attributes:**\n"
                for attr, value in important_attrs.items():
                    docs_content += f"- `{attr}`: {value}\n"
                docs_content += "\n"

            props = base_class.get("properties", {})
            if props:
                docs_content += "**Properties:**\n"
                for prop, info in props.items():
                    if info.get("docstring"):
                        docs_content += f"- `{prop}`: {info['docstring'].split('\\n')[0]}\n"
                    else:
                        docs_content += f"- `{prop}`\n"
                docs_content += "\n"

    docs_content += """
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

"""

    # Write the documentation
    docs_path = Path(__file__).parent.parent / "docs" / "entities.md"
    docs_path.parent.mkdir(exist_ok=True)

    with open(docs_path, "w", encoding="utf-8") as f:
        f.write(docs_content)

    print(f"Generated entity documentation: {docs_path}")
    print(
        f"Found {len(sensor_entities)} sensors, {len(device_tracker_entities)} device trackers, "
        f"{len(binary_sensor_entities)} binary sensors, {len(event_entities)} events"
    )

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
