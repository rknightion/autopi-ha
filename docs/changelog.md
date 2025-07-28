---
title: Changelog
description: Release history and changelog for the AutoPi Home Assistant Integration
---

# Changelog

All notable changes to this project are documented here. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

!!! info "Latest Updates"
    This page shows the most recent changes. For the complete changelog with all releases, see the [full CHANGELOG.md](https://github.com/rknightion/autopi-ha/blob/main/CHANGELOG.md) file.

## [0.1.0] - 2024-01-XX

### Added
- Initial release of AutoPi Home Assistant integration
- Vehicle profile data integration
- GPS position tracking and device trackers
- Comprehensive sensor suite for vehicle monitoring
- Configuration flow with API token authentication
- Vehicle selection during setup
- Multiple update interval configuration (fast, medium, slow)
- API optimization with bulk operations
- Retry logic with exponential backoff
- Integration health monitoring with diagnostic sensors

### Features

#### Core Integration
- **Config Flow**: GUI-based setup with API token validation
- **Vehicle Discovery**: Automatic detection of AutoPi vehicles
- **Multi-vehicle Support**: Monitor unlimited vehicles
- **Options Flow**: Configure update intervals after setup

#### Sensors
- **Vehicle Count**: Total number of monitored vehicles
- **Vehicle Status**: License plate or vehicle name display
- **Position Sensors**: Speed, altitude, course, GPS satellites
- **Diagnostic Sensors**: Latitude, longitude coordinates
- **API Health**: API calls, failures, success rate, update duration

#### Device Tracking
- **GPS Tracking**: Real-time vehicle location on Home Assistant map
- **High Accuracy**: 3-5 meter accuracy in good conditions
- **Automatic Updates**: Configurable update intervals

#### API Integration
- **Optimized Calls**: Bulk API operations for efficiency
- **Rate Limiting**: Automatic handling of API limits
- **Error Recovery**: Graceful handling of network issues
- **Secure Storage**: Encrypted API token storage

### Technical Details

#### Architecture
- **DataUpdateCoordinator**: Efficient data fetching pattern
- **Entity Base Classes**: Shared functionality across entities
- **Type Safety**: Comprehensive type definitions
- **Error Handling**: Custom exception hierarchy

#### Performance
- **Bulk Operations**: Single API call for all vehicle positions
- **Connection Reuse**: HTTP connection pooling
- **Smart Caching**: Reduces redundant API calls
- **Configurable Intervals**: Balance freshness with efficiency

#### Quality
- **Comprehensive Testing**: Unit and integration tests
- **Code Quality**: Linting, formatting, type checking
- **Documentation**: Complete user and developer documentation
- **CI/CD**: Automated testing and quality checks

### Installation
- **HACS Support**: Available through Home Assistant Community Store
- **Manual Installation**: Direct download and installation
- **Requirements**: Home Assistant 2023.1.0+, AutoPi account with API access

### Known Limitations
- **Read-only**: No vehicle control features in initial release
- **Cloud-dependent**: Requires internet connection to AutoPi API
- **OBD-II Data**: Not yet available, planned for future releases
- **Trip History**: Not yet available, planned for future releases

## Planned Features

### Version 0.2.0 (Q2 2024)
- **OBD-II Data Integration**: Engine diagnostics, fuel consumption
- **Binary Sensors**: Engine status, door status, connection status
- **Enhanced Error Handling**: Better diagnostic information
- **Performance Optimizations**: Reduced memory usage

### Version 0.3.0 (Q3 2024)
- **Trip Analytics**: Distance, duration, fuel efficiency
- **Maintenance Tracking**: Service reminders and diagnostics
- **Geofencing**: Custom zone alerts and automation
- **Advanced Automations**: Smart scheduling based on patterns

### Future Versions
- **Local API Support**: If AutoPi adds local connectivity
- **Real-time Updates**: WebSocket integration for instant updates
- **Fleet Management**: Enterprise features for multiple accounts
- **Machine Learning**: Predictive maintenance and behavior analysis

## Migration Notes

### From Pre-release Versions
- No migration needed for first official release
- Custom entity names and automations will be preserved
- API configuration may need to be re-entered

### Breaking Changes
- None in initial release
- Future breaking changes will be clearly documented
- Automatic migration will be provided where possible

## Upgrade Instructions

### HACS Updates
1. Check for updates in HACS dashboard
2. Click "Update" when available
3. Restart Home Assistant

### Manual Updates
1. Download latest release from GitHub
2. Replace files in `custom_components/autopi/`
3. Restart Home Assistant

### Post-upgrade Steps
1. Verify all entities are working
2. Check integration health with diagnostic sensors
3. Update any automations if entity names changed
4. Review configuration options for new features

## Support and Feedback

### Getting Help
- **Documentation**: Comprehensive guides available
- **GitHub Issues**: Bug reports and feature requests
- **Community**: Home Assistant forums and Discord
- **AutoPi Support**: For device-specific issues

### Reporting Issues
When reporting bugs, please include:
- Home Assistant version
- Integration version (from manifest.json)
- Relevant log entries with debug logging enabled
- Steps to reproduce the issue
- Expected vs. actual behavior

### Feature Requests
Feature requests are welcome! Popular requests include:
- Enhanced OBD-II diagnostics
- Trip planning and optimization
- Maintenance scheduling
- Fleet management tools
- Integration with other vehicle platforms

## Contributors

Thanks to all contributors who made this integration possible:

- **Primary Developer**: [@rknightion](https://github.com/rknightion)
- **Community Feedback**: Home Assistant community members
- **Testing**: Beta testers and early adopters
- **Documentation**: Contributors to guides and translations

## License and Legal

- **License**: MIT License
- **AutoPi**: Integration uses AutoPi's public API
- **Home Assistant**: Built for Home Assistant ecosystem
- **Privacy**: No data sent to third parties except AutoPi

## Links and Resources

- **GitHub Repository**: [rknightion/autopi-ha](https://github.com/rknightion/autopi-ha)
- **Documentation**: [Integration Documentation](https://autopi.ha-components.m7kni.com)
- **AutoPi**: [Official AutoPi Website](https://autopi.io)
- **Home Assistant**: [Home Assistant Documentation](https://home-assistant.io/docs)
- **HACS**: [Home Assistant Community Store](https://hacs.xyz)

---

For the complete changelog with all releases and detailed commit history, see the [full CHANGELOG.md](https://github.com/rknightion/autopi-ha/blob/main/CHANGELOG.md) file in the repository. 