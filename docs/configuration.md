---
title: Configuration
description: Complete configuration guide for the AutoPi Home Assistant integration
---

# Configuration

This guide covers all configuration options for the AutoPi Home Assistant integration.

## Initial Setup

### Adding the Integration

1. **Navigate to Integrations**:
   - Go to **Settings** → **Devices & Services**
   - Click **+ Add Integration**
   - Search for and select **AutoPi**

2. **Basic Configuration**:
   
   | Field | Required | Description | Default |
   |-------|----------|-------------|---------|
   | API Token | Yes | Your AutoPi API authentication token | - |
   | Base URL | No | AutoPi API endpoint | `https://api.autopi.io` |

### API Token Setup

#### Obtaining Your Token
1. Log in to [app.autopi.io](https://app.autopi.io)
2. Navigate to **Account Settings** → **API Tokens**
3. Create a new token with appropriate permissions:
   - **Read Vehicles**: Required for basic functionality
   - **Read Vehicle Data**: Required for sensor data
   - **Read Positions**: Required for location tracking

#### Token Validation
The integration automatically validates your token during setup:
- ✅ **Valid Token**: Proceeds to vehicle selection
- ❌ **Invalid Token**: Shows error and requires re-entry
- ⚠️ **Limited Permissions**: May limit available features

### Vehicle Selection

After token validation, select which vehicles to monitor:

1. **Available Vehicles**: All vehicles associated with your account
2. **Selection**: Check vehicles you want to include
3. **None Selected**: Integration won't create vehicle entities

!!! tip "Multiple Vehicles"
    You can monitor unlimited vehicles. Each vehicle creates its own device and entities.

## Configuration Options

Access configuration options after initial setup:

1. **Navigate to Integration**:
   - Go to **Settings** → **Devices & Services**
   - Find **AutoPi** integration
   - Click **Configure**

### Update Intervals

Configure how frequently different types of data are fetched:

#### Fast Update Ring (Position Data)
- **Purpose**: GPS position, speed, altitude, course
- **Default**: 1 minute
- **Range**: 1-60 minutes
- **Impact**: Higher frequency = more accurate tracking, more API calls

#### Medium Update Ring (Vehicle Status)
- **Purpose**: Vehicle profile, connection status
- **Default**: 5 minutes  
- **Range**: 1-60 minutes
- **Impact**: Generally stable data, infrequent updates sufficient

#### Slow Update Ring (Reserved)
- **Purpose**: Future features (trip history, maintenance data)
- **Default**: 15 minutes
- **Range**: 1-60 minutes
- **Impact**: Currently unused, reserved for future expansion

### Configuration Examples

#### High-Frequency Tracking
For real-time vehicle monitoring:
```
Fast Updates: 1 minute
Medium Updates: 2 minutes
Slow Updates: 15 minutes
```
- **Pros**: Near real-time data
- **Cons**: Higher API usage

#### Balanced Configuration
For typical home automation:
```
Fast Updates: 2 minutes
Medium Updates: 5 minutes
Slow Updates: 15 minutes
```
- **Pros**: Good balance of freshness and efficiency
- **Cons**: Slight delay in position updates

#### Conservative Configuration
For minimal API usage:
```
Fast Updates: 10 minutes
Medium Updates: 30 minutes
Slow Updates: 60 minutes
```
- **Pros**: Minimal API calls
- **Cons**: Less responsive data

## Advanced Configuration

### API Optimization

#### Rate Limiting
The integration automatically handles AutoPi API rate limits:
- **Exponential Backoff**: Automatic retry with increasing delays
- **Bulk Operations**: Fetches all vehicle positions in single calls
- **Error Handling**: Graceful handling of temporary API issues

#### Request Optimization
- **Conditional Requests**: Only fetch when data might have changed
- **Efficient Endpoints**: Uses bulk APIs where available
- **Connection Pooling**: Reuses HTTP connections

### Entity Configuration

#### Entity Naming
Entities follow this pattern:
```
{vehicle_name}_{entity_type}
```

Examples:
- `sensor.my_car_speed`
- `device_tracker.my_car`
- `sensor.my_car_altitude`

#### Entity Categories
Entities are categorized for organization:
- **Primary**: Main functional entities (speed, location)
- **Diagnostic**: Technical entities (API calls, coordinates)

### Integration-Level Entities

These entities monitor the integration itself:

| Entity | Purpose | Category |
|--------|---------|----------|
| Vehicle Count | Number of monitored vehicles | Diagnostic |
| API Calls | Total API requests made | Diagnostic |
| Failed API Calls | Number of failed requests | Diagnostic |
| API Success Rate | Percentage of successful requests | Diagnostic |
| Update Duration | Time taken for last update | Diagnostic |

## Error Handling Configuration

### Authentication Errors
When API token issues occur:
- **Automatic Detection**: Integration detects auth failures
- **Reauth Flow**: Prompts for new token without reconfiguration
- **Preservation**: Vehicle selection and options are preserved

### Connection Issues
For network or service problems:
- **Retry Logic**: Automatic retries with exponential backoff
- **Graceful Degradation**: Entities remain available with last known data
- **Status Indication**: Entity availability reflects connection status

### Configuration Validation
All configuration changes are validated:
- **Range Checking**: Update intervals within allowed bounds
- **API Testing**: Token validation before saving
- **Error Messages**: Clear feedback for invalid configurations

## YAML Configuration

While the integration uses the UI for configuration, you can inspect and backup your settings:

### Config Entry Information
```yaml
# Configuration is stored in .storage/core.config_entries
# This is for reference only - do not edit manually
autopi:
  entry_id: "unique_entry_identifier"
  version: 1
  domain: "autopi"
  title: "AutoPi"
  data:
    api_key: "your_encrypted_token"
    base_url: "https://api.autopi.io"
    selected_vehicles: 
      - "vehicle_id_1"
      - "vehicle_id_2"
  options:
    update_interval_fast: 1
    update_interval_medium: 5
    update_interval_slow: 15
```

### Logger Configuration
Add to `configuration.yaml` for debugging:
```yaml
logger:
  default: info
  logs:
    custom_components.autopi: debug
    custom_components.autopi.coordinator: debug
    custom_components.autopi.client: debug
```

## Troubleshooting Configuration

### Common Issues

#### "Configuration Invalid"
**Causes**:
- Invalid API token format
- Network connectivity issues
- AutoPi service unavailable

**Solutions**:
1. Verify token is copied correctly
2. Check internet connectivity
3. Try configuration again later

#### "No Vehicles Available"
**Causes**:
- Token lacks vehicle permissions
- No vehicles registered in AutoPi account
- All vehicles offline

**Solutions**:
1. Check token permissions in AutoPi dashboard
2. Verify vehicles are registered and online
3. Wait for vehicles to come online

#### Configuration Won't Save
**Causes**:
- Update intervals out of range
- Invalid token during validation
- Integration restart required

**Solutions**:
1. Use intervals between 1-60 minutes
2. Re-validate API token
3. Restart Home Assistant if needed

### Performance Tuning

#### Optimize for Your Use Case

**Real-time Tracking**:
- Fast updates: 1-2 minutes
- Monitor API usage carefully
- Consider AutoPi plan limits

**Casual Monitoring**:
- Fast updates: 5-10 minutes
- Medium updates: 15-30 minutes
- Balances freshness with efficiency

**Minimal Impact**:
- Fast updates: 30+ minutes
- Suitable for occasional checking
- Minimal API usage

#### Monitor Integration Health
Use diagnostic entities to monitor:
- API success rate should be >95%
- Update duration should be <5 seconds
- Failed API calls should be minimal

## Security Considerations

### API Token Security
- **Storage**: Tokens are encrypted in Home Assistant
- **Transmission**: HTTPS only for API communication
- **Rotation**: Regularly rotate tokens for security
- **Permissions**: Use minimal required permissions

### Network Security
- **Firewall**: Ensure outbound HTTPS is allowed
- **VPN**: Consider VPN for enhanced privacy
- **Monitoring**: Monitor unusual API activity

### Data Privacy
- **Location Data**: Vehicle positions are sensitive
- **Retention**: Configure recorder to manage data retention
- **Access**: Control who has access to vehicle entities

## Migration and Backup

### Backing Up Configuration
Integration configuration is automatically backed up with Home Assistant backups. For manual backup:

1. **Config Entries**: Included in HA snapshots
2. **Entity Registry**: Preserves entity customizations
3. **Historical Data**: Included in database backups

### Migration Between Instances
1. **Export Configuration**: Use HA backup system
2. **Import**: Restore backup on new instance
3. **Re-authenticate**: May need to re-enter API token

### Configuration Recovery
If configuration is lost:
1. **Re-add Integration**: Follow initial setup
2. **Restore Settings**: Configure update intervals
3. **Verify Entities**: Check all entities are created correctly 