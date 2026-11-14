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
