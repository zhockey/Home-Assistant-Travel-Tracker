"""Use only invented confirmation details in test fixtures."""

from datetime import date

# Import the pure parser directly, bypassing the legacy integration's HA imports.
import importlib.util
from pathlib import Path
import sys

PARSER_PATH = Path(__file__).resolve().parents[1] / "custom_components" / "travel_tracker" / "parser.py"
spec = importlib.util.spec_from_file_location("travel_tracker_isolated_parser", PARSER_PATH)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
parse_confirmation = module.parse_confirmation


AA_BODY = """Flight: AA 2345
From: Boston Logan (BOS)
To: Pittsburgh (PIT)
Departure: November 19, 2026 9:15 AM
Arrival: November 19, 2026 11:05 AM
Confirmation: XY5M3Q
Ticket number: 0001234567890
Payment: VISA ending 1234
"""
HILTON_BODY = """Hotel: Hilton Garden Inn Pittsburgh
City: Pittsburgh, PA
Check-in: November 19, 2026
Check-out: November 22, 2026
Confirmation: TEST-SHOULD-NOT-STORE
"""
NATIONAL_BODY = """Pickup location: Pittsburgh International Airport
Pickup date: November 19, 2026
Return location: Pittsburgh International Airport
Return date: November 22, 2026
Reservation: SECRET-BOOKING-NUMBER
"""


def test_american_flight():
    booking = parse_confirmation('"American Airlines" <notifications@email.aa.com>',
                                 "Your trip", AA_BODY)
    assert booking.kind == "flight"
    assert booking.provider == "American Airlines"
    assert booking.start_date == date(2026, 11, 19)
    assert booking.description == "BOS to PIT"
    assert booking.details["flight_number"] == "AA2345"
    assert booking.details["departure_time_local"] == "9:15 AM"
    assert booking.details["arrival_time_local"] == "11:05 AM"


def test_hilton():
    booking = parse_confirmation("reservation@hilton.com", "Stay confirmed", HILTON_BODY)
    assert booking.kind == "hotel"
    assert booking.end_date == date(2026, 11, 22)
    assert booking.destination == "Pittsburgh, PA"


def test_national():
    booking = parse_confirmation("no-reply@nationalcar.com", "Reservation", NATIONAL_BODY)
    assert booking.kind == "rental_car"
    assert booking.details["pickup_location"] == "Pittsburgh International Airport"


def test_privacy_whitelist_excludes_codes_payment_and_loyalty():
    samples = [
        ("notification@aa.com", AA_BODY),
        ("reservation@hilton.com", HILTON_BODY),
        ("reservation@nationalcar.com", NATIONAL_BODY),
    ]
    for sender, body in samples:
        booking = parse_confirmation(sender, "Confirmation", body)
        output = str(booking.as_dict()).upper()
        for value in ("XY5M3Q", "0001234567890", "VISA", "TEST-SHOULD", "SECRET-BOOKING"):
            assert value not in output


def test_unknown_sender_and_lookalike_domain_ignored():
    assert parse_confirmation("someone@random.com", "Flight", AA_BODY) is None
    assert parse_confirmation("fake@aa.com.evil.example", "Flight", AA_BODY) is None


def test_missing_departure_date_not_guessed():
    text = AA_BODY.replace("Departure: November 19, 2026 9:15 AM", "Departure: 9:15 AM")
    assert parse_confirmation("notify@aa.com", "Confirmation", text) is None


def test_missing_route_not_guessed():
    text = AA_BODY.replace("To: Pittsburgh (PIT)", "")
    assert parse_confirmation("notify@aa.com", "Confirmation", text) is None


def test_invalid_hotel_dates_not_accepted():
    text = HILTON_BODY.replace("November 22, 2026", "November 18, 2026")
    assert parse_confirmation("stay@hilton.com", "Stay", text) is None


def test_iso_and_numeric_dates_accepted():
    text = AA_BODY.replace("November 19, 2026 9:15 AM", "2026-11-19 9:15 AM")
    text = text.replace("November 19, 2026 11:05 AM", "11/19/2026 11:05 AM")
    assert parse_confirmation("test@aa.com", "Flight", text).start_date == date(2026, 11, 19)


def test_repeat_yields_same_deduplication_key():
    first = parse_confirmation("test@aa.com", "Flight", AA_BODY)
    second = parse_confirmation("test@aa.com", "Flight", AA_BODY)
    assert first.key == second.key


def test_cancelled_subject_does_not_create_new_booking():
    assert parse_confirmation("notification@aa.com", "Your flight is cancelled", AA_BODY) is None
    assert parse_confirmation("notification@aa.com", "Flight confirmed", AA_BODY) is not None


def test_sensitive_codes_appended_to_hotel_field_do_not_leak():
    altered = HILTON_BODY.replace(
        "Hotel: Hilton Garden Inn Pittsburgh",
        "Hotel: Hilton Garden Inn Pittsburgh | Confirmation: SECURE-PNR-123",
    )
    booking = parse_confirmation("stay@hilton.com", "Confirmed", altered)
    assert booking is not None
    assert booking.details["hotel"] == "Hilton Garden Inn Pittsburgh"
    assert "SECURE-PNR-123" not in str(booking.as_dict())


def test_flight_time_change_keeps_same_identity():
    original = parse_confirmation("notify@aa.com", "Booking", AA_BODY)
    updated = parse_confirmation(
        "notify@aa.com", "New departure time",
        AA_BODY.replace("9:15 AM", "10:30 AM"),
    )
    assert original.key == updated.key
    assert updated.details["departure_time_local"] == "10:30 AM"


def test_different_day_or_route_is_not_deduplicated():
    original = parse_confirmation("notify@aa.com", "Booking", AA_BODY)
    other_date = parse_confirmation(
        "notify@aa.com", "Booking", AA_BODY.replace("November 19, 2026", "November 20, 2026")
    )
    other_route = parse_confirmation(
        "notify@aa.com", "Booking", AA_BODY.replace("Pittsburgh (PIT)", "New York (JFK)")
    )
    assert original.key != other_date.key
    assert original.key != other_route.key
