"""Test the AutoPi integration init."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.core import HomeAssistant

from custom_components.autopi.const import DOMAIN


async def test_setup_entry(hass: HomeAssistant) -> None:
    """Test setting up the integration."""
    # Create a mock config entry
    mock_entry = MagicMock()
    mock_entry.entry_id = "test_entry_id"
    mock_entry.domain = DOMAIN
    mock_entry.title = "AutoPi"
    mock_entry.data = {
        "api_key": "test_api_key",
        "base_url": "https://api.autopi.io",
        "selected_vehicles": ["123"],
        "scan_interval": 5,
    }
    mock_entry.options = {}
    mock_entry.add_update_listener = MagicMock(return_value=lambda: None)
    mock_entry.async_on_unload = MagicMock()

    # Mock the coordinator and its methods
    with patch(
        "custom_components.autopi.AutoPiDataUpdateCoordinator"
    ) as mock_coordinator_class, patch(
        "custom_components.autopi.AutoPiPositionCoordinator"
    ) as mock_position_coordinator_class, patch(
        "custom_components.autopi.AutoPiTripCoordinator"
    ) as mock_trip_coordinator_class, patch(
        "custom_components.autopi.get_auto_zero_manager"
    ) as mock_auto_zero_manager:
        mock_coordinator = AsyncMock()
        mock_coordinator.async_config_entry_first_refresh = AsyncMock()
        mock_coordinator.get_vehicle_count = MagicMock(return_value=1)
        mock_coordinator.data = {}  # Add empty data to prevent the RuntimeWarning
        mock_coordinator_class.return_value = mock_coordinator

        mock_position_coordinator = AsyncMock()
        mock_position_coordinator.async_config_entry_first_refresh = AsyncMock()
        mock_position_coordinator_class.return_value = mock_position_coordinator

        mock_trip_coordinator = AsyncMock()
        mock_trip_coordinator.async_config_entry_first_refresh = AsyncMock()
        mock_trip_coordinator_class.return_value = mock_trip_coordinator

        mock_auto_zero = AsyncMock()
        mock_auto_zero.async_initialize = AsyncMock()
        mock_auto_zero_manager.return_value = mock_auto_zero

        # Mock platform setup
        with patch(
            "homeassistant.config_entries.ConfigEntries.async_forward_entry_setups",
            return_value=None
        ):
            # Test the setup
            from custom_components.autopi import async_setup_entry

            result = await async_setup_entry(hass, mock_entry)
            assert result is True

            # Verify the coordinator was created and stored
            assert mock_entry.entry_id in hass.data[DOMAIN]
            data = hass.data[DOMAIN][mock_entry.entry_id]
            assert "coordinator" in data
            assert "position_coordinator" in data
            assert "coordinators" in data
            assert data["coordinator"] == mock_coordinator
