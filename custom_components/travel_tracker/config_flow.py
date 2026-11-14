"""Home Assistant UI for standalone IMAP or opt-in Mail and Packages reuse."""

from __future__ import annotations

import imaplib
import ssl

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)
import voluptuous as vol

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
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
    SOURCE_LINKED,
    SOURCE_IMAP,
)
from .mailbox import test_mailbox


class TravelTrackerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Explicitly select a saved local M&P account or configure new IMAP access."""

    VERSION = 1

    def _mail_and_packages_entries(self) -> dict[str, str]:
        """Expose account labels, never passwords or private source data."""
        entries = {}
        for entry in self.hass.config_entries.async_entries(
            MAIL_AND_PACKAGES_DOMAIN
        ):
            host = entry.data.get(CONF_HOST)
            username = entry.data.get(CONF_USERNAME)
            password = entry.data.get(CONF_PASSWORD)
            if (
                isinstance(host, str)
                and host
                and isinstance(username, str)
                and username
                and isinstance(password, str)
                and password
            ):
                entries[entry.entry_id] = f"{username} ({host})"
        return entries

    async def async_step_user(self, user_input: dict | None = None):
        """Offer two clear paths only when Mail and Packages is present."""
        if self._mail_and_packages_entries():
            return self.async_show_menu(
                step_id="user",
                menu_options=["linked", "imap"],
            )
        return await self.async_step_imap(user_input)

    async def async_step_linked(self, user_input: dict | None = None):
        """Reference an installed Mail and Packages config entry with consent.

        This avoids a second saved password, not a second IMAP connection.
        """
        options = self._mail_and_packages_entries()
        if not options:
            return self.async_abort(reason="mail_and_packages_not_found")

        errors = {}
        if user_input is not None:
            linked_id = user_input.get(CONF_LINKED_ENTRY_ID)
            if linked_id not in options:
                errors[CONF_LINKED_ENTRY_ID] = "invalid_source"
            else:
                folder = user_input.get(CONF_FOLDER, "").strip()
                await self.async_set_unique_id(
                    f"linked:{linked_id}:{folder.lower() or 'source_folder'}"
                )
                self._abort_if_unique_id_configured()
                data = {
                    CONF_SOURCE: SOURCE_LINKED,
                    CONF_LINKED_ENTRY_ID: linked_id,
                    CONF_SCAN_INTERVAL: user_input.get(
                        CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                    ),
                }
                if folder:
                    data[CONF_FOLDER] = folder
                # No password, IMAP host or username copied into this entry.
                return self.async_create_entry(
                    title="Travel Tracker (Mail and Packages settings)",
                    data=data,
                )
        return self.async_show_form(
            step_id="linked",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_LINKED_ENTRY_ID): vol.In(options),
                    vol.Optional(CONF_FOLDER): str,
                    vol.Optional(
                        CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(
                            min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL
                        ),
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_imap(self, user_input: dict | None = None):
        """Set up a separate read-only TLS IMAP connection."""
        errors = {}
        if user_input is not None:
            try:
                await self.hass.async_add_executor_job(
                    test_mailbox,
                    user_input[CONF_HOST],
                    user_input[CONF_PORT],
                    user_input[CONF_USERNAME],
                    user_input[CONF_PASSWORD],
                    user_input[CONF_FOLDER],
                )
            except imaplib.IMAP4.error:
                errors["base"] = "invalid_auth_or_folder"
            except (OSError, TimeoutError, ssl.SSLError):
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(
                    f"direct:{user_input[CONF_HOST].lower()}:"
                    f"{user_input[CONF_USERNAME].lower()}:"
                    f"{user_input[CONF_FOLDER].lower()}"
                )
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title="Travel Tracker",
                    data={CONF_SOURCE: SOURCE_IMAP, **user_input},
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Optional(CONF_PORT, default=DEFAULT_PORT): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=65535)
                ),
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): TextSelector(
                    TextSelectorConfig(
                        type=TextSelectorType.PASSWORD,
                        autocomplete="current-password",
                    )
                ),
                vol.Optional(CONF_FOLDER, default=DEFAULT_FOLDER): str,
                vol.Optional(
                    CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                ): vol.All(
                    vol.Coerce(int),
                    vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL),
                ),
            }
        )
        return self.async_show_form(
            step_id="imap", data_schema=schema, errors=errors
        )
