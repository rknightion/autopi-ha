"""Tests for trip data parsing."""

from datetime import UTC, datetime

from custom_components.autopi.types import AutoPiTrip, TripData


def test_trip_parsing_with_none_duration():
    """Test that trips with None duration are parsed correctly."""
    trip_data: TripData = {
        "id": "test-trip-1",
        "start_time_utc": "2025-07-28T10:00:00Z",
        "end_time_utc": "2025-07-28T10:30:00Z",
        "start_position_lat": "52.520008",
        "start_position_lng": "13.404954",
        "start_position_display": None,
        "end_position_lat": "52.520008",
        "end_position_lng": "13.404954",
        "end_position_display": None,
        "vehicle": 123,
        "duration": None,  # This is the issue
        "distanceKm": 15.5,
        "tag": "trip",
        "last_recalc": "2025-07-28T10:31:00Z",
        "state": "completed",
    }

    # This should not raise an exception
    trip = AutoPiTrip.from_api_data(trip_data)

    assert trip.trip_id == "test-trip-1"
    assert trip.duration_seconds == 0  # Default when parsing fails
    assert trip.distance_km == 15.5
    assert trip.vehicle_id == 123


def test_trip_parsing_with_invalid_duration():
    """Test that trips with invalid duration format are parsed correctly."""
    trip_data: TripData = {
        "id": "test-trip-2",
        "start_time_utc": "2025-07-28T10:00:00Z",
        "end_time_utc": "2025-07-28T10:30:00Z",
        "start_position_lat": "52.520008",
        "start_position_lng": "13.404954",
        "start_position_display": None,
        "end_position_lat": "52.520008",
        "end_position_lng": "13.404954",
        "end_position_display": None,
        "vehicle": 123,
        "duration": "invalid-format",
        "distanceKm": 15.5,
        "tag": "trip",
        "last_recalc": "2025-07-28T10:31:00Z",
        "state": "completed",
    }

    trip = AutoPiTrip.from_api_data(trip_data)
    assert trip.duration_seconds == 0


def test_trip_parsing_with_valid_duration():
    """Test that trips with valid duration are parsed correctly."""
    trip_data: TripData = {
        "id": "test-trip-3",
        "start_time_utc": "2025-07-28T10:00:00Z",
        "end_time_utc": "2025-07-28T10:30:00Z",
        "start_position_lat": "52.520008",
        "start_position_lng": "13.404954",
        "start_position_display": None,
        "end_position_lat": "52.520008",
        "end_position_lng": "13.404954",
        "end_position_display": None,
        "vehicle": 123,
        "duration": "01:25:30",  # 1 hour, 25 minutes, 30 seconds
        "distanceKm": 15.5,
        "tag": "trip",
        "last_recalc": "2025-07-28T10:31:00Z",
        "state": "completed",
    }

    trip = AutoPiTrip.from_api_data(trip_data)
    assert trip.duration_seconds == 5130  # 1*3600 + 25*60 + 30


def test_trip_parsing_in_progress():
    """Test that in-progress trips are parsed correctly."""
    trip_data: TripData = {
        "id": "test-trip-4",
        "start_time_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),  # Started just now
        "end_time_utc": "",  # Not ended yet
        "start_position_lat": "52.520008",
        "start_position_lng": "13.404954",
        "start_position_display": None,
        "end_position_lat": "0",  # Not at end yet
        "end_position_lng": "0",
        "end_position_display": None,
        "vehicle": 123,
        "duration": None,  # In-progress
        "distanceKm": 0.0,
        "tag": "trip",
        "last_recalc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "state": "in_progress",
    }

    trip = AutoPiTrip.from_api_data(trip_data)
    assert trip.trip_id == "test-trip-4"
    # Duration should be calculated from start time (close to 0 since we just started)
    assert trip.duration_seconds >= 0
    assert trip.duration_seconds < 5  # Should be less than 5 seconds
    assert trip.state == "in_progress"


def test_trip_parsing_in_progress_with_none_positions():
    """Test that in-progress trips with None end positions are parsed correctly."""
    trip_data: TripData = {
        "id": "test-trip-5",
        "start_time_utc": "2025-07-28T15:58:40Z",
        "end_time_utc": None,
        "start_position_lat": "51.264327",
        "start_position_lng": "-1.085937",
        "start_position_display": {},
        "end_position_lat": None,
        "end_position_lng": None,
        "end_position_display": {},
        "vehicle": 5353,
        "duration": None,
        "distanceKm": 0.0,
        "tag": "",
        "last_recalc": None,
        "state": "IN_PROGRESS_WITHOUT_END",
    }

    # This should not raise an exception
    trip = AutoPiTrip.from_api_data(trip_data)

    assert trip.trip_id == "test-trip-5"
    assert trip.start_lat == 51.264327
    assert trip.start_lng == -1.085937
    assert trip.end_lat == 0.0  # Default value for None
    assert trip.end_lng == 0.0  # Default value for None
    assert trip.state == "IN_PROGRESS_WITHOUT_END"
