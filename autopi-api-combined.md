# AutoPi API Endpoints for Home Assistant Integration

This guide provides a comprehensive overview of AutoPi API endpoints and metrics useful for building a custom Home Assistant integration. AutoPi exposes a REST API that allows third-party clients to query information about vehicles and devices.

## API Overview

- **Protocol**: REST API following OpenAPI schema
- **Method**: Most calls use GET method with JSON responses
- **Authentication**: Requires authenticated API token
- **Base URL**: `https://api.autopi.io/`

---

### Historical Positions

| Endpoint | Parameters | Response Data | Use Case |
|----------|------------|---------------|----------|
| `GET /logbook/storage/raw/` | `device_id`, `start_utc`, `end_utc`, `data_type` (e.g., `track.pos.loc`) | Historical location data | Query past location data for specific time ranges |

---

## 2. Vehicle Status & Metrics 📊

Access a wide range of sensor data from the vehicle's OBD-II port or the AutoPi device itself.

### Discovering Available Metrics

| Endpoint | Parameters | Response Data | Use Case |
|----------|------------|---------------|----------|
| `GET /logbook/storage/data_fields/` | `device_id` (UUID) or `vehicle_id` (int) | Array of `Field` objects containing:<br>• `field_prefix`<br>• `field_name`<br>• `sampling_frequency`<br>• `type`<br>• `title`<br>• `last_seen`<br>• `last_value` | **Crucial first step** - Discover all telemetry fields supported by a device. Use to dynamically create sensors in Home Assistant. |

### Real-time Sensor Data

| Endpoint | Parameters | Response Data | Use Case |
|----------|------------|---------------|----------|
| `GET /logbook/v2/recent_stats/` | `device_id` (required), `from_timestamp`, `type` (optional, e.g., `obd.fuel_level`), `kind` (`events` or `data`) | Array of `RecentStatsV2` items with:<br>• `@ts` (timestamp)<br>• `@rec` (record upload time)<br>• `@uid` (unit ID)<br>• `@vid` (vehicle ID)<br>• `@t` (data type)<br>• Dynamic keys with actual values | Main endpoint for latest sensor values. Without type filter, returns most recent value of every data type. |
| `GET /logbook/recent_stats/` | `device_id` (UUID), `from_timestamp` (ISO date) | `RecentStats` object with:<br>• `voltage`<br>• `voltage_ts`<br>• `voltage_level` (battery %)<br>• `voltage_level_ts`<br>• `latest_com` (last communication time) | Battery voltage and percentage sensor entity. Detect offline devices using last communication timestamp. |

### Historical Sensor Data

| Endpoint | Parameters | Response Data | Use Case |
|----------|------------|---------------|----------|
| `GET /logbook/storage/read/` | `device_id`, `field`, `field_type`, `from_utc`, `to_utc`, `interval` (e.g., `10m`), `aggregation` (`avg`, `min`, `max`) | `DataItem` list with aggregated values | Perfect for history graphs and statistics sensors. Supports aggregations. |
| `GET /logbook/raw/` or `GET /logbook/storage/raw/` | `device_id`, `start_utc`, `end_utc`, `data_type`, `page_num`, `page_size` | `PagedRawData` with `RawData` items containing `ts`, `rec`, `t` | Retrieve historical time-series for graphs |

### Vehicle Information

| Endpoint | Parameters | Response Data | Use Case |
|----------|------------|---------------|----------|
| `GET /fleet/vehicles/{id}/` | Vehicle ID | `FleetVehicle` object with `mileage` field | Get vehicle mileage |
| `GET /fleet/vehicles/` | `driving` (boolean filter) | List of vehicles with driving state | Check which vehicles are currently in motion |

### Manual OBD Queries

| Endpoint | Parameters | Response Data | Use Case |
|----------|------------|---------------|----------|
| `POST /dongle/{unit_id}/obd/query/{command}/` | Unit ID, OBD command (e.g., `010C` for RPM) | Result of OBD command | Query specific PIDs not logged automatically |

---

## 3. Driving & Trip Data 🚗

Monitor and analyze trip history, including distance, duration, and start/end locations.

| Endpoint | Parameters | Response Data | Use Case |
|----------|------------|---------------|----------|
| `GET /logbook/v2/trips/` | Optional filters by time, device, vehicle | Paginated list of `TripSerializerV2` objects with:<br>• `start_time_utc`<br>• `end_time_utc`<br>• `start_position_lat/lng`<br>• `end_position_lat/lng`<br>• `distanceKm`<br>• `duration`<br>• `tag` (business/personal) | Create sensors for latest trip details |
| `GET /logbook/v2/trips/{id}/` | Trip UUID | Single `TripSerializerV2` object | Retrieve specific journey details |
| `GET /logbook/fleet_summary/timedistance/` | `vehicle_id`, `device_id`, `exclude_unassociated` | `TimeDistanceData` with `today` and `month` sections containing distance and time metrics | High-level daily/monthly distance and driving time sensors |

---

## 4. Vehicle Diagnostics & Alerts ⚠️

Track vehicle health by monitoring Diagnostic Trouble Codes (DTCs) and system alerts.

### Alerts

| Endpoint | Parameters | Response Data | Use Case |
|----------|------------|---------------|----------|
| `GET /fleet/alerts/` | Various filters | List of active alerts with `severity`, `title`, `description`, `state` | Monitor all active fleet alerts |
| `GET /fleet/vehicles/{vehicle_pk}/alerts/` | Vehicle PK | Vehicle-specific alerts | Get alerts for specific vehicle |
| `GET /fleet/alerts/summary/` | None | Alert counts by severity (critical, high, medium, low) | Dashboard summary of alert severity |
| `GET /logbook/fleet_summary/alerts/` | Severity, date range filters | `AlertsData` with total alerts and severity breakdown | Alternative alert summary endpoint |

### Diagnostic Trouble Codes

| Endpoint | Parameters | Response Data | Use Case |
|----------|------------|---------------|----------|
| `GET /logbook/diagnostics/` | `device_id` | List of DTCs with `code` and descriptive `text` | Monitor active diagnostic codes |
| `GET /dongle/{unit_id}/obd/dtc/` | Unit ID | Current DTCs for the unit | Binary sensor for DTC presence |
| `POST /dongle/{unit_id}/obd/dtc/clear/` | Unit ID | None | Service to clear DTCs |
| `GET /logbook/fleet_summary/diagnostics/` | `from_utc`, `end_utc`, `search` | `DiagnosticsData` with total DTCs and code list | Dashboard sensor for "number of active DTCs" |

---

## 5. Device & Connectivity Status 📶

Metadata about the AutoPi dongle itself, including connectivity status and hardware information.

| Endpoint | Parameters | Response Data | Use Case |
|----------|------------|---------------|----------|
| `GET /dongle/devices/{id}/` | Device ID | Detailed device info:<br>• `last_communication`<br>• `connection` status<br>• `imei`<br>• `sim_phone_number`<br>• `sim_data_usage`<br>• `data_usage`<br>• `hw_board_ver` | Monitor device connectivity and data usage |
| `GET /dongle/devices/` | None | List of all registered devices with summary status | Overview of all devices |
| `GET /logbook/fleet_summary/devices/` | `device_id`, `alert_type` | `DevicesData` with counts of devices, firmware versions, alerts, update status | Dashboard showing online units and update needs |

---

## 6. Geofencing 📍

Determine if vehicles are inside or outside predefined geographical areas.

| Endpoint | Parameters | Response Data | Use Case |
|----------|------------|---------------|----------|
| `GET /fleet/vehicles/{vehicle_pk}/geofence_summary/` | Vehicle PK | List of geofences with `state` (inside/outside) and `timestamp` | Create binary sensors for geofence states |
| `GET /fleet/geofences/` | None | All configured geofences with `vehicles_inside_count` | Monitor geofence occupancy |
| `GET /logbook/fleet_summary/geofences/` | `device_id` | `GeofenceSummary` with geofence counts and details | Integration with Home Assistant zones |

---

## 7. Events & Notifications 🔔

| Endpoint | Parameters | Response Data | Use Case |
|----------|------------|---------------|----------|
| `GET /logbook/simplified_events/` | `device_id`, `vehicle_id`, `start_utc`, `end_utc`, `type`, `tags` | Paged events with `ts`, type, tag, name, kwargs | Convert to Home Assistant events/notifications for harsh braking, speeding, geofence entry/exit |

---

## 8. Fleet Summary Dashboards 📈

| Endpoint | Parameters | Response Data | Use Case |
|----------|------------|---------------|----------|
| `GET /logbook/fleet_summary/vehicles/` | `vehicle_id`, `exclude_unassociated` | `VehiclesData` with counts:<br>• All vehicles<br>• Active vehicles now<br>• Driven in last 30 days<br>• On/off location | Sensors for vehicle activity metrics |

---

## Common OBD Data Types

The API accepts these common OBD parameter strings for the `type` or `data_type` query parameters:

- **`obd.speed`** – Vehicle speed
- **`obd.rpm`** – Engine revolutions per minute
- **`obd.coolant_temp`** – Coolant temperature
- **`obd.fuel_rate`** – Fuel consumption rate
- **`obd.throttle_pos`** – Throttle position percentage
- **`obd.engine_load`** – Engine load percentage
- **`obd.mass_air_flow`** – Mass air flow sensor
- **`obd.intake_temp`** – Intake air temperature
- **`obd.fuel_level`** – Fuel tank level percentage
- **`obd.bat`** or **`obd.batt.lvl`** – Battery voltage

---

## Implementation Recommendations

### Initial Setup
1. Obtain API token for authentication
2. Call `/logbook/storage/data_fields/` to discover available sensors for each device
3. Use field information to dynamically create Home Assistant sensor entities

### Core Functionality
- **Device Tracker**: Use `/logbook/v2/most_recent_position/` for real-time location tracking
- **Sensors**: Poll `/logbook/v2/recent_stats/` for latest OBD values
- **History**: Use `/logbook/storage/read/` with aggregations for statistics
- **Alerts**: Monitor `/fleet/alerts/` for vehicle health notifications

### Best Practices
- Cache available data fields to minimize API calls during normal operation
- Use appropriate polling intervals based on data type (location vs. fuel level)
- Implement proper error handling for offline devices
- Consider using fleet summary endpoints for dashboard overviews rather than multiple individual calls

---

## Summary

The AutoPi API provides comprehensive vehicle telemetry suitable for a full-featured Home Assistant integration. Start with position tracking and basic OBD sensors, then expand to include trips, diagnostics, and geofencing based on user needs. The dynamic field discovery ensures the integration can adapt to different vehicle capabilities without hardcoding specific sensors.