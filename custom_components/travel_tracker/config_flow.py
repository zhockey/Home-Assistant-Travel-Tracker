"""Home Assistant UI for setting up a TLS IMAP inbox."""

from __future__ import annotations

import imaplib
import ssl

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
import voluptuous as vol

from .const import (
    CONF_FOLDER, CONF_SCAN_INTERVAL, DEFAULT_FOLDER, DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL, DOMAIN, MAX_SCAN_INTERVAL, MIN_SCAN_INTERVAL,
)
from .mailbox import test_mailbox


class TravelTrackerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Configure mailbox access through the Home Assistant UI."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None):
        errors = {}
        if user_input is not None:
            try:
                await self.hass.async_add_executor_job(
                    test_mailbox, user_input[CONF_HOST], user_input[CONF_PORT],
                    user_input[CONF_USERNAME], user_input[CONF_PASSWORD],
                    user_input[CONF_FOLDER],
                )
            except imaplib.IMAP4.error:
                errors["base"] = "invalid_auth_or_folder"
            except (OSError, TimeoutError, ssl.SSLError):
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(
                    f"{user_input[CONF_HOST].lower()}:{user_input[CONF_USERNAME].lower()}:"
                    f"{user_input[CONF_FOLDER].lower()}"
                )
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title="Travel Tracker", data=user_input)

        schema = vol.Schema({
            vol.Required(CONF_HOST): str,
            vol.Optional(CONF_PORT, default=DEFAULT_PORT): vol.All(
                vol.Coerce(int), vol.Range(min=1, max=65535)),
            vol.Required(CONF_USERNAME): str,
            vol.Required(CONF_PASSWORD): str,
            vol.Optional(CONF_FOLDER, default=DEFAULT_FOLDER): str,
            vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
                vol.Coerce(int), vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL)),
        })
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
