"""Periodic local read-only IMAP polling for Travel Tracker."""

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

from .const import (
    CONF_FOLDER,
    CONF_LINKED_ENTRY_ID,
    CONF_SCAN_INTERVAL,
    CONF_SOURCE,
    DEFAULT_FOLDER,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAIL_AND_PACKAGES_DOMAIN,
    SOURCE_LINKED,
)
from .mailbox import fetch_bookings
from .trips import build_snapshot

_LOGGER = logging.getLogger(__name__)


def resolve_mailbox_config(hass: HomeAssistant, config: dict) -> tuple:
    """Look up the explicitly linked M&P entry without copying its password.

    Linking reuses account settings; it does NOT share a network IMAP session.
    """
    source = config
    if config.get(CONF_SOURCE) == SOURCE_LINKED:
        entry_id = config.get(CONF_LINKED_ENTRY_ID)
        entry = hass.config_entries.async_get(entry_id) if entry_id else None
        if entry is None or entry.domain != MAIL_AND_PACKAGES_DOMAIN:
            raise UpdateFailed("Linked Mail and Packages account is unavailable")
        source = entry.data
    try:
        host = source[CONF_HOST]
        port = int(source.get(CONF_PORT, DEFAULT_PORT))
        username = source[CONF_USERNAME]
        password = source[CONF_PASSWORD]
        folder = config.get(CONF_FOLDER) or source.get(
            CONF_FOLDER, DEFAULT_FOLDER
        )
        if not (
            isinstance(host, str)
            and host
            and isinstance(username, str)
            and username
            and isinstance(password, str)
            and password
            and isinstance(folder, str)
            and folder
        ):
            raise ValueError("Invalid connection values")
        return host, port, username, password, folder
    except (KeyError, TypeError, ValueError) as exc:
        # Never include host, username, password or source metadata in logs.
        raise UpdateFailed("IMAP account configuration is incomplete") from exc


class TravelCoordinator(DataUpdateCoordinator[dict]):
    """Fetch a sanitized itinerary snapshot from the selected IMAP account."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(
                minutes=entry.data.get(
                    CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                )
            ),
        )
        self.entry = entry

    async def _async_update_data(self) -> dict:
        today = dt_util.now().date()
        params = resolve_mailbox_config(self.hass, self.entry.data)
        try:
            bookings = await self.hass.async_add_executor_job(
                fetch_bookings, *params, today
            )
        except (
            OSError, TimeoutError, imaplib.IMAP4.error, ssl.SSLError
        ) as exc:
            raise UpdateFailed(
                f"Unable to read IMAP mailbox ({type(exc).__name__})"
            ) from exc
        return build_snapshot(bookings, today)
