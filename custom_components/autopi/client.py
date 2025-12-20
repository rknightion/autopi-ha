"""AutoPi API client."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Final, cast

from aiohttp import ClientError, ClientSession, ClientTimeout

from .const import (
    ALERTS_ENDPOINT,
    CHARGING_SESSIONS_ENDPOINT,
    DATA_FIELDS_ENDPOINT,
    DEFAULT_BASE_URL,
    DIAGNOSTICS_ENDPOINT,
    EVENTS_ENDPOINT,
    EVENTS_HISTOGRAM_ENDPOINT,
    FLEET_ALERTS_ENDPOINT,
    FLEET_ALERTS_SUMMARY_ENDPOINT,
    FLEET_VEHICLE_SUMMARY_ENDPOINT,
    GEOFENCE_SUMMARY_ENDPOINT_TEMPLATE,
    MOST_RECENT_POSITIONS_ENDPOINT,
    OBD_DTCS_ENDPOINT,
    RECENT_STATS_ENDPOINT,
    RFID_EVENTS_ENDPOINT,
    SIMPLIFIED_EVENTS_ENDPOINT,
    TRIPS_ENDPOINT,
    USER_AGENT,
    VEHICLE_PROFILE_ENDPOINT,
)
from .exceptions import (
    AutoPiAPIError,
    AutoPiAuthenticationError,
    AutoPiConnectionError,
    AutoPiError,
    AutoPiRateLimitError,
    AutoPiTimeoutError,
)
from .types import (
    AlertsData,
    AutoPiEvent,
    AutoPiTrip,
    AutoPiVehicle,
    ChargingSession,
    DataFieldResponse,
    DataFieldValue,
    DeviceMostRecentPosition,
    DtcEntry,
    EventsResponse,
    FleetAlert,
    FleetAlertSummary,
    FleetVehicleSummary,
    RecentStatEvent,
    RfidEvent,
    SimplifiedEvent,
    TripsResponse,
)

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
            "Authorization": f"APIToken {api_key}",
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

            _LOGGER.debug(
                "Successfully fetched %d vehicles from AutoPi API",
                vehicle_count,
            )

            # Convert API data to AutoPiVehicle objects
            vehicles = [
                AutoPiVehicle.from_api_data(vehicle_data) for vehicle_data in results
            ]

            return vehicles

        except Exception:
            _LOGGER.exception("Failed to fetch vehicles")
            raise

    async def get_data_fields(
        self, device_id: str, vehicle_id: int
    ) -> dict[str, DataFieldValue]:
        """Get all available data fields for a specific device and vehicle.

        Args:
            device_id: The device ID
            vehicle_id: The vehicle ID

        Returns:
            Dictionary mapping field IDs to DataFieldValue objects

        Raises:
            AutoPiAuthenticationError: If authentication fails
            AutoPiConnectionError: If connection fails
            AutoPiAPIError: If API returns an error
        """
        _LOGGER.debug(
            "Fetching data fields for device %s, vehicle %d", device_id, vehicle_id
        )

        try:
            response = await self._request(
                "GET",
                DATA_FIELDS_ENDPOINT,
                params={"device_id": device_id, "vehicle_id": vehicle_id},
            )

            # Response should be a list
            if not isinstance(response, list):
                _LOGGER.error("Unexpected response type: %s", type(response))
                return {}

            fields: dict[str, DataFieldValue] = {}

            for field_data in response:
                try:
                    field_response = cast(DataFieldResponse, field_data)
                    field_value = DataFieldValue.from_api_data(field_response)
                    fields[field_value.field_id] = field_value

                    _LOGGER.debug(
                        "Parsed field %s: %s = %s",
                        field_value.field_id,
                        field_value.title,
                        field_value.last_value,
                    )

                except (KeyError, TypeError) as err:
                    _LOGGER.warning("Failed to parse field data: %s", err)
                    continue

            _LOGGER.debug(
                "Successfully fetched %d data fields for device %s",
                len(fields),
                device_id,
            )
            return fields

        except Exception:
            _LOGGER.exception("Failed to fetch data fields")
            raise

    async def get_trips(
        self, vehicle_id: int, device_id: str | None = None, page_size: int = 1
    ) -> tuple[int, list[AutoPiTrip]]:
        """Get trips for a specific vehicle.

        Args:
            vehicle_id: The vehicle ID
            device_id: Optional device ID to filter by
            page_size: Number of trips to return (default 1 for last trip only)

        Returns:
            Tuple of (total_trip_count, list of AutoPiTrip objects)

        Raises:
            AutoPiAuthenticationError: If authentication fails
            AutoPiConnectionError: If connection fails
            AutoPiAPIError: If API returns an error
        """
        _LOGGER.debug(
            "Fetching trips for vehicle %d with page_size %d", vehicle_id, page_size
        )

        try:
            params: dict[str, Any] = {
                "vehicle": vehicle_id,
                "page_size": page_size,
                "page": 1,
            }

            if device_id:
                params["device_id"] = device_id

            response = await self._request(
                "GET",
                TRIPS_ENDPOINT,
                params=params,
            )

            trips_response = cast(TripsResponse, response)
            count = trips_response.get("count", 0)
            results = trips_response.get("results", [])

            _LOGGER.debug(
                "Successfully fetched %d of %d trips for vehicle %d",
                len(results),
                count,
                vehicle_id,
            )

            # Convert API data to AutoPiTrip objects
            trips = []
            for trip_data in results:
                try:
                    trip = AutoPiTrip.from_api_data(trip_data)
                    trips.append(trip)
                except (KeyError, ValueError, TypeError) as err:
                    _LOGGER.warning(
                        "Failed to parse trip data: %s. Trip data: %s", err, trip_data
                    )
                    continue

            return count, trips

        except Exception:
            _LOGGER.exception("Failed to fetch trips")
            raise

    async def get_fleet_alerts(self) -> tuple[int, list[FleetAlert]]:
        """Get fleet-wide alerts summary.

        Returns:
            Tuple of (total_alert_count, list of FleetAlert objects)

        Raises:
            AutoPiAuthenticationError: If authentication fails
            AutoPiConnectionError: If connection fails
            AutoPiAPIError: If API returns an error
        """
        _LOGGER.debug("Fetching fleet alerts from AutoPi API")

        try:
            response = await self._request(
                "GET",
                ALERTS_ENDPOINT,
            )

            alerts_response = cast(AlertsData, response)
            total = alerts_response.get("total", 0)
            severities = alerts_response.get("severities", [])

            _LOGGER.debug("Successfully fetched fleet alerts: %d total alerts", total)

            # Convert API data to FleetAlert objects
            alerts = []
            for severity_data in severities:
                severity = severity_data["severity"]
                for alert_data in severity_data["alerts"]:
                    try:
                        alert = FleetAlert.from_api_data(severity, alert_data)
                        alerts.append(alert)
                    except (KeyError, ValueError) as err:
                        _LOGGER.warning("Failed to parse alert data: %s", err)
                        continue

            return total, alerts

        except Exception:
            _LOGGER.exception("Failed to fetch fleet alerts")
            raise

    async def get_device_events(
        self, device_id: str, page_hits: int = 5
    ) -> list[AutoPiEvent]:
        """Get recent events for a specific device.

        Args:
            device_id: The AutoPi device ID
            page_hits: Number of events to fetch (default: 5)

        Returns:
            List of AutoPiEvent objects

        Raises:
            AutoPiAuthenticationError: If authentication fails
            AutoPiConnectionError: If connection fails
            AutoPiAPIError: If API returns an error
        """
        _LOGGER.debug("Fetching events for device %s", device_id)

        try:
            response = await self._request(
                "GET",
                EVENTS_ENDPOINT,
                params={
                    "device_id": device_id,
                    "page_num": 1,
                    "page_hits": page_hits,
                },
            )

            events_response = cast(EventsResponse, response)
            results = events_response.get("results", [])

            _LOGGER.debug(
                "Successfully fetched %d events for device %s",
                len(results),
                device_id,
            )

            # Convert API data to AutoPiEvent objects
            events = []
            for event_data in results:
                try:
                    event = AutoPiEvent.from_api_data(event_data, device_id)
                    events.append(event)
                except (KeyError, ValueError) as err:
                    _LOGGER.warning("Failed to parse event data: %s", err)
                    continue

            return events

        except Exception:
            _LOGGER.exception("Failed to fetch events for device %s", device_id)
            raise

    async def get_recent_stats(
        self,
        device_id: str,
        from_timestamp: str,
        stat_type: str | None = None,
        kind: str | None = None,
    ) -> list[RecentStatEvent]:
        """Get recent stats for a specific device."""
        _LOGGER.debug("Fetching recent stats for device %s", device_id)

        try:
            params: dict[str, Any] = {
                "device_id": device_id,
                "from_timestamp": from_timestamp,
            }
            if stat_type:
                params["type"] = stat_type
            if kind:
                params["kind"] = kind

            response = await self._request(
                "GET",
                RECENT_STATS_ENDPOINT,
                params=params,
            )

            if not isinstance(response, list):
                _LOGGER.error(
                    "Unexpected recent stats response type: %s", type(response)
                )
                return []

            events: list[RecentStatEvent] = []
            for entry in response:
                if not isinstance(entry, dict):
                    continue
                parsed = RecentStatEvent.from_api_data(entry)
                if parsed:
                    events.append(parsed)

            events.sort(key=lambda item: item.timestamp, reverse=True)
            return events

        except Exception:
            _LOGGER.exception("Failed to fetch recent stats for device %s", device_id)
            raise

    async def get_most_recent_positions(self) -> list[DeviceMostRecentPosition]:
        """Get most recent positions for all devices."""
        _LOGGER.debug("Fetching most recent positions from AutoPi API")

        try:
            response = await self._request("GET", MOST_RECENT_POSITIONS_ENDPOINT)

            if not isinstance(response, list):
                _LOGGER.error(
                    "Unexpected most recent positions response type: %s",
                    type(response),
                )
                return []

            positions: list[DeviceMostRecentPosition] = []
            for entry in response:
                if not isinstance(entry, dict):
                    continue
                try:
                    positions.append(DeviceMostRecentPosition.from_api_data(entry))
                except (KeyError, ValueError, TypeError) as err:
                    _LOGGER.warning("Failed to parse most recent position: %s", err)
                    continue

            return positions

        except Exception:
            _LOGGER.exception("Failed to fetch most recent positions")
            raise

    async def get_charging_sessions(
        self,
        vehicle_id: int,
        start_tags: list[str],
        end_tags: list[str],
        from_utc: str,
        to_utc: str,
    ) -> list[ChargingSession]:
        """Get charging sessions for a vehicle."""
        _LOGGER.debug("Fetching charging sessions for vehicle %d", vehicle_id)

        try:
            params: dict[str, Any] = {
                "vehicle_id": vehicle_id,
                "start_tags": start_tags,
                "end_tags": end_tags,
                "from_utc": from_utc,
                "to_utc": to_utc,
            }

            response = await self._request(
                "GET",
                CHARGING_SESSIONS_ENDPOINT,
                params=params,
            )

            if not isinstance(response, list):
                _LOGGER.error(
                    "Unexpected charging sessions response type: %s", type(response)
                )
                return []

            sessions = []
            for entry in response:
                if not isinstance(entry, dict):
                    continue
                sessions.append(ChargingSession.from_api_data(entry))

            return sessions

        except Exception:
            _LOGGER.exception(
                "Failed to fetch charging sessions for vehicle %d", vehicle_id
            )
            raise

    async def get_fleet_alerts_summary(self) -> FleetAlertSummary:
        """Get fleet alerts summary."""
        _LOGGER.debug("Fetching fleet alerts summary")

        response = await self._request("GET", FLEET_ALERTS_SUMMARY_ENDPOINT)
        if not isinstance(response, dict):
            _LOGGER.error(
                "Unexpected fleet alerts summary response: %s", type(response)
            )
            return FleetAlertSummary(open=0, critical=0, high=0, medium=0, low=0)

        return FleetAlertSummary.from_api_data(response)

    async def get_vehicle_alerts(
        self, vehicle_id: int, page_size: int = 5
    ) -> dict[str, Any]:
        """Get alerts for a specific vehicle."""
        _LOGGER.debug("Fetching alerts for vehicle %d", vehicle_id)
        response = await self._request(
            "GET",
            FLEET_ALERTS_ENDPOINT,
            params={"vehicle": vehicle_id, "page_size": page_size},
        )
        if not isinstance(response, dict):
            _LOGGER.error("Unexpected vehicle alerts response: %s", type(response))
            return {"count": 0, "results": [], "page_size": page_size}
        return response

    async def get_diagnostics(
        self, device_id: str, page_hits: int = 5
    ) -> dict[str, Any]:
        """Get diagnostic events for a device."""
        _LOGGER.debug("Fetching diagnostics for device %s", device_id)
        response = await self._request(
            "GET",
            DIAGNOSTICS_ENDPOINT,
            params={"device_id": device_id, "page_hits": page_hits},
        )
        if not isinstance(response, dict):
            _LOGGER.error("Unexpected diagnostics response: %s", type(response))
            return {"count": 0, "results": []}
        return response

    async def get_obd_dtcs(self, vehicle_id: int) -> list[DtcEntry]:
        """Get OBD DTC entries for a vehicle."""
        _LOGGER.debug("Fetching OBD DTCs for vehicle %d", vehicle_id)
        response = await self._request(
            "GET",
            OBD_DTCS_ENDPOINT,
            params={"vehicle_id": vehicle_id},
        )

        entries: list[DtcEntry] = []
        if isinstance(response, dict):
            results = response.get("results", [])
        else:
            results = response if isinstance(response, list) else []

        for entry in results:
            if not isinstance(entry, dict):
                continue
            entries.append(DtcEntry.from_api_data(entry))

        return entries

    async def get_geofence_summary(self, vehicle_id: int) -> dict[str, Any]:
        """Get geofence summary for a vehicle."""
        _LOGGER.debug("Fetching geofence summary for vehicle %d", vehicle_id)
        endpoint = GEOFENCE_SUMMARY_ENDPOINT_TEMPLATE.format(vehicle_id=vehicle_id)
        response = await self._request("GET", endpoint)
        if not isinstance(response, dict):
            _LOGGER.error("Unexpected geofence summary response: %s", type(response))
            return {
                "count": 0,
                "results": [],
                "counts": {"locations": 0, "geofences": 0},
            }
        return response

    async def get_fleet_vehicle_summary(self) -> FleetVehicleSummary:
        """Get fleet vehicle activity summary."""
        _LOGGER.debug("Fetching fleet vehicle summary")
        response = await self._request("GET", FLEET_VEHICLE_SUMMARY_ENDPOINT)
        if not isinstance(response, dict):
            _LOGGER.error(
                "Unexpected fleet vehicle summary response: %s", type(response)
            )
            return FleetVehicleSummary(
                all_vehicles=0,
                active_now=0,
                driven_last_30_days=0,
                on_location=0,
            )

        def _safe_int(value: Any, default: int = 0) -> int:
            try:
                if value is None:
                    return default
                return int(value)
            except (TypeError, ValueError):
                return default

        return FleetVehicleSummary(
            all_vehicles=_safe_int(
                response.get("all", response.get("all_vehicles", 0))
            ),
            active_now=_safe_int(
                response.get("active_now", response.get("active_vehicles_now", 0))
            ),
            driven_last_30_days=_safe_int(
                response.get(
                    "driven_last_30_days",
                    response.get("driven_vehicles_last_30_days", 0),
                )
            ),
            on_location=_safe_int(response.get("on_location", 0)),
        )

    async def get_events_histogram(
        self,
        device_id: str,
        start_utc: str,
        end_utc: str,
        interval: str,
        filter_tag: str,
        event_type: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get event histogram buckets."""
        _LOGGER.debug(
            "Fetching events histogram for device %s (tag: %s)", device_id, filter_tag
        )
        params: dict[str, Any] = {
            "device_id": device_id,
            "start_utc": start_utc,
            "end_utc": end_utc,
            "interval": interval,
            "filter_tag": filter_tag,
        }
        if event_type:
            params["type"] = event_type

        response = await self._request(
            "GET",
            EVENTS_HISTOGRAM_ENDPOINT,
            params=params,
        )

        if not isinstance(response, list):
            _LOGGER.error("Unexpected events histogram response: %s", type(response))
            return []

        return [entry for entry in response if isinstance(entry, dict)]

    async def get_simplified_events(
        self,
        vehicle_id: int,
        page_hits: int = 1,
        ordering: str = "-ts",
    ) -> list[SimplifiedEvent]:
        """Get simplified events for a vehicle."""
        _LOGGER.debug("Fetching simplified events for vehicle %d", vehicle_id)
        response = await self._request(
            "GET",
            SIMPLIFIED_EVENTS_ENDPOINT,
            params={
                "vehicle_id": vehicle_id,
                "page_hits": page_hits,
                "ordering": ordering,
            },
        )

        if not isinstance(response, dict):
            _LOGGER.error("Unexpected simplified events response: %s", type(response))
            return []

        results = response.get("results", [])
        events: list[SimplifiedEvent] = []
        for entry in results:
            if not isinstance(entry, dict):
                continue
            parsed = SimplifiedEvent.from_api_data(entry)
            if parsed:
                events.append(parsed)

        events.sort(key=lambda event: event.timestamp, reverse=True)
        return events

    async def get_rfid_events(
        self,
        start_time: str,
        end_time: str,
    ) -> list[RfidEvent]:
        """Get RFID events."""
        _LOGGER.debug("Fetching RFID events")
        response = await self._request(
            "GET",
            RFID_EVENTS_ENDPOINT,
            params={"start_time": start_time, "end_time": end_time},
        )

        results: list[dict[str, Any]] = []
        if isinstance(response, dict):
            results = response.get("rfid_events", []) or response.get("results", [])
        elif isinstance(response, list):
            results = response

        events: list[RfidEvent] = []
        for entry in results:
            if not isinstance(entry, dict):
                continue
            parsed = RfidEvent.from_api_data(entry)
            if parsed:
                events.append(parsed)

        events.sort(key=lambda event: event.timestamp, reverse=True)
        return events

    async def get_trips_page(
        self,
        vehicle_id: int,
        device_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> TripsResponse:
        """Get a page of trips using limit/offset pagination."""
        _LOGGER.debug(
            "Fetching trips page for vehicle %d (limit=%d, offset=%d)",
            vehicle_id,
            limit,
            offset,
        )
        params: dict[str, Any] = {
            "vehicle": vehicle_id,
            "limit": limit,
            "offset": offset,
        }
        if device_id:
            params["device_id"] = device_id

        response = await self._request(
            "GET",
            TRIPS_ENDPOINT,
            params=params,
        )
        return cast(TripsResponse, response)

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
            endpoint,  # Log endpoint without base URL to avoid exposing full URLs
            retry_count,
            MAX_RETRIES,
        )

        if params:
            # Log params but filter out any sensitive data
            safe_params = {
                k: v for k, v in params.items() if k not in ["api_key", "token"]
            }
            _LOGGER.debug("Request params: %s", safe_params)

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
                        _LOGGER.debug(
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
                    if response.status == 404:
                        _LOGGER.debug(
                            "Resource not found (%s): %s", endpoint, response_text
                        )
                    else:
                        _LOGGER.error(
                            "Client error %d: %s", response.status, response_text
                        )
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
                    _LOGGER.exception(
                        "Failed to parse JSON response: %s", response_text
                    )
                    raise AutoPiAPIError(
                        "Invalid JSON response from API",
                        data={"response": response_text},
                    ) from err

        except AutoPiError:
            # Re-raise our custom exceptions without modification
            raise

        except TimeoutError as err:
            _LOGGER.exception("Request timeout for %s %s", method, url)
            raise AutoPiTimeoutError(f"Request timeout for {method} {url}") from err

        except ClientError as err:
            _LOGGER.exception("Connection error for %s %s", method, url)

            # Retry on connection errors
            if retry_count < MAX_RETRIES:
                _LOGGER.debug(
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
            _LOGGER.exception("Unexpected error during %s %s", method, url)
            raise AutoPiAPIError(f"Unexpected error: {err}") from err
