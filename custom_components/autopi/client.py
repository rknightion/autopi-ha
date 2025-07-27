"""AutoPi API client."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Final

from aiohttp import ClientError, ClientSession, ClientTimeout

from .const import (
    DEFAULT_BASE_URL,
    USER_AGENT,
    VEHICLE_PROFILE_ENDPOINT,
)
from .exceptions import (
    AutoPiAPIError,
    AutoPiAuthenticationError,
    AutoPiConnectionError,
    AutoPiRateLimitError,
    AutoPiTimeoutError,
)
from .types import AutoPiVehicle

_LOGGER = logging.getLogger(__name__)

DEFAULT_TIMEOUT: Final = 30
MAX_RETRIES: Final = 3
RETRY_DELAY: Final = 1  # seconds


class AutoPiClient:
    """Client to interact with AutoPi API."""

    def __init__(
        self,
        session: ClientSession,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
    ) -> None:
        """Initialize the AutoPi client.

        Args:
            session: aiohttp client session
            api_key: AutoPi API key
            base_url: Base URL for AutoPi API
        """
        self._session = session
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._headers = {
            "Authorization": f"Bearer {api_key}",
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        _LOGGER.debug("AutoPi client initialized with base URL: %s", self._base_url)

    async def get_vehicles(self) -> list[AutoPiVehicle]:
        """Get all vehicles from the AutoPi API.

        Returns:
            List of AutoPiVehicle objects

        Raises:
            AutoPiAuthenticationError: If authentication fails
            AutoPiConnectionError: If connection fails
            AutoPiAPIError: If API returns an error
        """
        _LOGGER.debug("Fetching vehicles from AutoPi API")

        try:
            data = await self._request(
                "GET",
                VEHICLE_PROFILE_ENDPOINT,
            )

            # Type-safe access to response data
            vehicle_count = data.get("count", 0)
            results = data.get("results", [])

            _LOGGER.info(
                "Successfully fetched %d vehicles from AutoPi API",
                vehicle_count,
            )

            # Convert API data to AutoPiVehicle objects
            vehicles = [
                AutoPiVehicle.from_api_data(vehicle_data) for vehicle_data in results
            ]

            return vehicles

        except Exception as err:
            _LOGGER.error("Failed to fetch vehicles: %s", err)
            raise

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        retry_count: int = 0,
    ) -> dict[str, Any]:
        """Make a request to the AutoPi API.

        Args:
            method: HTTP method
            endpoint: API endpoint
            data: Request data
            params: Query parameters
            retry_count: Current retry count

        Returns:
            Response data

        Raises:
            AutoPiAuthenticationError: If authentication fails
            AutoPiConnectionError: If connection fails
            AutoPiAPIError: If API returns an error
        """
        url = f"{self._base_url}{endpoint}"

        _LOGGER.debug(
            "Making %s request to %s (retry %d/%d)",
            method,
            url,
            retry_count,
            MAX_RETRIES,
        )

        try:
            async with self._session.request(
                method,
                url,
                headers=self._headers,
                json=data,
                params=params,
                timeout=ClientTimeout(total=DEFAULT_TIMEOUT),
            ) as response:
                response_text = await response.text()

                _LOGGER.debug(
                    "Received response with status %d for %s %s",
                    response.status,
                    method,
                    url,
                )

                if response.status == 401:
                    _LOGGER.error("Authentication failed: Invalid API key")
                    raise AutoPiAuthenticationError("Invalid API key")

                if response.status == 429:
                    _LOGGER.warning("Rate limit exceeded")
                    raise AutoPiRateLimitError(
                        "Rate limit exceeded", status_code=response.status
                    )

                if response.status >= 500:
                    _LOGGER.error("Server error %d: %s", response.status, response_text)

                    # Retry on server errors
                    if retry_count < MAX_RETRIES:
                        _LOGGER.info(
                            "Retrying request after server error (attempt %d/%d)",
                            retry_count + 1,
                            MAX_RETRIES,
                        )
                        await asyncio.sleep(RETRY_DELAY * (retry_count + 1))
                        return await self._request(
                            method, endpoint, data, params, retry_count + 1
                        )

                    raise AutoPiAPIError(
                        f"Server error: {response.status}",
                        status_code=response.status,
                        data={"response": response_text},
                    )

                if response.status >= 400:
                    _LOGGER.error("Client error %d: %s", response.status, response_text)
                    raise AutoPiAPIError(
                        f"Client error: {response.status}",
                        status_code=response.status,
                        data={"response": response_text},
                    )

                if response.status == 204:
                    # No content
                    return {}

                try:
                    return await response.json()
                except Exception as err:
                    _LOGGER.error("Failed to parse JSON response: %s", response_text)
                    raise AutoPiAPIError(
                        "Invalid JSON response from API",
                        data={"response": response_text},
                    ) from err

        except TimeoutError as err:
            _LOGGER.error("Request timeout for %s %s", method, url)
            raise AutoPiTimeoutError(f"Request timeout for {method} {url}") from err

        except ClientError as err:
            _LOGGER.error("Connection error for %s %s: %s", method, url, err)

            # Retry on connection errors
            if retry_count < MAX_RETRIES:
                _LOGGER.info(
                    "Retrying request after connection error (attempt %d/%d)",
                    retry_count + 1,
                    MAX_RETRIES,
                )
                await asyncio.sleep(RETRY_DELAY * (retry_count + 1))
                return await self._request(
                    method, endpoint, data, params, retry_count + 1
                )

            raise AutoPiConnectionError(
                f"Failed to connect to AutoPi API: {err}"
            ) from err

        except Exception as err:
            _LOGGER.error("Unexpected error during %s %s: %s", method, url, err)
            raise AutoPiAPIError(f"Unexpected error: {err}") from err
