"""Config flow for AutoPi integration."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_API_KEY,
    CONF_BASE_URL,
    CONF_SCAN_INTERVAL,
    CONF_SELECTED_VEHICLES,
    CONF_UPDATE_INTERVAL_FAST,
    CONF_UPDATE_INTERVAL_MEDIUM,
    CONF_UPDATE_INTERVAL_SLOW,
    DEFAULT_BASE_URL,
    DEFAULT_NAME,
    DEFAULT_SCAN_INTERVAL_MINUTES,
    DEFAULT_UPDATE_INTERVAL_FAST_MINUTES,
    DEFAULT_UPDATE_INTERVAL_MEDIUM_MINUTES,
    DEFAULT_UPDATE_INTERVAL_SLOW_MINUTES,
    DOMAIN,
    MAX_SCAN_INTERVAL_MINUTES,
    MIN_SCAN_INTERVAL_MINUTES,
    USER_AGENT,
    VEHICLE_PROFILE_ENDPOINT,
)
from .exceptions import (
    AutoPiAPIError,
    AutoPiAuthenticationError,
    AutoPiConnectionError,
)
from .types import AutoPiVehicle

_LOGGER = logging.getLogger(__name__)

# Configure third-party logging for config flow
loggers_to_configure = [
    "aiohttp",
]

for logger_name in loggers_to_configure:
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.ERROR)
    logger.propagate = False


class AutoPiConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for AutoPi."""

    VERSION = 1
    MINOR_VERSION = 0

    def __init__(self) -> None:
        """Initialize the config flow."""
        super().__init__()
        self._api_key: str | None = None
        self._base_url: str = DEFAULT_BASE_URL
        self._vehicles: list[AutoPiVehicle] = []

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> OptionsFlow:
        """Get the options flow for this handler."""
        return AutoPiOptionsFlow()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._api_key = user_input[CONF_API_KEY]
            self._base_url = user_input.get(CONF_BASE_URL, DEFAULT_BASE_URL)

            _LOGGER.debug("Testing API connection with provided credentials")

            try:
                # Test the API connection and get vehicles
                vehicles = await self._test_api_connection()

                if not vehicles:
                    _LOGGER.warning("No vehicles found in AutoPi account")
                    return self.async_abort(reason="no_vehicles")

                self._vehicles = vehicles

                # If we have vehicles, proceed to vehicle selection
                return await self.async_step_select_vehicles()

            except AutoPiAuthenticationError:
                _LOGGER.warning("Authentication failed with provided API key")
                errors["base"] = "invalid_auth"
            except AutoPiConnectionError:
                _LOGGER.warning("Failed to connect to AutoPi API")
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected error during API connection test")
                errors["base"] = "unknown"

        # Show the form
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_API_KEY): str,
                    vol.Optional(CONF_BASE_URL, default=DEFAULT_BASE_URL): str,
                }
            ),
            errors=errors,
        )

    async def async_step_select_vehicles(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle vehicle selection step."""
        if user_input is not None:
            # Create the config entry
            selected_vehicles = user_input.get(CONF_SELECTED_VEHICLES, [])

            _LOGGER.info(
                "Creating AutoPi config entry with %d selected vehicles",
                len(selected_vehicles),
            )

            return self.async_create_entry(
                title=DEFAULT_NAME,
                data={
                    CONF_API_KEY: self._api_key,
                    CONF_BASE_URL: self._base_url,
                    CONF_SELECTED_VEHICLES: selected_vehicles,
                    CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL_MINUTES,
                },
            )

        # Prepare vehicle options
        vehicle_options = {
            str(vehicle.id): f"{vehicle.name} ({vehicle.license_plate})"
            if vehicle.license_plate
            else vehicle.name
            for vehicle in self._vehicles
        }

        # Show vehicle selection form
        return self.async_show_form(
            step_id="select_vehicles",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SELECTED_VEHICLES,
                        default=list(vehicle_options.keys()),
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                selector.SelectOptionDict(value=k, label=v)
                                for k, v in vehicle_options.items()
                            ],
                            multiple=True,
                            mode=selector.SelectSelectorMode.LIST,
                        )
                    ),
                }
            ),
        )

    async def _test_api_connection(self) -> list[AutoPiVehicle]:
        """Test the API connection and return available vehicles.

        Returns:
            List of available vehicles

        Raises:
            AutoPiAuthenticationError: If authentication fails
            AutoPiConnectionError: If connection fails
            AutoPiAPIError: If API returns an error
        """
        session = async_get_clientsession(self.hass)

        headers = {
            "Authorization": f"APIToken {self._api_key}",
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        }

        url = f"{self._base_url}{VEHICLE_PROFILE_ENDPOINT}"

        _LOGGER.debug("Testing API connection to %s", url)

        try:
            async with session.get(
                url,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as response:
                if response.status == 401:
                    raise AutoPiAuthenticationError("Invalid API key")

                if response.status != 200:
                    text = await response.text()
                    _LOGGER.error("API returned status %d: %s", response.status, text)
                    raise AutoPiAPIError(
                        f"API returned status {response.status}",
                        status_code=response.status,
                    )

                data = await response.json()

                _LOGGER.debug(
                    "Successfully connected to API, found %d vehicles",
                    data.get("count", 0),
                )

                # Convert API data to AutoPiVehicle objects
                vehicles = [
                    AutoPiVehicle.from_api_data(vehicle_data)
                    for vehicle_data in data.get("results", [])
                ]

                return vehicles

        except aiohttp.ClientError as err:
            _LOGGER.error("Connection error: %s", err)
            raise AutoPiConnectionError(
                f"Failed to connect to AutoPi API: {err}"
            ) from err
        except Exception as err:
            _LOGGER.error("Unexpected error during API test: %s", err)
            raise

    async def async_step_reauth(self, user_input=None):
        """Handle reauthentication flow."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle reauthentication confirmation step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Update the API key
            self._api_key = user_input[CONF_API_KEY]

            # Get the existing config entry
            existing_entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
            if existing_entry:
                self._base_url = existing_entry.data.get(CONF_BASE_URL, DEFAULT_BASE_URL)

                try:
                    # Test the new API key
                    vehicles = await self._test_api_connection()

                    if vehicles:
                        # Update the config entry with the new API key
                        self.hass.config_entries.async_update_entry(
                            existing_entry,
                            data={
                                **existing_entry.data,
                                CONF_API_KEY: self._api_key,
                            },
                        )

                        await self.hass.config_entries.async_reload(existing_entry.entry_id)

                        return self.async_abort(reason="reauth_successful")
                    else:
                        errors["base"] = "no_vehicles"

                except AutoPiAuthenticationError:
                    _LOGGER.warning("Reauthentication failed with provided API key")
                    errors["base"] = "invalid_auth"
                except AutoPiConnectionError:
                    _LOGGER.warning("Failed to connect to AutoPi API during reauth")
                    errors["base"] = "cannot_connect"
                except Exception:  # pylint: disable=broad-except
                    _LOGGER.exception("Unexpected error during reauthentication")
                    errors["base"] = "unknown"

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_API_KEY): str,
                }
            ),
            errors=errors,
        )


class AutoPiOptionsFlow(OptionsFlow):
    """Handle options flow for AutoPi."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            # Check if user wants to update API key
            if user_input.get("update_api_key"):
                return await self.async_step_api_key()

            # Otherwise save the update intervals
            _LOGGER.debug("Updating options with: %s", user_input)

            # Remove the update_api_key from the data before saving
            options_data = {k: v for k, v in user_input.items() if k != "update_api_key"}

            return self.async_create_entry(title="", data=options_data)

        # Get current intervals from options or defaults
        current_fast = self.config_entry.options.get(
            CONF_UPDATE_INTERVAL_FAST, DEFAULT_UPDATE_INTERVAL_FAST_MINUTES
        )
        current_medium = self.config_entry.options.get(
            CONF_UPDATE_INTERVAL_MEDIUM, DEFAULT_UPDATE_INTERVAL_MEDIUM_MINUTES
        )
        current_slow = self.config_entry.options.get(
            CONF_UPDATE_INTERVAL_SLOW, DEFAULT_UPDATE_INTERVAL_SLOW_MINUTES
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_UPDATE_INTERVAL_FAST,
                        default=current_fast,
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=MIN_SCAN_INTERVAL_MINUTES,
                            max=MAX_SCAN_INTERVAL_MINUTES,
                            unit_of_measurement="minutes",
                            mode=selector.NumberSelectorMode.BOX,
                        )
                    ),
                    vol.Required(
                        CONF_UPDATE_INTERVAL_MEDIUM,
                        default=current_medium,
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=MIN_SCAN_INTERVAL_MINUTES,
                            max=MAX_SCAN_INTERVAL_MINUTES,
                            unit_of_measurement="minutes",
                            mode=selector.NumberSelectorMode.BOX,
                        )
                    ),
                    vol.Required(
                        CONF_UPDATE_INTERVAL_SLOW,
                        default=current_slow,
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=MIN_SCAN_INTERVAL_MINUTES,
                            max=MAX_SCAN_INTERVAL_MINUTES,
                            unit_of_measurement="minutes",
                            mode=selector.NumberSelectorMode.BOX,
                        )
                    ),
                    vol.Optional("update_api_key", default=False): bool,
                }
            ),
            description_placeholders={
                "fast_desc": "Vehicle position updates",
                "medium_desc": "Vehicle status updates",
                "slow_desc": "Reserved for future use",
            },
        )

    async def async_step_api_key(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle API key update step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Test the new API key
            api_key = user_input[CONF_API_KEY]
            base_url = self.config_entry.data.get(CONF_BASE_URL, DEFAULT_BASE_URL)

            session = async_get_clientsession(self.hass)
            headers = {
                "Authorization": f"APIToken {api_key}",
                "User-Agent": USER_AGENT,
                "Accept": "application/json",
            }

            url = f"{base_url}{VEHICLE_PROFILE_ENDPOINT}"

            try:
                async with session.get(
                    url,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    if response.status == 401:
                        errors["base"] = "invalid_auth"
                    elif response.status == 200:
                        # Valid API key - update the config entry
                        self.hass.config_entries.async_update_entry(
                            self.config_entry,
                            data={
                                **self.config_entry.data,
                                CONF_API_KEY: api_key,
                            },
                        )

                        # Reload the integration
                        await self.hass.config_entries.async_reload(self.config_entry.entry_id)

                        return self.async_abort(reason="api_key_updated")
                    else:
                        errors["base"] = "cannot_connect"

            except aiohttp.ClientError:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected error during API key validation")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="api_key",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_API_KEY): str,
                }
            ),
            errors=errors,
        )
