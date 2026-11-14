"""Synthetic end-to-end reservation test, no Home Assistant or real mailbox."""

from datetime import date
from email.message import EmailMessage
import importlib
from pathlib import Path
import sys
import types
from unittest.mock import patch

package_name = "travel_tracker_sandbox"
root = Path(__file__).resolve().parents[1] / "custom_components" / "travel_tracker"
package = types.ModuleType(package_name)
package.__path__ = [str(root)]
sys.modules[package_name] = package
mailbox = importlib.import_module(package_name + ".mailbox")
trips = importlib.import_module(package_name + ".trips")


def fixture_email(sender, body, html=False):
    message = EmailMessage()
    message["From"] = sender
    message["Subject"] = "Example booking confirmation"
    if html:
        message.set_content(
            "<html><body><script>NOT DATA</script><p>"
            + body.replace("\n", "<br>") + "</p></body></html>",
            subtype="html",
        )
    else:
        message.set_content(body)
    return message.as_bytes()


FLIGHT = """Flight: AA 2345
From: Boston Logan (BOS)
To: Pittsburgh (PIT)
Departure: November 19, 2026 9:15 AM
Arrival: November 19, 2026 11:05 AM
Confirmation: VERY-SECRET-123
"""
HOTEL = """Hotel: Hilton Garden Inn Pittsburgh
City: Pittsburgh, PA
Check-in: November 19, 2026
Check-out: November 22, 2026
Booking reference: PRIVATE-987
"""


def test_imap_to_trip_snapshot_without_network():
    emails = [
        fixture_email("notify@aa.com", FLIGHT),
        fixture_email("stay@hilton.com", HOTEL),
    ]

    class FakeIMAP:
        def __init__(self):
            self.fetch_calls = []
            self.readonly = None

        def login(self, *_args):
            return "OK", [b"login ok"]

        def select(self, _folder, readonly=False):
            self.readonly = readonly
            return "OK", [b"2"]

        def search(self, *_args):
            return "OK", [b"1 2"]

        def fetch(self, index, command):
            self.fetch_calls.append(command)
            return "OK", [(b"BODY[]", emails[int(index) - 1])]

        def logout(self):
            return "BYE", []

    fake = FakeIMAP()
    with patch.object(mailbox.imaplib, "IMAP4_SSL", return_value=fake):
        bookings = mailbox.fetch_bookings(
            "imap.example", 993, "test", "secret", "Travel", date(2026, 11, 13)
        )
    assert fake.readonly is True
    assert fake.fetch_calls == ["(BODY.PEEK[])", "(BODY.PEEK[])"]
    assert len(bookings) == 2

    state = trips.build_snapshot(bookings, date(2026, 11, 13))
    assert state["upcoming_count"] == 1
    assert state["next_flight"]["flight_number"] == "AA2345"
    assert state["next_hotel"]["hotel"] == "Hilton Garden Inn Pittsburgh"
    assert state["days_until_trip"] == 6
    assert state["travel_this_week"] is True
    assert "VERY-SECRET" not in str(state)
    assert "PRIVATE-987" not in str(state)
    assert trips.build_snapshot(bookings + bookings, date(2026, 11, 13))["upcoming_count"] == 1


def test_html_only_confirmation():
    booking = mailbox.parse_message(fixture_email("stay@hilton.com", HOTEL, html=True))
    assert booking is not None
    assert booking.kind == "hotel"


def test_non_travel_email_ignored():
    assert mailbox.parse_message(fixture_email("random@example.org", FLIGHT)) is None


def test_previous_trip_is_not_upcoming():
    flight = mailbox.parse_message(fixture_email("notify@aa.com", FLIGHT))
    snapshot = trips.build_snapshot([flight], date(2027, 2, 1))
    assert snapshot["upcoming_count"] == 0
    assert snapshot["next_flight"] is None
