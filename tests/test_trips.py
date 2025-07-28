"""Tests for AutoPi trip functionality."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest

from custom_components.autopi.client import AutoPiClient
from custom_components.autopi.types import AutoPiTrip, TripData


class TestTripData:
    """Test trip data models."""

    def test_autopi_trip_from_api_data(self):
        """Test creating AutoPiTrip from API data."""
        trip_data: TripData = {
            "id": "8ef02061-b186-493f-aa01-2d273b0e16e5",
            "start_time_utc": "2025-07-28T06:36:24Z",
            "end_time_utc": "2025-07-28T07:14:50Z",
            "start_position_lat": "50.968820",
            "start_position_lng": "-1.301295",
            "start_position_display": {
                "address": "Mitchell Drive, Fair Oak, Eastleigh",
                "city": "Eastleigh",
                "county": "Hampshire",
                "country": "United Kingdom",
                "postal_code": "SO50 7FN",
                "country_code": "gb",
                "latitude": "50.96862636505153",
                "longitude": "-1.301216205826457",
                "provider": "OpenStreetMap",
                "precision": "street",
            },
            "end_position_lat": "51.264327",
            "end_position_lng": "-1.085937",
            "end_position_display": {
                "address": "Festival Place, Basingstoke",
                "city": "Basingstoke",
                "county": "Hampshire",
                "country": "United Kingdom",
                "postal_code": "RG21 7BL",
                "country_code": "gb",
                "latitude": "51.26528375",
                "longitude": "-1.0860997523377698",
                "provider": "OpenStreetMap",
                "precision": "street",
            },
            "vehicle": 5353,
            "duration": "00:38:26",
            "distanceKm": 42.8405581064021,
            "tag": "",
            "last_recalc": "2025-07-28T07:29:59.001287Z",
            "state": "COMPLETED",
        }

        trip = AutoPiTrip.from_api_data(trip_data)

        assert trip.trip_id == "8ef02061-b186-493f-aa01-2d273b0e16e5"
        assert trip.start_time == datetime(2025, 7, 28, 6, 36, 24, tzinfo=UTC)
        assert trip.end_time == datetime(2025, 7, 28, 7, 14, 50, tzinfo=UTC)
        assert trip.start_lat == 50.968820
        assert trip.start_lng == -1.301295
        assert trip.start_address == "Mitchell Drive, Fair Oak, Eastleigh"
        assert trip.end_lat == 51.264327
        assert trip.end_lng == -1.085937
        assert trip.end_address == "Festival Place, Basingstoke"
        assert trip.vehicle_id == 5353
        assert trip.duration_seconds == 2306  # 38 minutes 26 seconds
        assert trip.distance_km == 42.8405581064021
        assert trip.state == "COMPLETED"

    def test_autopi_trip_no_address(self):
        """Test creating AutoPiTrip without address display data."""
        trip_data: TripData = {
            "id": "test-trip",
            "start_time_utc": "2025-07-28T06:36:24Z",
            "end_time_utc": "2025-07-28T07:14:50Z",
            "start_position_lat": "50.968820",
            "start_position_lng": "-1.301295",
            "start_position_display": None,
            "end_position_lat": "51.264327",
            "end_position_lng": "-1.085937",
            "end_position_display": None,
            "vehicle": 123,
            "duration": "01:00:00",
            "distanceKm": 50.0,
            "tag": "",
            "last_recalc": "2025-07-28T07:29:59.001287Z",
            "state": "COMPLETED",
        }

        trip = AutoPiTrip.from_api_data(trip_data)

        assert trip.start_address is None
        assert trip.end_address is None
        assert trip.duration_seconds == 3600


class TestAutoPiClientTrips:
    """Test AutoPi client trip methods."""

    @pytest.mark.asyncio
    async def test_get_trips_success(self):
        """Test successful trip fetching."""
        session = Mock()
        client = AutoPiClient(session, "test_key")

        trip_response = {
            "count": 2782,
            "results": [
                {
                    "id": "trip-1",
                    "start_time_utc": "2025-07-28T06:36:24Z",
                    "end_time_utc": "2025-07-28T07:14:50Z",
                    "start_position_lat": "50.968820",
                    "start_position_lng": "-1.301295",
                    "start_position_display": None,
                    "end_position_lat": "51.264327",
                    "end_position_lng": "-1.085937",
                    "end_position_display": None,
                    "vehicle": 123,
                    "duration": "00:30:00",
                    "distanceKm": 25.5,
                    "tag": "",
                    "last_recalc": "2025-07-28T07:29:59Z",
                    "state": "COMPLETED",
                }
            ],
            "page_size": 1,
        }

        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = trip_response

            count, trips = await client.get_trips(123, "device1", page_size=1)

            assert count == 2782
            assert len(trips) == 1
            assert trips[0].trip_id == "trip-1"
            assert trips[0].distance_km == 25.5
            assert trips[0].duration_seconds == 1800

            mock_request.assert_called_once_with(
                "GET",
                "/logbook/v2/trips/",
                params={
                    "vehicle": 123,
                    "device_id": "device1",
                    "page_size": 1,
                    "page": 1,
                },
            )

    @pytest.mark.asyncio
    async def test_get_trips_no_device(self):
        """Test trip fetching without device ID."""
        session = Mock()
        client = AutoPiClient(session, "test_key")

        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"count": 0, "results": [], "page_size": 1}

            count, trips = await client.get_trips(123)

            assert count == 0
            assert len(trips) == 0

            mock_request.assert_called_once_with(
                "GET",
                "/logbook/v2/trips/",
                params={
                    "vehicle": 123,
                    "page_size": 1,
                    "page": 1,
                },
            )

    @pytest.mark.asyncio
    async def test_get_trips_parse_error(self):
        """Test handling of trip parsing errors."""
        session = Mock()
        client = AutoPiClient(session, "test_key")

        trip_response = {
            "count": 1,
            "results": [
                {
                    "id": "trip-1",
                    # Missing required fields
                    "vehicle": 123,
                }
            ],
            "page_size": 1,
        }

        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = trip_response

            count, trips = await client.get_trips(123)

            # Should return count but no trips due to parse error
            assert count == 1
            assert len(trips) == 0
