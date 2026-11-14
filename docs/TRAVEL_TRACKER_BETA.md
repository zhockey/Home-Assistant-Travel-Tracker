# Travel Tracker v0.2 beta

This is a development preview, not yet a HACS release. The old Mail and Packages
fork contained in the repository still has legacy tests, assets and workflows.
The integration path `custom_components/travel_tracker` is being replaced with a
travel-specific implementation.

## What it does

- Connects to a TLS IMAP mailbox, selecting the configured folder read-only.
- Reads recent messages with `BODY.PEEK[]` and never marks them read.
- Parses *example-format* American Airlines, Hilton, and National confirmation emails.
- Exposes six HA sensors and two binary sensors from a deduplicated itinerary snapshot.
- Does not store raw mail, loyalty details, payment numbers or booking references.
- Limits mailbox scans to 300 recent messages within the last 365 days.
- Supports a 15 to 240 minute polling interval, default 30 minutes.

## Standalone validation

```sh
python -m pip install pytest
python -m pytest --noconftest -q tests/test_travel_parser.py tests/test_full_sandbox.py
```

No Home Assistant, real email account or network is needed for these tests.

## Disposable HA runtime smoke test

Use Python 3.13 and the `pytest-homeassistant` package matching Home Assistant.
The file `tests/test_travel_ha_runtime.py` exercises an actual HA config entry,
coordinator, platform loading, entities and unload without a real mailbox. The
`Travel Tracker HA sandbox` workflow runs it on GitHub-hosted runners.

## Cautions

- **Do not install over your production HA integration yet.**
- **Do not merge before the HA sandbox passes and provider templates are verified.**
- Home Assistant keeps IMAP credentials in its protected config-entry storage; use
  an app password and a dedicated travel folder/mailbox.
- Dates and trip cities *will* be visible in HA state history and backups.
- The parser trusts matching sender domains for format recognition but does
  not authenticate SMTP sender identity or verify SPF/DKIM.
- There is no support yet for cancellations, date changes, true round-trip
  grouping, OAuth-only mail providers, or live flight data.

Original Mail and Packages MIT attribution remains in the repository LICENSE.
