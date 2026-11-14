"""Conservative, local-only parsing of travel reservation confirmations.

Only explicitly allowlisted itinerary fields are returned. Raw email, payment,
loyalty, ticket, and reservation identifiers are never included in the result.
The patterns below cover *example formats*; real-world provider templates vary.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from email.utils import parseaddr
import hashlib
import re


@dataclass(frozen=True)
class Booking:
    """Non-sensitive information for one reservation segment."""

    kind: str
    provider: str
    start_date: date
    end_date: date
    description: str
    destination: str
    details: dict[str, str] = field(default_factory=dict)

    @property
    def key(self) -> str:
        """Stable de-duplication key from the itinerary, not confirmation IDs."""
        values = (
            self.kind, self.provider, self.start_date.isoformat(),
            self.end_date.isoformat(), self.description, self.destination,
            *(f"{key}:{value}" for key, value in sorted(self.details.items())),
        )
        return hashlib.sha256("\x00".join(values).encode("utf-8")).hexdigest()[:20]

    def as_dict(self) -> dict:
        """Export only allowlisted non-sensitive itinerary fields."""
        return {
            "kind": self.kind,
            "provider": self.provider,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "description": self.description,
            "destination": self.destination,
            **self.details,
        }


def _provider(sender: str) -> str | None:
    address = parseaddr(sender)[1].lower()
    if "@" not in address:
        return None
    domain = address.rsplit("@", 1)[1]
    providers = {
        "american": ("aa.com",),
        "hilton": ("hilton.com", "hiltonhonors.com"),
        "national": ("nationalcar.com", "nationalcarental.com"),
    }
    for name, domains in providers.items():
        if any(domain == item or domain.endswith("." + item) for item in domains):
            return name
    return None


def _field(text: str, *labels: str) -> str:
    """Extract one entire line after a recognized label."""
    joined = "|".join(re.escape(label) for label in labels)
    match = re.search(rf"(?im)^[ \t]*(?:{joined})[ \t]*:[ \t]*([^\r\n]+)", text)
    return _clean(match.group(1)) if match else ""


def _clean(value: str) -> str:
    value = re.sub(r"[\x00-\x1f\x7f]+", " ", value)
    # Never publish codes accidentally appended to otherwise valid itinerary fields.
    value = re.split(
        r"(?i)\\b(?:confirmation|reservation(?:\\s+(?:number|code))?|booking\\s+(?:reference|code)|ticket\\s+(?:number|code)|payment|card\\s+ending|loyalty\\s+(?:number|id)|member\\s+(?:number|id))\\b\\s*[:#-]?",
        value,
        maxsplit=1,
    )[0]
    return re.sub(r"\\s+", " ", value).strip(" -|,;")[:100]


def _date(value: str) -> date | None:
    """Parse an explicitly supplied date, never infer one from email receipt time."""
    patterns = (
        (r"\b\d{4}-\d{2}-\d{2}\b", "%Y-%m-%d"),
        (r"\b\d{1,2}/\d{1,2}/\d{4}\b", "%m/%d/%Y"),
        (r"\b[A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4}\b", None),
    )
    for pattern, fmt in patterns:
        found = re.search(pattern, value, flags=re.I)
        if not found:
            continue
        candidate = found.group().replace(",", "")
        formats = (fmt,) if fmt else ("%b %d %Y", "%B %d %Y")
        for candidate_fmt in formats:
            try:
                return datetime.strptime(candidate, candidate_fmt).date()
            except ValueError:
                pass
    return None


def _time(value: str) -> str:
    match = re.search(r"\b(?:1[0-2]|0?[1-9]):[0-5]\d\s*[AP]M\b|\b(?:[01]?\d|2[0-3]):[0-5]\d\b", value, re.I)
    return _clean(match.group()) if match else ""


def _airport(value: str) -> str:
    # Prefer an explicit IATA code, e.g. Boston Logan (BOS) or just BOS.
    matches = re.findall(r"\b[A-Z]{3}\b", value)
    if matches:
        return matches[-1]
    return _clean(value)


def parse_confirmation(sender: str, subject: str, body: str) -> Booking | None:
    """Parse a recognized provider's plain-text confirmation into safe fields.

    No booking is emitted without an explicit start date. Unrecognized email is
    ignored, and a sender domain alone is not considered proof of authenticity.
    """
    provider = _provider(sender)
    if not provider:
        return None
    # Cancelled notices should not create new bookings. Proper cancellation
    # reconciliation with earlier confirmations remains a future feature.
    if re.search(r"\\b(?:canceled|cancelled|voided)\\b", subject, re.I):
        return None
    body = body[:150_000]

    if provider == "american":
        flight_field = _field(body, "Flight", "Flight number")
        number = re.search(r"\bAA\s*[- ]?\s*\d{1,4}\b", flight_field or body, re.I)
        departure = _field(body, "Departure", "Departs", "Departure date", "Depart")
        arrival = _field(body, "Arrival", "Arrives", "Arrival date")
        start = _date(departure)
        if not number or not start:
            return None
        origin = _airport(_field(body, "From", "Origin", "Departure airport"))
        destination = _airport(_field(body, "To", "Destination", "Arrival airport"))
        if not origin or not destination:
            return None
        end = _date(arrival) or start
        if end < start:
            return None
        flight_number = re.sub(r"[\s-]+", "", number.group()).upper()
        details = {"flight_number": flight_number, "origin": origin, "arrival_airport": destination}
        if depart_time := _time(departure):
            details["departure_time_local"] = depart_time
        if arrive_time := _time(arrival):
            details["arrival_time_local"] = arrive_time
        return Booking("flight", "American Airlines", start, end,
                       f"{origin} to {destination}", destination, details)

    if provider == "hilton":
        checkin = _date(_field(body, "Check-in", "Check in", "Arrival date"))
        checkout = _date(_field(body, "Check-out", "Check out", "Departure date"))
        if not checkin or not checkout or checkout <= checkin:
            return None
        hotel = _field(body, "Hotel", "Property", "Hotel name") or "Hilton stay"
        city = _field(body, "City", "Location")
        return Booking("hotel", "Hilton", checkin, checkout, hotel, city,
                       {"hotel": hotel})

    if provider == "national":
        pickup = _date(_field(body, "Pickup date", "Pick-up date", "Pick up date"))
        returned = _date(_field(body, "Return date", "Drop-off date", "Dropoff date"))
        if not pickup or not returned or returned < pickup:
            return None
        location = _field(body, "Pickup location", "Pick-up location", "Pick up location")
        destination = _field(body, "Return location", "Drop-off location") or location
        details = {}
        if location:
            details["pickup_location"] = location
        if destination:
            details["return_location"] = destination
        return Booking("rental_car", "National", pickup, returned,
                       "National rental car", destination, details)
    return None
