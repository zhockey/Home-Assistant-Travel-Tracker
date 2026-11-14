"""Periodic read-only IMAP polling for Travel Tracker."""

from __future__ import annotations

from datetime import timedelta
import imaplib
import logging
import ssl

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import CONF_FOLDER, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, DOMAIN
from .mailbox import fetch_bookings
from .trips import build_snapshot

_LOGGER = logging.getLogger(__name__)


class TravelCoordinator(DataUpdateCoordinator[dict]):
    """Fetch a compact, sanitized itinerary snapshot."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass, _LOGGER, name=DOMAIN,
            update_interval=timedelta(minutes=entry.data.get(
                CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)),
        )
        self.entry = entry

    async def _async_update_data(self) -> dict:
        data = self.entry.data
        today = dt_util.now().date()
        try:
            bookings = await self.hass.async_add_executor_job(
                fetch_bookings, data[CONF_HOST], data[CONF_PORT],
                data[CONF_USERNAME], data[CONF_PASSWORD],
                data[CONF_FOLDER], today,
            )
        except (OSError, TimeoutError, imaplib.IMAP4.error, ssl.SSLError) as exc:
            # Never put credentials or email contents into logs or error messages.
            raise UpdateFailed(
                f"Unable to read IMAP mailbox ({type(exc).__name__})"
            ) from exc
        return build_snapshot(bookings, today)
