"""Tests for trip data parsing."""

from datetime import datetime

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
        "start_time_utc": datetime.utcnow().isoformat() + "Z",  # Started just now
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
        "last_recalc": datetime.utcnow().isoformat() + "Z",
        "state": "in_progress",
    }

    trip = AutoPiTrip.from_api_data(trip_data)
    assert trip.trip_id == "test-trip-4"
    # Duration should be calculated from start time (close to 0 since we just started)
    assert trip.duration_seconds >= 0
    assert trip.duration_seconds < 5  # Should be less than 5 seconds
    assert trip.state == "in_progress"
