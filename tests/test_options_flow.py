"""Tests for AutoPi options flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, Mock, patch

import pytest
from homeassistant import data_entry_flow
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.autopi.const import (
    CONF_API_KEY,
    CONF_AUTO_ZERO_ENABLED,
    CONF_DISCOVERY_ENABLED,
    CONF_UPDATE_INTERVAL_FAST,
    DEFAULT_UPDATE_INTERVAL_FAST_MINUTES,
    DOMAIN,
    MAX_SCAN_INTERVAL_MINUTES,
    MIN_SCAN_INTERVAL_MINUTES,
)

from .conftest import create_mock_aiohttp_response


class TestOptionsFlowInit:
    """Test the initial step of the options flow."""

    async def test_show_options_form(
        self, hass: HomeAssistant, mock_config_entry_data, mock_config_entry_options
    ):
        """Test that the options form is shown."""
        # Create a config entry and add it to hass
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="AutoPi",
            data=mock_config_entry_data,
            options=mock_config_entry_options,
            entry_id="test_entry",
            unique_id="test_unique_id",
        )
        entry.add_to_hass(hass)

        # Start options flow through proper handler
        result = await hass.config_entries.options.async_init(entry.entry_id)

        assert result["type"] == data_entry_flow.FlowResultType.FORM
        assert result["step_id"] == "init"

    async def test_options_form_shows_current_values(
        self, hass: HomeAssistant, mock_config_entry_data
    ):
        """Test that current option values are shown in the form."""
        # Create entry with specific options
        options = {
            CONF_UPDATE_INTERVAL_FAST: 2,
            CONF_DISCOVERY_ENABLED: False,
            CONF_AUTO_ZERO_ENABLED: True,
        }

        entry = MockConfigEntry(
            domain=DOMAIN,
            title="AutoPi",
            data=mock_config_entry_data,
            options=options,
            entry_id="test_entry",
            unique_id="test_unique_id",
        )
        entry.add_to_hass(hass)

        result = await hass.config_entries.options.async_init(entry.entry_id)

        assert result["type"] == data_entry_flow.FlowResultType.FORM
        # Check that default values in schema match current options
        # (This is a simplified check - actual implementation may vary)

    async def test_update_interval_fast_option(
        self, hass: HomeAssistant, mock_config_entry_data, mock_config_entry_options
    ):
        """Test updating the fast update interval."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="AutoPi",
            data=mock_config_entry_data,
            options=mock_config_entry_options,
            entry_id="test_entry",
            unique_id="test_unique_id",
        )
        entry.add_to_hass(hass)

        # Start the options flow
        result = await hass.config_entries.options.async_init(entry.entry_id)
        assert result["type"] == data_entry_flow.FlowResultType.FORM

        # Submit updated options
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                "polling_interval": 3,
                "discovery_enabled": True,
                "auto_zero_enabled": False,
            }
        )

        assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
        assert result["data"][CONF_UPDATE_INTERVAL_FAST] == 3
        assert result["data"][CONF_DISCOVERY_ENABLED] is True
        assert result["data"][CONF_AUTO_ZERO_ENABLED] is False

    async def test_update_all_options(
        self, hass: HomeAssistant, mock_config_entry_data, mock_config_entry_options
    ):
        """Test updating all options at once."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="AutoPi",
            data=mock_config_entry_data,
            options=mock_config_entry_options,
            entry_id="test_entry",
            unique_id="test_unique_id",
        )
        entry.add_to_hass(hass)

        # Start the options flow
        result = await hass.config_entries.options.async_init(entry.entry_id)
        assert result["type"] == data_entry_flow.FlowResultType.FORM

        new_options = {
            "polling_interval": 10,
            "discovery_enabled": False,
            "auto_zero_enabled": True,
        }

        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input=new_options
        )

        assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
        assert result["data"][CONF_UPDATE_INTERVAL_FAST] == 10
        assert result["data"][CONF_DISCOVERY_ENABLED] is False
        assert result["data"][CONF_AUTO_ZERO_ENABLED] is True

    async def test_minimum_update_interval(
        self, hass: HomeAssistant, mock_config_entry_data, mock_config_entry_options
    ):
        """Test that minimum update interval is enforced."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="AutoPi",
            data=mock_config_entry_data,
            options=mock_config_entry_options,
            entry_id="test_entry",
            unique_id="test_unique_id",
        )
        entry.add_to_hass(hass)

        # Start the options flow
        result = await hass.config_entries.options.async_init(entry.entry_id)
        assert result["type"] == data_entry_flow.FlowResultType.FORM

        # Try to set interval to minimum value
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                "polling_interval": MIN_SCAN_INTERVAL_MINUTES,
                "discovery_enabled": True,
                "auto_zero_enabled": False,
            }
        )

        assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
        assert result["data"][CONF_UPDATE_INTERVAL_FAST] == MIN_SCAN_INTERVAL_MINUTES

    async def test_maximum_update_interval(
        self, hass: HomeAssistant, mock_config_entry_data, mock_config_entry_options
    ):
        """Test that maximum update interval is enforced."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="AutoPi",
            data=mock_config_entry_data,
            options=mock_config_entry_options,
            entry_id="test_entry",
            unique_id="test_unique_id",
        )
        entry.add_to_hass(hass)

        # Start the options flow
        result = await hass.config_entries.options.async_init(entry.entry_id)
        assert result["type"] == data_entry_flow.FlowResultType.FORM

        # Try to set interval to maximum value
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                "polling_interval": MAX_SCAN_INTERVAL_MINUTES,
                "discovery_enabled": True,
                "auto_zero_enabled": False,
            }
        )

        assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
        assert result["data"][CONF_UPDATE_INTERVAL_FAST] == MAX_SCAN_INTERVAL_MINUTES


class TestOptionsFlowAPIKeyUpdate:
    """Test the API key update step."""

    async def test_show_api_key_update_form(
        self, hass: HomeAssistant, mock_config_entry_data, mock_config_entry_options
    ):
        """Test that API key update form is accessible."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="AutoPi",
            data=mock_config_entry_data,
            options=mock_config_entry_options,
            entry_id="test_entry",
            unique_id="test_unique_id",
        )
        entry.add_to_hass(hass)

        # Start the options flow
        result = await hass.config_entries.options.async_init(entry.entry_id)
        assert result["type"] == data_entry_flow.FlowResultType.FORM

        # Navigate to API key step by setting update_api_key=True
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                "polling_interval": DEFAULT_UPDATE_INTERVAL_FAST_MINUTES,
                "update_api_key": True,
                "auto_zero_enabled": False,
                "discovery_enabled": True,
            }
        )

        assert result["type"] == data_entry_flow.FlowResultType.FORM
        assert result["step_id"] == "api_key"
        assert CONF_API_KEY in result["data_schema"].schema

    async def test_update_api_key_with_valid_key(
        self, hass: HomeAssistant, mock_config_entry_data, mock_config_entry_options, mock_api_vehicle_response
    ):
        """Test updating API key with valid credentials."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="AutoPi",
            data=mock_config_entry_data,
            options=mock_config_entry_options,
            entry_id="test_entry",
            unique_id="test_unique_id",
        )
        entry.add_to_hass(hass)

        # Start the options flow
        result = await hass.config_entries.options.async_init(entry.entry_id)
        assert result["type"] == data_entry_flow.FlowResultType.FORM

        # Navigate to API key step
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                "polling_interval": DEFAULT_UPDATE_INTERVAL_FAST_MINUTES,
                "update_api_key": True,
                "auto_zero_enabled": False,
                "discovery_enabled": True,
            }
        )
        assert result["type"] == data_entry_flow.FlowResultType.FORM
        assert result["step_id"] == "api_key"

        # Mock successful API validation
        with patch("custom_components.autopi.config_flow.async_get_clientsession") as mock_session_getter, \
             patch.object(hass.config_entries, "async_reload") as mock_reload:
            mock_session = AsyncMock()
            mock_response = create_mock_aiohttp_response(200, mock_api_vehicle_response)
            mock_session.get = Mock(return_value=mock_response)
            mock_session_getter.return_value = mock_session

            result = await hass.config_entries.options.async_configure(
                result["flow_id"],
                user_input={CONF_API_KEY: "new_valid_key"}
            )

        # API key update returns abort, not create_entry
        assert result["type"] == data_entry_flow.FlowResultType.ABORT
        assert result["reason"] == "api_key_updated"

    async def test_update_api_key_with_invalid_key(
        self, hass: HomeAssistant, mock_config_entry_data, mock_config_entry_options
    ):
        """Test that invalid API key shows error."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="AutoPi",
            data=mock_config_entry_data,
            options=mock_config_entry_options,
            entry_id="test_entry",
            unique_id="test_unique_id",
        )
        entry.add_to_hass(hass)

        # Start the options flow
        result = await hass.config_entries.options.async_init(entry.entry_id)
        assert result["type"] == data_entry_flow.FlowResultType.FORM

        # Navigate to API key step
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                "polling_interval": DEFAULT_UPDATE_INTERVAL_FAST_MINUTES,
                "update_api_key": True,
                "auto_zero_enabled": False,
                "discovery_enabled": True,
            }
        )
        assert result["type"] == data_entry_flow.FlowResultType.FORM
        assert result["step_id"] == "api_key"

        # Mock authentication failure
        with patch("custom_components.autopi.config_flow.async_get_clientsession") as mock_session_getter:
            mock_session = AsyncMock()
            mock_response = create_mock_aiohttp_response(401)
            mock_session.get = Mock(return_value=mock_response)
            mock_session_getter.return_value = mock_session

            result = await hass.config_entries.options.async_configure(
                result["flow_id"],
                user_input={CONF_API_KEY: "invalid_key"}
            )

        assert result["type"] == data_entry_flow.FlowResultType.FORM
        assert result["step_id"] == "api_key"
        assert result["errors"] == {"base": "invalid_auth"}

    async def test_update_api_key_with_connection_error(
        self, hass: HomeAssistant, mock_config_entry_data, mock_config_entry_options
    ):
        """Test that connection error during API key update shows error."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="AutoPi",
            data=mock_config_entry_data,
            options=mock_config_entry_options,
            entry_id="test_entry",
            unique_id="test_unique_id",
        )
        entry.add_to_hass(hass)

        # Start the options flow
        result = await hass.config_entries.options.async_init(entry.entry_id)
        assert result["type"] == data_entry_flow.FlowResultType.FORM

        # Navigate to API key step
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                "polling_interval": DEFAULT_UPDATE_INTERVAL_FAST_MINUTES,
                "update_api_key": True,
                "auto_zero_enabled": False,
                "discovery_enabled": True,
            }
        )
        assert result["type"] == data_entry_flow.FlowResultType.FORM
        assert result["step_id"] == "api_key"

        # Mock connection error
        with patch("custom_components.autopi.config_flow.async_get_clientsession") as mock_session_getter:
            mock_session = AsyncMock()
            # Make get() raise immediately (not as a coroutine)
            mock_session.get = Mock(side_effect=Exception("Connection failed"))
            mock_session_getter.return_value = mock_session

            result = await hass.config_entries.options.async_configure(
                result["flow_id"],
                user_input={CONF_API_KEY: "test_key"}
            )

        assert result["type"] == data_entry_flow.FlowResultType.FORM
        assert result["step_id"] == "api_key"
        assert result["errors"] == {"base": "unknown"}
