---
title: Installation
description: Detailed installation instructions for the AutoPi Home Assistant integration
---

# Installation

This page provides detailed installation instructions for the AutoPi Home Assistant integration.

## Prerequisites

### System Requirements

| Component | Requirement | Notes |
|-----------|------------|-------|
| Home Assistant | 2023.1.0+ | Core or Supervised installation |
| Python | 3.11+ | Handled automatically by Home Assistant |
| Network | Internet access | Required for AutoPi API communication |
| Storage | ~5MB | For integration files and cache |

### AutoPi Requirements

- **Active AutoPi Account**: Sign up at [autopi.io](https://autopi.io)
- **AutoPi Device**: Installed and connected vehicle device
- **API Access**: Valid API token with vehicle permissions

## Installation Methods

### HACS Installation

[HACS](https://hacs.xyz) is the recommended installation method for custom integrations.

#### Step 1: Install HACS (if needed)

If you don't have HACS installed:

1. **Prerequisites**:
   - Home Assistant Supervisor (for Supervisor installations)
   - Git installed (for manual HACS installation)

2. **Install HACS**:
   - Follow the [official HACS installation guide](https://hacs.xyz/docs/setup/prerequisites)
   - Restart Home Assistant after installation

#### Step 2: Install from the HACS Default Repository

1. **Open HACS**:
   - Navigate to **HACS** in your Home Assistant sidebar
   - Click on **Integrations**

2. **Find AutoPi**:
   - Search for **AutoPi** in the default HACS integrations list
   - Open the AutoPi integration page

3. **Install**:
   - Click **Install**
   - Select the version (latest recommended)
   - Wait for download to complete

4. **Restart Home Assistant**:
   - Go to **Settings** → **System** → **Restart**
   - Wait for restart to complete

### Manual Installation

For advanced users or custom Home Assistant setups.

#### Step 1: Download Integration

Choose one of these methods:

**Method A: Download Release**
```bash
# Download latest release
wget https://github.com/rknightion/autopi-ha/releases/latest/download/autopi.zip

# Extract to custom_components
unzip autopi.zip -d /config/custom_components/
```

**Method B: Clone Repository**
```bash
# Clone the repository
git clone https://github.com/rknightion/autopi-ha.git

# Copy integration files
cp -r autopi-ha/custom_components/autopi /config/custom_components/
```

#### Step 2: Verify Installation

Check that files are in the correct location:

```
/config/custom_components/autopi/
├── __init__.py
├── config_flow.py
├── const.py
├── coordinator.py
├── manifest.json
├── sensor.py
├── device_tracker.py
└── ... (other files)
```

#### Step 3: Restart Home Assistant

- Restart your Home Assistant instance
- Check logs for any errors during startup

### Docker Installation

For Docker-based Home Assistant installations.

#### Docker Compose Example

```yaml
version: '3'
services:
  homeassistant:
    container_name: homeassistant
    image: ghcr.io/home-assistant/home-assistant:stable
    volumes:
      - ./config:/config
      - ./custom_components:/config/custom_components
    restart: unless-stopped
    # ... other configuration
```

#### Installation Steps

1. **Prepare Directory**:
   ```bash
   mkdir -p ./custom_components/autopi
   ```

2. **Download Integration**:
   ```bash
   # Download and extract
   wget -O autopi.zip https://github.com/rknightion/autopi-ha/releases/latest/download/autopi.zip
   unzip autopi.zip -d ./custom_components/
   ```

3. **Restart Container**:
   ```bash
   docker-compose restart homeassistant
   ```

## Installation Verification

### Check Integration Loading

1. **Navigate to Integrations**:
   - Go to **Settings** → **Devices & Services**
   - Click **+ Add Integration**
   - Search for "AutoPi"

2. **Verify Availability**:
   - AutoPi should appear in the search results
   - Icon should be visible
   - Description should be present

### Check Logs

Enable debug logging to verify installation:

```yaml
# configuration.yaml
logger:
  default: info
  logs:
    custom_components.autopi: debug
```

Look for these log entries:
```
INFO: AutoPi integration loaded successfully
DEBUG: AutoPi manifest loaded: version X.X.X
```

## Troubleshooting Installation

### Common Issues

#### Integration Not Found
**Symptoms**: AutoPi doesn't appear in integration list

**Solutions**:
1. Verify files are in correct directory
2. Check file permissions (readable by Home Assistant)
3. Restart Home Assistant completely
4. Check logs for loading errors

#### Version Conflicts
**Symptoms**: Integration fails to load with dependency errors

**Solutions**:
1. Check Home Assistant version compatibility
2. Update Home Assistant to latest version
3. Verify integration version compatibility

#### HACS Issues
**Symptoms**: HACS can't find or install integration

**Solutions**:
1. Verify HACS is properly installed
2. Check internet connectivity
3. Manually refresh HACS repositories
4. Clear HACS cache and retry

### Log Analysis

Common log entries and meanings:

| Log Entry | Meaning | Action |
|-----------|---------|--------|
| `AutoPi integration loaded` | Success | None needed |
| `Unable to load manifest` | File corruption | Reinstall integration |
| `Import error` | Missing dependencies | Check HA version |
| `Permission denied` | File permissions | Fix file ownership |

### Getting Help

If installation fails:

1. **Check Documentation**: Review this guide and FAQ
2. **Search Issues**: Look for similar problems on GitHub
3. **Create Issue**: Report with installation details:
   - Home Assistant version
   - Installation method used
   - Complete error logs
   - System information

## Next Steps

After successful installation:

1. **[Getting Started](getting-started.md)**: Complete setup guide
2. **[Configuration](configuration.md)**: Configure the integration
3. **[Vehicle Data](vehicle-data.md)**: Understand available data

## Updates and Maintenance

### Updating via HACS

1. **Check for Updates**:
   - HACS will notify of available updates
   - Updates appear in HACS dashboard

2. **Install Update**:
   - Click **Update** in HACS
   - Select version to install
   - Restart Home Assistant

### Manual Updates

1. **Download New Version**:
   - Get latest release from GitHub
   - Follow manual installation steps

2. **Backup Configuration**:
   - Integration settings are preserved
   - Consider backing up config entries

### Version Management

- **Stable Releases**: Recommended for production
- **Beta Releases**: Early access to new features
- **Development**: Latest code, may be unstable

Keep track of installed version in:
- HACS interface
- Integration device info
- `custom_components/autopi/manifest.json` 
