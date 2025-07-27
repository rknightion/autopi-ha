# AutoPi API Endpoints for Home Assistant Integration

Based on the provided OpenAPI specification, here are the potential API calls and data points of interest for a comprehensive Home Assistant integration.

---

### **1. Vehicle Tracking & Location** 🛰️

These endpoints are essential for the core `device_tracker` functionality in Home Assistant, providing the vehicle's geographical location and related data.

| Data/Metric of Interest | API Endpoint(s) | Description |
| :--- | :--- | :--- |
| **Current Vehicle Position** | `GET /logbook/v2/most_recent_position/` | Retrieves the most recent cached GPS position for a single specified vehicle (`device_id` or `vehicle_id`). The response includes latitude, longitude, speed, altitude, and course. |
| **All Vehicle Positions** | `GET /logbook/v2/most_recent_positions/` | Fetches the latest known positions for all vehicles in your fleet. This is useful for displaying all vehicles on a single map. |
| **Historical Positions** | `GET /logbook/storage/raw/` | Query historical location data by setting the `data_type` parameter to a position-related field (e.g., `track.pos.loc`). Requires a `device_id` and a time range (`start_utc`, `end_utc`). |

---

### **2. Vehicle Status & Metrics** 📊

These endpoints provide access to a wide range of sensor data from the vehicle's OBD-II port or the AutoPi device itself. This is where you'll get data like fuel level, speed, battery voltage, and more.

| Data/Metric of Interest | API Endpoint(s) | Description |
| :--- | :--- | :--- |
| **Discovering Available Metrics** | `GET /logbook/storage/data_fields/` | **This is a crucial first step.** This endpoint returns a list of all available data fields (e.g., `obd.speed`, `obd.fuel_level`, `obd.batt.lvl`) for a specific device. You can use this list to dynamically create sensors in Home Assistant. |
| **Latest Sensor Data (Real-time)** | `GET /logbook/v2/recent_stats/` | Retrieves the most recently logged telemetry data for a specified device. You can query for a specific data type (e.g., `type=obd.fuel_level`) to get its latest value and timestamp. |
| **Historical Sensor Data** | `GET /logbook/storage/read/` | Fetches historical data for a specific field (discovered via `/logbook/storage/data_fields/`) over a time range. It supports aggregations like `avg`, `min`, `max`, making it perfect for generating history graphs. |
| **Vehicle Mileage** | `GET /fleet/vehicles/{id}/` | The `FleetVehicle` object in the response contains a `mileage` field. |
| **Device Battery/Voltage** | `GET /logbook/v2/recent_stats/` | Use this to get the latest value for fields like `obd.batt.lvl` or similar voltage indicators. |

---

### **3. Driving & Trip Data** 🚗

Monitor and analyze trip history, including distance, duration, and start/end locations.

| Data/Metric of Interest | API Endpoint(s) | Description |
| :--- | :--- | :--- |
| **List of Recent Trips** | `GET /logbook/v2/trips/` | Returns a paginated list of all recorded trips for your vehicles. |
| **Specific Trip Details** | `GET /logbook/v2/trips/{id}/` | Retrieves detailed information for a single trip, including `start_time_utc`, `end_time_utc`, `start_position`, `end_position`, `duration`, and `distanceKm`. |
| **Driving State** | `GET /fleet/vehicles/` | The `driving` boolean filter can indicate which vehicles are currently in motion. The vehicle object itself might contain state information that implies driving. |

---

### **4. Vehicle Diagnostics & Alerts** ⚠️

Keep track of the vehicle's health by monitoring for Diagnostic Trouble Codes (DTCs) and other system alerts.

| Data/Metric of Interest | API Endpoint(s) | Description |
| :--- | :--- | :--- |
| **Active Alerts** | `GET /fleet/alerts/` | Lists all active alerts for the fleet. The response includes `severity`, `title`, `description`, and `state` (e.g., OPEN, RESOLVED). |
| **Vehicle-Specific Alerts** | `GET /fleet/vehicles/{vehicle_pk}/alerts/` | Retrieves alerts for a specific vehicle. |
| **Alert Summary** | `GET /fleet/alerts/summary/` | Provides a summarized count of alerts grouped by severity (critical, high, medium, low). |
| **Diagnostic Trouble Codes (DTCs)** | `GET /logbook/diagnostics/` | Returns a list of logged DTCs for a specified device, including the error `code` and descriptive `text`. |

---

### **5. Device & Connectivity Status** 📶

These endpoints provide metadata about the AutoPi dongle itself, such as its connectivity status and hardware information.

| Data/Metric of Interest | API Endpoint(s) | Description |
| :--- | :--- | :--- |
| **Device Details & Status** | `GET /dongle/devices/{id}/` | Provides detailed information about a specific dongle, including `last_communication` timestamp, `connection` status, `imei`, `sim_phone_number`, `sim_data_usage`, and `hw_board_ver`. |
| **List of All Devices** | `GET /dongle/devices/` | Returns a list of all registered devices with their summary status. |
| **Data Usage** | `GET /dongle/devices/{id}/` | The `Device` object contains `data_usage` and `sim_data_usage` fields. |

---

### **6. Geofencing** 📍

Determine if a vehicle is inside or outside of a predefined geographical area.

| Data/Metric of Interest | API Endpoint(s) | Description |
| :--- | :--- | :--- |
| **Geofence State for a Vehicle** | `GET /fleet/vehicles/{vehicle_pk}/geofence_summary/` | Returns a list of geofences relevant to the vehicle and includes the `state` (e.g., 'inside' or 'outside') and a `timestamp`. This is ideal for creating binary sensors. |
| **List Geofences** | `GET /fleet/geofences/` | Lists all configured geofences and shows how many vehicles are currently inside each one (`vehicles_inside_count`). |
| **Check if Vehicle is in any Geofence** | `GET /fleet/vehicles/` | The `FleetVehicleList` object contains a `geofences` field that can indicate which, if any, geofence a vehicle is in. |