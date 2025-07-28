---
title: Contributing
description: Guide for contributing to the AutoPi Home Assistant integration
---

# Contributing

Thank you for your interest in contributing to the AutoPi Home Assistant integration! This guide will help you get started with contributing to the project.

## Ways to Contribute

### 🐛 Bug Reports
Help us improve by reporting bugs you encounter:

- **Search existing issues** before creating new ones
- **Use issue templates** for consistent reporting
- **Provide detailed information** including logs and steps to reproduce
- **Test with latest version** to ensure the bug still exists

### 💡 Feature Requests
Suggest new features or improvements:

- **Check existing requests** to avoid duplicates
- **Describe the use case** and how it would benefit users
- **Consider implementation complexity** and AutoPi API capabilities
- **Be open to discussion** about the best approach

### 📝 Documentation
Improve documentation for users and developers:

- **Fix typos and errors** in existing documentation
- **Add missing information** or clarify confusing sections
- **Create examples** and tutorials
- **Translate documentation** to other languages

### 💻 Code Contributions
Contribute code improvements and new features:

- **Bug fixes** for reported issues
- **New features** that enhance functionality
- **Performance improvements** and optimizations
- **Test coverage** improvements

## Getting Started

### Development Environment

1. **Prerequisites**:
   - Python 3.11 or later
   - Git
   - Home Assistant development environment
   - AutoPi account for testing

2. **Setup**:
   ```bash
   # Fork and clone the repository
   git clone https://github.com/YOUR_USERNAME/autopi-ha.git
   cd autopi-ha
   
   # Install dependencies
   uv sync --all-extras
   
   # Install pre-commit hooks
   uv run pre-commit install
   ```

3. **Verify Setup**:
   ```bash
   # Run tests
   uv run pytest
   
   # Run linting
   uv run ruff check .
   uv run mypy .
   ```

### Project Structure

```
autopi-ha/
├── custom_components/autopi/    # Main integration code
├── tests/                       # Test suite
├── docs/                        # Documentation
├── scripts/                     # Development scripts
├── .github/                     # GitHub workflows
├── pyproject.toml              # Project configuration
└── Makefile                    # Development commands
```

## Development Workflow

### 1. Choose an Issue

- **Browse open issues** on GitHub
- **Look for "good first issue"** labels for beginners
- **Ask questions** if you need clarification
- **Assign yourself** to avoid duplicate work

### 2. Create a Branch

```bash
# Create and switch to a new branch
git checkout -b feature/your-feature-name

# Or for bug fixes
git checkout -b fix/issue-description
```

### 3. Make Changes

#### Code Guidelines

- **Follow existing patterns** in the codebase
- **Use type hints** throughout your code
- **Add docstrings** to classes and functions
- **Keep functions focused** and single-purpose
- **Handle errors gracefully** with appropriate exceptions

#### Example Code Style

```python
class ExampleSensor(AutoPiVehicleEntity, SensorEntity):
    """Example sensor for demonstration.
    
    This sensor shows how to implement a new vehicle sensor
    following the project's conventions.
    """
    
    _attr_icon = "mdi:example"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    
    def __init__(
        self,
        coordinator: AutoPiDataUpdateCoordinator,
        vehicle_id: str,
    ) -> None:
        """Initialize the example sensor.
        
        Args:
            coordinator: The data coordinator
            vehicle_id: The vehicle ID
        """
        super().__init__(coordinator, vehicle_id, "example")
        self._attr_name = "Example"
    
    @property
    def native_value(self) -> float | None:
        """Return the sensor value."""
        if vehicle := self.vehicle:
            return vehicle.example_data
        return None
```

### 4. Write Tests

All code changes should include appropriate tests:

```python
async def test_example_sensor(hass, mock_coordinator):
    """Test example sensor functionality."""
    # Arrange
    sensor = ExampleSensor(mock_coordinator, "test_vehicle")
    
    # Act
    await sensor.async_update()
    
    # Assert
    assert sensor.native_value == expected_value
```

### 5. Update Documentation

- **Update docstrings** for new or changed code
- **Add user documentation** for new features
- **Update changelog** for notable changes
- **Run documentation generation**:
  ```bash
  uv run python scripts/generate_docs.py
  ```

### 6. Test Your Changes

```bash
# Run all tests
uv run pytest

# Run specific tests
uv run pytest tests/test_sensor.py

# Run with coverage
uv run pytest --cov=custom_components.autopi

# Test with real Home Assistant
cp -r custom_components/autopi /path/to/ha/config/custom_components/
```

### 7. Commit Changes

```bash
# Stage your changes
git add .

# Commit with descriptive message
git commit -m "feat: add example sensor for vehicle data

- Implement ExampleSensor class
- Add tests for sensor functionality
- Update documentation"
```

#### Commit Message Format

Use conventional commits format:

- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation changes
- `test:` for test additions/changes
- `refactor:` for code refactoring
- `chore:` for maintenance tasks

### 8. Push and Create Pull Request

```bash
# Push your branch
git push origin feature/your-feature-name

# Create pull request on GitHub
# Fill out the PR template with details
```

## Pull Request Guidelines

### PR Requirements

- **Clear description** of changes and motivation
- **Tests included** for new functionality
- **Documentation updated** as needed
- **All checks passing** (tests, linting, etc.)
- **No breaking changes** without discussion

### PR Template

```markdown
## Description
Brief description of what this PR does.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring

## Testing
- [ ] Tests added/updated
- [ ] Manual testing completed
- [ ] All checks passing

## Checklist
- [ ] Code follows project style
- [ ] Documentation updated
- [ ] Changelog updated
```

### Review Process

1. **Automated checks** must pass
2. **Maintainer review** of code and approach
3. **Testing** by maintainers or community
4. **Feedback incorporation** as needed
5. **Final approval** and merge

## Coding Standards

### Code Quality

The project uses several tools to maintain code quality:

```bash
# Linting with Ruff
uv run ruff check .
uv run ruff format .

# Type checking with MyPy
uv run mypy custom_components

# Security scanning with Bandit
uv run bandit -r custom_components
```

### Testing Standards

- **Unit tests** for individual components
- **Integration tests** for component interaction
- **Mock external dependencies** (don't call real APIs)
- **Aim for >90% coverage** on new code
- **Test error conditions** and edge cases

### Documentation Standards

- **Docstrings** for all public classes and methods
- **Type hints** throughout the codebase
- **User documentation** for new features
- **Code comments** for complex logic
- **Examples** for usage patterns

## Specific Contribution Areas

### 🔌 Adding New Sensors

1. **Identify data source** in AutoPi API
2. **Design sensor class** extending base entities
3. **Implement data fetching** in coordinator
4. **Add tests** for sensor behavior
5. **Update documentation** with new sensor info

### 🗺️ Improving Device Tracking

1. **Enhance GPS accuracy** handling
2. **Add location features** (zones, geocoding)
3. **Optimize update frequency** based on movement
4. **Implement geofencing** capabilities

### 📊 API Optimization

1. **Reduce API calls** through better caching
2. **Implement smart scheduling** based on usage
3. **Add connection pooling** improvements
4. **Enhance error recovery** mechanisms

### 🧪 Testing Improvements

1. **Add integration tests** with Home Assistant
2. **Mock more API scenarios** for thorough testing
3. **Performance testing** for large fleets
4. **User acceptance testing** scenarios

## Community Guidelines

### Code of Conduct

- **Be respectful** and inclusive in all interactions
- **Provide constructive feedback** in reviews
- **Help newcomers** get started with contributions
- **Follow GitHub community guidelines**

### Communication

- **Use GitHub issues** for bug reports and feature requests
- **Join discussions** on existing issues before starting work
- **Ask questions** if you're unsure about implementation
- **Provide updates** on work in progress

### Recognition

Contributors are recognized in:

- **Changelog** for notable contributions
- **GitHub contributors** section
- **Release notes** for major features
- **Documentation** acknowledgments

## Development Resources

### Useful Links

- **[Home Assistant Developer Docs](https://developers.home-assistant.io/)**: Core development guide
- **[AutoPi API Docs](https://api.autopi.io/docs)**: API reference
- **[Python Type Hints](https://docs.python.org/3/library/typing.html)**: Type annotation guide
- **[Pytest Documentation](https://docs.pytest.org/)**: Testing framework

### Development Tools

```bash
# Makefile commands
make help          # Show available commands
make test          # Run tests
make lint          # Run linting
make format        # Format code
make check-all     # Run all checks
make docgen        # Generate documentation
```

### Debugging Tips

1. **Enable debug logging**:
   ```yaml
   logger:
     logs:
       custom_components.autopi: debug
   ```

2. **Use VS Code debugger** with Home Assistant
3. **Test with mock data** before real API calls
4. **Check entity registry** for proper registration

## Release Process

### Version Bumping

1. **Update version** in `manifest.json`
2. **Update changelog** with new features
3. **Create release** with GitHub Actions
4. **Test release** with HACS installation

### Release Types

- **Patch releases** (0.1.1): Bug fixes, minor improvements
- **Minor releases** (0.2.0): New features, non-breaking changes
- **Major releases** (1.0.0): Breaking changes, major features

## Getting Help

### Where to Get Help

- **GitHub Discussions**: General questions and ideas
- **GitHub Issues**: Specific bugs or feature requests
- **Code Comments**: In-line questions during review
- **Documentation**: Comprehensive guides and references

### Maintainer Response

- **Issues**: Usually within 1-3 days
- **Pull Requests**: Review within 1 week
- **Questions**: Best effort response
- **Security Issues**: Immediate attention

Thank you for contributing to the AutoPi Home Assistant integration! Your contributions help make the project better for everyone. 🚗✨ 

