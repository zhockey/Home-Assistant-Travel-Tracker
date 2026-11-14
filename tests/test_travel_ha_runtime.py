"""Run with pytest-homeassistant to verify the actual HA integration setup."""

from datetime import date
from unittest.mock import patch

from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from pytest_homeassistant.common import MockConfigEntry

from custom_components.travel_tracker.const import DOMAIN
from custom_components.travel_tracker.parser import Booking


async def test_integration_creates_eight_entities(hass: HomeAssistant):
    """Set up a fake mailbox using HA's genuine config entry and entity registry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Travel Tracker",
        data={
            CONF_HOST: "imap.invalid.test",
            CONF_PORT: 993,
            CONF_USERNAME: "fake",
            CONF_PASSWORD: "not-a-real-password",
            "folder": "Travel",
            "scan_interval": 30,
        },
    )
    entry.add_to_hass(hass)
    sample = Booking(
        "flight", "American Airlines", date(2026, 11, 19),
        date(2026, 11, 19), "BOS to PIT", "PIT",
        {"flight_number": "AA2345", "origin": "BOS", "arrival_airport": "PIT"},
    )
    with patch(
        "custom_components.travel_tracker.coordinator.fetch_bookings",
        return_value=[sample],
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    sensors = hass.states.async_all("sensor")
    binary_sensors = hass.states.async_all("binary_sensor")
    assert len(sensors) >= 6, [s.entity_id for s in sensors]
    assert len(binary_sensors) >= 2, [s.entity_id for s in binary_sensors]
    assert any(state.state == "BOS to PIT" for state in sensors)
    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_config_flow_password_is_masked(hass: HomeAssistant):
    """Ensure the IMAP password cannot be entered in a plaintext field."""
    from homeassistant.helpers.selector import TextSelectorType
    from homeassistant.const import CONF_PASSWORD
    flow = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    assert flow["type"].value == "form"
    schema = flow["data_schema"]
    # Iterate schema keys by their underlying field names, not marker objects.
    password_selector = next(value for key, value in schema.schema.items() if str(key) == CONF_PASSWORD)
    assert password_selector.config["type"] == TextSelectorType.PASSWORD


async def test_config_flow_creates_entry_with_mocked_imap(hass: HomeAssistant):
    """Exercise the full configuration form without connecting to a real server."""
    sample = {
        CONF_HOST: "imap.example.test",
        CONF_PORT: 993,
        CONF_USERNAME: "synthetic@example.test",
        CONF_PASSWORD: "test-only-password",
        "folder": "Travel",
        "scan_interval": 30,
    }
    flow = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    with patch("custom_components.travel_tracker.config_flow.test_mailbox"):
        result = await hass.config_entries.flow.async_configure(
            flow["flow_id"], user_input=sample
        )
    assert result["type"].value == "create_entry"
    assert result["data"]["folder"] == "Travel"


async def test_config_flow_rejects_invalid_mocked_credentials(hass: HomeAssistant):
    """A bad IMAP login should produce a form error without exposing the password."""
    import imaplib

    sample = {
        CONF_HOST: "imap.example.test",
        CONF_PORT: 993,
        CONF_USERNAME: "synthetic@example.test",
        CONF_PASSWORD: "test-only-password",
        "folder": "Travel",
        "scan_interval": 30,
    }
    flow = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    with patch(
        "custom_components.travel_tracker.config_flow.test_mailbox",
        side_effect=imaplib.IMAP4.error("bad mock credentials"),
    ):
        result = await hass.config_entries.flow.async_configure(
            flow["flow_id"], user_input=sample
        )
    assert result["type"].value == "form"
    assert result["errors"]["base"] == "invalid_auth_or_folder"
    assert "test-only-password" not in str(result)



async def test_existing_mail_and_packages_offered_as_explicit_option(
    hass: HomeAssistant,
):
    """The settings reuse is opt-in, and the linked entry contains no secrets."""
    from custom_components.travel_tracker.const import (
        CONF_LINKED_ENTRY_ID, CONF_SOURCE, SOURCE_LINKED,
    )

    source = MockConfigEntry(
        domain="mail_and_packages",
        title="Mail and Packages",
        data={
            CONF_HOST: "imap.mail.example",
            CONF_PORT: 993,
            CONF_USERNAME: "synthetic@example.test",
            CONF_PASSWORD: "source-only-secret",
            "folder": "Packages",
        },
    )
    source.add_to_hass(hass)

    menu = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    assert menu["type"].value == "menu"
    assert "linked" in menu["menu_options"]
    assert "imap" in menu["menu_options"]

    form = await hass.config_entries.flow.async_configure(
        menu["flow_id"], user_input={"next_step_id": "linked"}
    )
    assert form["type"].value == "form"
    entry = await hass.config_entries.flow.async_configure(
        menu["flow_id"],
        user_input={
            CONF_LINKED_ENTRY_ID: source.entry_id,
            "folder": "Travel",
            "scan_interval": 30,
        },
    )
    assert entry["type"].value == "create_entry"
    assert entry["data"][CONF_SOURCE] == SOURCE_LINKED
    assert entry["data"][CONF_LINKED_ENTRY_ID] == source.entry_id
    assert entry["data"]["folder"] == "Travel"
    assert "source-only-secret" not in str(entry["data"])
    assert CONF_PASSWORD not in entry["data"]


async def test_linked_account_reuses_settings_with_separate_read_only_scan(
    hass: HomeAssistant,
):
    """Linked mode uses source credentials at runtime without duplicating them."""
    from custom_components.travel_tracker.const import (
        CONF_LINKED_ENTRY_ID, CONF_SOURCE, SOURCE_LINKED,
    )

    source = MockConfigEntry(
        domain="mail_and_packages",
        title="Mail and Packages",
        data={
            CONF_HOST: "imap.mail.example",
            CONF_PORT: 993,
            CONF_USERNAME: "synthetic@example.test",
            CONF_PASSWORD: "source-only-secret",
            "folder": "Packages",
        },
    )
    source.add_to_hass(hass)
    linked = MockConfigEntry(
        domain=DOMAIN,
        title="Travel Tracker (Mail and Packages settings)",
        data={
            CONF_SOURCE: SOURCE_LINKED,
            CONF_LINKED_ENTRY_ID: source.entry_id,
            "folder": "Travel",
            "scan_interval": 30,
        },
    )
    linked.add_to_hass(hass)
    with patch(
        "custom_components.travel_tracker.coordinator.fetch_bookings",
        return_value=[],
    ) as fetch:
        assert await hass.config_entries.async_setup(linked.entry_id)
        await hass.async_block_till_done()
    assert fetch.call_count >= 1
    args = fetch.call_args.args
    assert args[:5] == (
        "imap.mail.example", 993, "synthetic@example.test",
        "source-only-secret", "Travel",
    )
    assert CONF_PASSWORD not in linked.data
    assert await hass.config_entries.async_unload(linked.entry_id)


async def test_missing_mail_and_packages_account_fails_closed(
    hass: HomeAssistant,
):
    """A removed source should never fall back to stored or guessed credentials."""
    import pytest
    from homeassistant.helpers.update_coordinator import UpdateFailed
    from custom_components.travel_tracker.coordinator import TravelCoordinator
    from custom_components.travel_tracker.const import (
        CONF_LINKED_ENTRY_ID, CONF_SOURCE, SOURCE_LINKED,
    )

    linked = MockConfigEntry(
        domain=DOMAIN,
        title="Travel Tracker (Mail and Packages settings)",
        data={
            CONF_SOURCE: SOURCE_LINKED,
            CONF_LINKED_ENTRY_ID: "no-longer-installed",
        },
    )
    with patch(
        "custom_components.travel_tracker.coordinator.fetch_bookings"
    ) as fetch:
        with pytest.raises(UpdateFailed, match="unavailable"):
            await TravelCoordinator(hass, linked)._async_update_data()
    fetch.assert_not_called()
