"""Config flow for AutoPi integration."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_API_KEY,
    CONF_BASE_URL,
    CONF_SCAN_INTERVAL,
    CONF_SELECTED_VEHICLES,
    DEFAULT_BASE_URL,
    DEFAULT_NAME,
    DEFAULT_SCAN_INTERVAL_MINUTES,
    DOMAIN,
    MIN_SCAN_INTERVAL_MINUTES,
    MAX_SCAN_INTERVAL_MINUTES,
    USER_AGENT,
    VEHICLE_PROFILE_ENDPOINT,
)
from .exceptions import (
    AutoPiAuthenticationError,
    AutoPiConnectionError,
    AutoPiAPIError,
)
from .types import VehicleProfileResponse, AutoPiVehicle

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
        return AutoPiOptionsFlow(config_entry)

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
                len(selected_vehicles)
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
                            options=list(vehicle_options.items()),
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
            "Authorization": f"Bearer {self._api_key}",
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
                    _LOGGER.error(
                        "API returned status %d: %s",
                        response.status,
                        text
                    )
                    raise AutoPiAPIError(
                        f"API returned status {response.status}",
                        status_code=response.status
                    )

                data: VehicleProfileResponse = await response.json()
                
                _LOGGER.debug(
                    "Successfully connected to API, found %d vehicles",
                    data.get("count", 0)
                )

                # Convert API data to AutoPiVehicle objects
                vehicles = [
                    AutoPiVehicle.from_api_data(vehicle_data)
                    for vehicle_data in data.get("results", [])
                ]

                return vehicles

        except aiohttp.ClientError as err:
            _LOGGER.error("Connection error: %s", err)
            raise AutoPiConnectionError(f"Failed to connect to AutoPi API: {err}") from err
        except Exception as err:
            _LOGGER.error("Unexpected error during API test: %s", err)
            raise


class AutoPiOptionsFlow(OptionsFlow):
    """Handle options flow for AutoPi."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            _LOGGER.debug("Updating options with: %s", user_input)
            return self.async_create_entry(title="", data=user_input)

        current_interval = self.config_entry.data.get(
            CONF_SCAN_INTERVAL,
            DEFAULT_SCAN_INTERVAL_MINUTES
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_SCAN_INTERVAL,
                        default=current_interval,
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=MIN_SCAN_INTERVAL_MINUTES,
                            max=MAX_SCAN_INTERVAL_MINUTES,
                            unit_of_measurement="minutes",
                            mode=selector.NumberSelectorMode.BOX,
                        )
                    ),
                }
            ),
        ) 