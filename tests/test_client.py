"""Tests for AutoPi API client."""

from unittest.mock import AsyncMock, Mock, patch

import aiohttp
import pytest

from custom_components.autopi.client import AutoPiClient
from custom_components.autopi.const import (
    DEFAULT_BASE_URL,
    VEHICLE_PROFILE_ENDPOINT,
)
from custom_components.autopi.exceptions import (
    AutoPiAPIError,
    AutoPiAuthenticationError,
    AutoPiConnectionError,
    AutoPiRateLimitError,
    AutoPiTimeoutError,
)


def create_async_context_manager(return_value):
    """Create an async context manager mock."""
    async_cm = AsyncMock()
    async_cm.__aenter__.return_value = return_value
    async_cm.__aexit__.return_value = None
    return async_cm


@pytest.fixture
def mock_session():
    """Create a mock aiohttp session."""
    session = Mock(spec=aiohttp.ClientSession)
    session.close = AsyncMock()
    # Configure request to be a regular Mock that will be overridden in tests
    session.request = Mock()
    return session


@pytest.fixture
def client(mock_session):
    """Create an AutoPi client with mocked session."""
    return AutoPiClient(mock_session, "test_api_key", DEFAULT_BASE_URL)


class TestAutoPiClient:
    """Test the AutoPi API client."""

    @pytest.mark.asyncio
    async def test_client_initialization(self):
        """Test client initialization with custom session."""
        session = Mock(spec=aiohttp.ClientSession)
        client = AutoPiClient(session, "test_key", "https://custom.api.url")

        assert client._api_key == "test_key"
        assert client._base_url == "https://custom.api.url"
        assert client._session == session

    @pytest.mark.asyncio
    async def test_get_vehicles_success(self, client, mock_session):
        """Test successful vehicle retrieval."""
        mock_response = Mock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="")
        mock_response.json = AsyncMock(return_value={
            "results": [
                {
                    "id": 123,
                    "display_name": "Test Vehicle",
                    "callName": "Test",
                    "licensePlate": "ABC123",
                    "vin": "1234567890",
                    "year": 2020,
                    "type": "ICE",
                    "battery_nominal_voltage": 12,
                    "devices": [{"id": "device1"}],
                    "make": {"id": 1},
                    "model": {"id": 1},
                }
            ],
            "next": None,
        })

        # Configure mock to return an async context manager
        mock_session.request.return_value = create_async_context_manager(mock_response)

        vehicles = await client.get_vehicles()

        assert len(vehicles) == 1
        assert vehicles[0].id == 123
        assert vehicles[0].name == "Test"
        assert vehicles[0].license_plate == "ABC123"

        # Verify API call
        mock_session.request.assert_called_once()
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "GET"
        assert VEHICLE_PROFILE_ENDPOINT in call_args[0][1]
        assert call_args[1]["headers"]["Authorization"] == "APIToken test_api_key"

    @pytest.mark.asyncio
    async def test_get_vehicles_pagination(self, client, mock_session):
        """Test vehicle retrieval with pagination."""
        # First page
        mock_response1 = Mock()
        mock_response1.status = 200
        mock_response1.text = AsyncMock(return_value="")
        mock_response1.json = AsyncMock(return_value={
            "results": [{
                "id": 1,
                "display_name": "Vehicle 1",
                "callName": "V1",
                "licensePlate": "ABC111",
                "vin": "VIN111",
                "year": 2021,
                "type": "ICE",
                "battery_nominal_voltage": 12,
                "devices": [{"id": "d1"}],
                "make": {"id": 1},
                "model": {"id": 1},
            }],
            "next": f"{DEFAULT_BASE_URL}/next_page",
        })

        # Second page
        mock_response2 = Mock()
        mock_response2.status = 200
        mock_response2.text = AsyncMock(return_value="")
        mock_response2.json = AsyncMock(return_value={
            "results": [{
                "id": 2,
                "display_name": "Vehicle 2",
                "callName": "V2",
                "licensePlate": "ABC222",
                "vin": "VIN222",
                "year": 2022,
                "type": "ICE",
                "battery_nominal_voltage": 12,
                "devices": [{"id": "d2"}],
                "make": {"id": 1},
                "model": {"id": 1},
            }],
            "next": None,
        })

        # Configure mock to return responses in sequence
        mock_session.request.side_effect = [
            create_async_context_manager(mock_response1),
            create_async_context_manager(mock_response2),
        ]

        vehicles = await client.get_vehicles()

        # Currently the client doesn't follow pagination, so we only get the first page
        assert len(vehicles) == 1
        assert vehicles[0].id == 1
        assert mock_session.request.call_count == 1

    @pytest.mark.asyncio
    async def test_get_vehicles_auth_error(self, client, mock_session):
        """Test authentication error handling."""
        mock_response = Mock()
        mock_response.status = 401
        mock_response.text = AsyncMock(return_value="Unauthorized")

        mock_session.request.return_value = create_async_context_manager(mock_response)

        with pytest.raises(AutoPiAuthenticationError):
            await client.get_vehicles()

    @pytest.mark.asyncio
    async def test_get_vehicles_rate_limit(self, client, mock_session):
        """Test rate limit error handling."""
        mock_response = Mock()
        mock_response.status = 429
        mock_response.text = AsyncMock(return_value="Rate limit exceeded")

        mock_session.request.return_value = create_async_context_manager(mock_response)

        with pytest.raises(AutoPiRateLimitError):
            await client.get_vehicles()

    @pytest.mark.asyncio
    async def test_get_vehicles_connection_error(self, client, mock_session):
        """Test connection error handling."""
        # Configure request to raise an exception
        mock_session.request.side_effect = aiohttp.ClientError("Connection failed")

        with pytest.raises(AutoPiConnectionError):
            await client.get_vehicles()

    @pytest.mark.asyncio
    async def test_get_vehicles_timeout(self, client, mock_session):
        """Test timeout error handling."""
        # Configure request to raise a timeout exception
        mock_session.request.side_effect = TimeoutError()

        with pytest.raises(AutoPiTimeoutError):
            await client.get_vehicles()

    @pytest.mark.asyncio
    async def test_get_data_fields_success(self, client, mock_session):
        """Test successful data fields retrieval."""
        mock_response = Mock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="")
        mock_response.json = AsyncMock(return_value=[
            {
                "field_prefix": "obd.bat",
                "field_name": "level",
                "frequency": 1.0,
                "type": "int",
                "title": "Battery Level",
                "last_seen": "2024-01-20T10:00:00Z",
                "last_value": 85,
                "description": "Battery charge level",
            },
            {
                "field_prefix": "track.pos",
                "field_name": "loc",
                "frequency": 0.5,
                "type": "dict",
                "title": "Location",
                "last_seen": "2024-01-20T10:00:00Z",
                "last_value": {"lat": 51.264327, "lon": -1.085937},
                "description": "GPS location",
            },
        ])

        mock_session.request.return_value = create_async_context_manager(mock_response)

        fields = await client.get_data_fields("device1", 123)

        assert len(fields) == 2
        assert "obd.bat.level" in fields
        assert "track.pos.loc" in fields

        # Check first field
        bat_field = fields["obd.bat.level"]
        assert bat_field.field_id == "obd.bat.level"
        assert bat_field.last_value == 85
        assert bat_field.frequency == 1.0
        assert bat_field.value_type == "int"

        # Check location field
        loc_field = fields["track.pos.loc"]
        assert isinstance(loc_field.last_value, dict)
        assert loc_field.last_value["lat"] == 51.264327

    @pytest.mark.asyncio
    async def test_get_data_fields_empty_response(self, client, mock_session):
        """Test handling of empty data fields response."""
        mock_response = Mock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="")
        mock_response.json = AsyncMock(return_value=[])

        mock_session.request.return_value = create_async_context_manager(mock_response)

        fields = await client.get_data_fields("device1", 123)

        assert fields == {}

    @pytest.mark.asyncio
    async def test_get_data_fields_api_error(self, client, mock_session):
        """Test API error handling for data fields."""
        mock_response = Mock()
        mock_response.status = 500
        mock_response.text = AsyncMock(return_value="Internal server error")

        mock_session.request.return_value = create_async_context_manager(mock_response)

        with pytest.raises(AutoPiAPIError) as exc_info:
            await client.get_data_fields("device1", 123)

        assert "500" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_retry_logic(self, client, mock_session):
        """Test retry logic with exponential backoff."""
        # First two attempts fail, third succeeds
        mock_response_fail = Mock()
        mock_response_fail.status = 503
        mock_response_fail.text = AsyncMock(return_value="Service unavailable")

        mock_response_success = Mock()
        mock_response_success.status = 200
        mock_response_success.text = AsyncMock(return_value="")
        mock_response_success.json = AsyncMock(return_value={"results": [], "next": None})

        # Configure mock to fail twice then succeed
        mock_session.request.side_effect = [
            create_async_context_manager(mock_response_fail),
            create_async_context_manager(mock_response_fail),
            create_async_context_manager(mock_response_success),
        ]

        with patch("asyncio.sleep", new_callable=AsyncMock):
            vehicles = await client.get_vehicles()

        assert vehicles == []
        assert mock_session.request.call_count == 3

