---
title: Getting Started
description: Complete guide to setting up the AutoPi Home Assistant integration
---

# Getting Started

This guide will walk you through setting up the AutoPi Home Assistant integration from start to finish.

## Prerequisites

Before you begin, ensure you have:

### AutoPi Requirements
- **AutoPi Account**: Active account at [app.autopi.io](https://app.autopi.io)
- **AutoPi Device**: At least one AutoPi device installed in your vehicle
- **API Token**: AutoPi API token with vehicle access permissions

### Home Assistant Requirements
- **Home Assistant**: Version 2023.1.0 or later
- **Administrator Access**: Ability to install custom integrations
- **Internet Connection**: For communication with AutoPi cloud services

## Step 1: Obtain AutoPi API Token

### Method 1: AutoPi Dashboard (Recommended)
1. Log in to [app.autopi.io](https://app.autopi.io)
2. Navigate to **Account Settings** → **API Tokens**
3. Click **Generate New Token**
4. Give your token a descriptive name (e.g., "Home Assistant")
5. Select appropriate permissions (minimum: vehicle read access)
6. **Copy and save** the token securely

### Method 2: API Documentation
1. Visit the [AutoPi API documentation](https://api.autopi.io/docs)
2. Follow the authentication guide
3. Generate a token programmatically if needed

!!! warning "Token Security"
    Your API token provides access to your vehicle data. Store it securely and never share it publicly.

## Step 2: Install the Integration

Choose your preferred installation method:

### Option A: HACS Installation (Recommended)

1. **Install HACS** (if not already installed):
   - Visit [HACS installation guide](https://hacs.xyz/docs/setup/prerequisites)
   - Follow the installation instructions

2. **Install Integration**:
   - Open **HACS** → **Integrations**
   - Search for **AutoPi** in the default HACS list
   - Click **Install** and restart Home Assistant

### Option B: Manual Installation

1. **Download Latest Release**:
   - Go to [GitHub Releases](https://github.com/rknightion/autopi-ha/releases)
   - Download `autopi.zip` from the latest release

2. **Extract Files**:
   ```bash
   # Extract to your Home Assistant config directory
   unzip autopi.zip -d config/custom_components/
   ```

3. **Restart Home Assistant**:
   - Restart your Home Assistant instance
   - The integration will be available after restart

## Step 3: Add Integration

1. **Navigate to Integrations**:
   - Go to **Settings** → **Devices & Services**
   - Click **+ Add Integration**

2. **Search for AutoPi**:
   - Type "AutoPi" in the search box
   - Select **AutoPi** from the results

3. **Configure Connection**:
   - **API Token**: Enter your AutoPi API token
   - **Base URL** (optional): Use default unless you have a custom endpoint
   - Click **Submit**

4. **Select Vehicles**:
   - The integration will discover your vehicles
   - Select which vehicles you want to monitor
   - Click **Submit**

## Step 4: Configure Options (Optional)

After adding the integration, you can configure update intervals:

1. **Access Integration Options**:
   - Go to **Settings** → **Devices & Services**
   - Find **AutoPi** integration
   - Click **Configure**

2. **Set Update Interval**:
   - **Update Interval** (1-10 min): All vehicle data including position, status, and metrics, default 1 minute

3. **Save Configuration**:
   - Click **Submit**
   - Integration will reload with new settings

## Step 5: Verify Installation

After setup, you should see:

### New Devices
- One device per monitored vehicle
- Named with vehicle's call name or license plate
- Located under **Settings** → **Devices & Services** → **AutoPi**

### New Entities
For each vehicle:
- **Device Tracker**: `device_tracker.{vehicle_name}`
- **Status Sensor**: `sensor.{vehicle_name}_status`
- **Position Sensors**: Speed, altitude, course, GPS satellites
- **Diagnostic Sensors**: Latitude, longitude

Integration-wide:
- **Vehicle Count**: `sensor.autopi_vehicle_count`
- **API Statistics**: API calls, failures, success rate
- **Performance**: Update duration

### Dashboard Cards
The entities will automatically appear in:
- **Map card**: Vehicle locations
- **Entity cards**: Vehicle status and metrics
- **History graphs**: Sensor data over time

## Troubleshooting

### Common Issues

#### "Invalid API Token"
- Verify your token is correct and hasn't expired
- Check token permissions include vehicle access
- Regenerate token if necessary

#### "No Vehicles Found"
- Ensure your AutoPi devices are online
- Check vehicle registration in AutoPi dashboard
- Verify API token has access to vehicles

#### "Connection Failed"
- Check internet connectivity
- Verify AutoPi service status
- Try again after a few minutes

#### "Integration Won't Load"
- Restart Home Assistant completely
- Check logs for detailed error messages
- Verify installation files are correct

### Getting Help

If you encounter issues:

1. **Check Logs**:
   ```yaml
   # Add to configuration.yaml for detailed logging
   logger:
     default: info
     logs:
       custom_components.autopi: debug
   ```

2. **Search Issues**: Check [GitHub Issues](https://github.com/rknightion/autopi-ha/issues)

3. **Report Bugs**: Create a new issue with:
   - Home Assistant version
   - Integration version
   - Relevant log entries
   - Steps to reproduce

## Next Steps

Once installation is complete:

- **[Configuration Guide](configuration.md)**: Detailed configuration options
- **[Entity Reference](entities.md)**: Complete list of available entities
- **[API Optimization](api-optimization.md)**: Optimize API usage and performance
- **[Vehicle Data](vehicle-data.md)**: Understanding vehicle data and attributes

## Security Best Practices

### API Token Management
- Store tokens securely
- Rotate tokens periodically
- Use minimal required permissions
- Monitor token usage in AutoPi dashboard

### Network Security
- Use HTTPS for Home Assistant (recommended)
- Consider VPN for remote access
- Monitor integration logs for unusual activity

### Data Privacy
- Vehicle location data is sensitive
- Review Home Assistant data retention policies
- Consider excluding location entities from recorder if desired 
