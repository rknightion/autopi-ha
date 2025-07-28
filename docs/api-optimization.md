---
title: API Optimization
description: Optimize AutoPi API usage for efficiency and cost management
---

# API Optimization

This guide helps you optimize AutoPi API usage for efficiency, performance, and cost management.

## Understanding API Usage

### API Call Types

The AutoPi integration makes different types of API calls:

| Call Type | Frequency | Purpose | Impact |
|-----------|-----------|---------|--------|
| Vehicle Profile | Medium interval | Get vehicle information | Low frequency |
| Position Data | Fast interval | GPS location and movement | High frequency |
| Authentication | As needed | Token validation | Minimal |
| Bulk Positions | Fast interval | All vehicles at once | Efficient |

### Current Implementation

The integration uses optimized API patterns:

#### Bulk Operations
- **Single Call**: Fetches all vehicle positions in one request
- **Efficiency**: Reduces API calls from N to 1 for N vehicles
- **Rate Limiting**: Lower chance of hitting rate limits

#### Smart Caching
- **Conditional Requests**: Only fetch when data might have changed
- **Local Caching**: Reduces redundant API calls
- **Error Handling**: Graceful fallback during API issues

#### Connection Reuse
- **HTTP Keep-Alive**: Reuses connections for multiple requests
- **Session Management**: Maintains authentication state
- **Connection Pooling**: Efficient network resource usage

## Monitoring API Usage

### Diagnostic Entities

Use these entities to monitor API health:

#### API Call Counters
- **Total API Calls**: `sensor.autopi_api_calls`
- **Failed API Calls**: `sensor.autopi_failed_api_calls`
- **Success Rate**: `sensor.autopi_api_success_rate`

#### Performance Metrics
- **Update Duration**: `sensor.autopi_update_duration`
- **Last Update**: Check entity timestamps

### Setting Up Monitoring

Create dashboard cards to track API usage:

```yaml
# Example dashboard configuration
type: entities
title: AutoPi API Health
entities:
  - sensor.autopi_api_calls
  - sensor.autopi_failed_api_calls
  - sensor.autopi_api_success_rate
  - sensor.autopi_update_duration
```

### Creating Alerts

Set up alerts for API issues:

```yaml
# automation.yaml
- alias: "AutoPi API Success Rate Low"
  trigger:
    - platform: numeric_state
      entity_id: sensor.autopi_api_success_rate
      below: 90
  action:
    - service: notify.mobile_app_your_phone
      data:
        message: "AutoPi API success rate is {{ states('sensor.autopi_api_success_rate') }}%"
```

## Optimizing Update Intervals

### Understanding Trade-offs

| Aspect | Frequent Updates | Infrequent Updates |
|--------|------------------|-------------------|
| **Data Freshness** | Real-time | Delayed |
| **API Usage** | High | Low |
| **Responsiveness** | Immediate | Slower |
| **Battery Impact** | Higher | Lower |

### Recommended Configurations

#### Real-time Tracking
For active vehicle monitoring:
```
Fast Updates (Position): 1-2 minutes
Medium Updates (Status): 5 minutes
Slow Updates (Future): 15 minutes
```

**Use Cases**:
- Fleet management
- Teen driver monitoring
- Security tracking
- Real-time navigation

**Considerations**:
- Higher API usage
- More responsive data
- Better for automations

#### Balanced Usage
For typical home automation:
```
Fast Updates (Position): 5 minutes
Medium Updates (Status): 15 minutes
Slow Updates (Future): 30 minutes
```

**Use Cases**:
- Arrival/departure detection
- General vehicle monitoring
- Family coordination

**Considerations**:
- Good balance of freshness and efficiency
- Suitable for most use cases
- Reasonable API usage

#### Conservative Mode
For minimal API impact:
```
Fast Updates (Position): 15 minutes
Medium Updates (Status): 30 minutes
Slow Updates (Future): 60 minutes
```

**Use Cases**:
- Basic presence detection
- Periodic status checks
- API usage concerns

**Considerations**:
- Lower data freshness
- Minimal API usage
- May miss short trips

### Dynamic Optimization

Consider varying update intervals based on:

#### Vehicle State
- **Moving**: More frequent updates
- **Parked**: Less frequent updates
- **Home**: Minimal updates needed

#### Time of Day
- **Day**: Normal intervals
- **Night**: Reduced frequency
- **Work Hours**: Based on usage patterns

#### Location Context
- **Home**: Lower frequency
- **Away**: Higher frequency
- **Unknown**: Balanced approach

## Rate Limiting and Error Handling

### AutoPi Rate Limits

Understanding AutoPi API limits:

#### Typical Limits
- **Requests per minute**: Varies by plan
- **Concurrent connections**: Usually limited
- **Daily quotas**: Plan-dependent

#### Rate Limit Response
When rate limited, the API returns:
- **HTTP 429**: Too Many Requests
- **Retry-After header**: Suggested wait time
- **Error details**: In response body

### Integration Response

The integration handles rate limits automatically:

#### Exponential Backoff
- **Initial retry**: 1 second delay
- **Increasing delays**: 2s, 4s, 8s, 16s...
- **Maximum delay**: 300 seconds
- **Retry limit**: Configurable

#### Graceful Degradation
- **Entity availability**: Maintains last known state
- **Error logging**: Records issues for debugging
- **User notification**: Clear error messages

#### Recovery Strategies
- **Automatic retry**: Resumes when limits reset
- **Circuit breaker**: Temporarily stops requests if persistent failures
- **Health checks**: Verifies API availability

## Optimizing for Cost

### Understanding Costs

If your AutoPi plan has API limits or costs:

#### Usage Calculation
```
Daily API Calls = (Vehicles × 24 × 60) / Update_Interval_Minutes
```

Examples:
- 1 vehicle, 5-minute updates: 288 calls/day
- 3 vehicles, 2-minute updates: 2,160 calls/day
- 1 vehicle, 15-minute updates: 96 calls/day

#### Cost Factors
- **Number of vehicles**: Linear increase
- **Update frequency**: Inverse relationship
- **Plan tier**: Different rate limits/costs
- **Usage patterns**: Peak vs. off-peak

### Cost Optimization Strategies

#### Vehicle Selection
- **Active vehicles only**: Only monitor vehicles in use
- **Seasonal adjustment**: Disable during storage periods
- **Use-case based**: Different intervals per vehicle

#### Smart Scheduling
- **Time-based intervals**: Reduce updates during inactive hours
- **Presence-based**: Higher frequency when away from home
- **Event-driven**: Increase frequency during trips

#### Bulk Operations
- **Multi-vehicle efficiency**: Single call for all vehicles
- **Batch processing**: Group API operations
- **Shared resources**: Coordinate between features

## Advanced Optimization

### Custom Update Logic

For advanced users, consider implementing:

#### Proximity-based Updates
- **Home zone**: Minimal updates when home
- **Away zone**: Normal updates when away
- **Travel detection**: Increased frequency during movement

#### Battery-aware Updates
- **Vehicle state**: Adjust based on ignition status
- **Power management**: Reduce updates when vehicle is off
- **Smart intervals**: Dynamic based on activity

### Integration with Other Systems

#### Home Assistant Automations
```yaml
# Reduce updates when home
- alias: "AutoPi Conservative Mode at Home"
  trigger:
    - platform: zone
      entity_id: device_tracker.my_car
      zone: zone.home
      event: enter
  action:
    # Custom service to adjust intervals
    # (This would require custom implementation)
```

#### External Systems
- **Fleet management**: Coordinate with other platforms
- **Cost tracking**: Monitor usage across systems
- **Analytics**: Combine with other data sources

## Troubleshooting Performance

### Common Issues

#### High API Usage
**Symptoms**:
- Rapid increase in API call count
- Rate limiting errors
- Unexpected costs

**Solutions**:
1. Check update intervals are reasonable
2. Verify vehicle count is correct
3. Monitor for failed requests causing retries
4. Review integration logs for issues

#### Slow Updates
**Symptoms**:
- Long update durations
- Stale data
- Entity unavailability

**Solutions**:
1. Check network connectivity
2. Verify AutoPi service status
3. Review error logs
4. Test API access directly

#### Failed Requests
**Symptoms**:
- Low success rate
- Frequent errors
- Inconsistent data

**Solutions**:
1. Verify API token validity
2. Check network stability
3. Review AutoPi service status
4. Consider reducing update frequency temporarily

### Performance Monitoring

#### Key Metrics to Track

| Metric | Healthy Range | Action Threshold |
|--------|---------------|------------------|
| Success Rate | >95% | <90% |
| Update Duration | <5 seconds | >10 seconds |
| Failed Calls | <5% of total | >10% of total |
| API Calls/Day | As planned | 50% over plan |

#### Logging Configuration

Enable detailed logging for troubleshooting:

```yaml
# configuration.yaml
logger:
  default: info
  logs:
    custom_components.autopi.client: debug
    custom_components.autopi.coordinator: debug
```

### Best Practices Summary

1. **Monitor Usage**: Track API calls and success rates
2. **Right-size Intervals**: Balance freshness with efficiency
3. **Use Bulk Operations**: Let integration optimize calls
4. **Handle Errors Gracefully**: Don't increase frequency on failures
5. **Plan for Growth**: Consider future vehicle additions
6. **Regular Review**: Periodically assess and adjust settings

## Future Optimizations

### Planned Improvements

#### Intelligent Scheduling
- **Machine learning**: Learn usage patterns
- **Predictive updates**: Anticipate when data is needed
- **Context awareness**: Adjust based on Home Assistant state

#### Enhanced Caching
- **Smart invalidation**: Only update when necessary
- **Cross-session persistence**: Remember state across restarts
- **Selective updates**: Update only changed data

#### Advanced Error Handling
- **Better diagnostics**: More detailed error reporting
- **Self-healing**: Automatic recovery from common issues
- **Adaptive behavior**: Learn from errors and adjust 