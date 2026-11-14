"""Group reservations and build a safe Home Assistant state snapshot."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from .parser import Booking


@dataclass(frozen=True)
class Trip:
    start_date: date
    end_date: date
    destination: str
    bookings: tuple[Booking, ...]

    def as_dict(self) -> dict:
        return {
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "destination": self.destination,
            "reservations": [booking.as_dict() for booking in self.bookings[:10]],
        }


def group_trips(bookings: list[Booking]) -> list[Trip]:
    """Simple adjacency grouping, not yet a full round-trip matcher."""
    unique = {booking.key: booking for booking in bookings}
    ordered = sorted(unique.values(), key=lambda booking: (booking.start_date, booking.end_date))
    groups: list[list[Booking]] = []
    for booking in ordered:
        if groups and booking.start_date <= max(b.end_date for b in groups[-1]) + timedelta(days=1):
            groups[-1].append(booking)
        else:
            groups.append([booking])
    result = []
    for group in groups:
        flight = next((b for b in group if b.kind == "flight"), None)
        hotel = next((b for b in group if b.kind == "hotel"), None)
        result.append(Trip(
            min(b.start_date for b in group),
            max(b.end_date for b in group),
            (flight or hotel or group[0]).destination or "Trip",
            tuple(group),
        ))
    return result


def build_snapshot(bookings: list[Booking], today: date) -> dict:
    """Create the only data exposed through Home Assistant."""
    unique = {booking.key: booking for booking in bookings}
    ordered = sorted(unique.values(), key=lambda b: (b.start_date, b.kind))
    trips = group_trips(ordered)
    upcoming = [trip for trip in trips if trip.end_date >= today]

    def next_booking(kind: str) -> dict | None:
        found = next((b for b in ordered if b.kind == kind and b.end_date >= today), None)
        return found.as_dict() if found else None

    next_trip = upcoming[0] if upcoming else None
    return {
        "next_trip": next_trip.as_dict() if next_trip else None,
        "next_flight": next_booking("flight"),
        "next_hotel": next_booking("hotel"),
        "next_rental_car": next_booking("rental_car"),
        "days_until_trip": max((next_trip.start_date - today).days, 0) if next_trip else None,
        "upcoming_trips": [trip.as_dict() for trip in upcoming[:5]],
        "upcoming_count": len(upcoming),
        "travel_today": any(trip.start_date <= today <= trip.end_date for trip in trips),
        "travel_this_week": any(trip.start_date <= today + timedelta(days=6)
                                and trip.end_date >= today for trip in trips),
    }
