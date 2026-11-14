# Travel Tracker v0.2 beta: engineering notes

**Status:** pre-release draft. **Do not install on production Home Assistant yet.**

## What exists now

- Minimal custom integration under `custom_components/travel_tracker/`.
- Secure IMAP (TLS) setup via Home Assistant, with a password-style field.
- Read-only folder selection and `BODY.PEEK[]` to avoid marking messages as read.
- Bound scanning: 365 days of mail, at most 300 recent messages per refresh, up to 512 KiB per parsed message.
- Parsers for **synthetic example formats**, not comprehensive live provider templates: American Airlines, Hilton, National.
- In-memory booking parsing and same-day updates using itinerary identity, without storing confirmation IDs.
- Basic date-adjacency trip grouping.
- Six HA sensors and two binary sensors. Home Assistant Recorder may retain trip data.
- Cancellation notices do not create new bookings. **They do not yet erase an earlier confirmed booking.**

## Tests

Run isolated tests without Home Assistant or mail credentials:

```sh
python -m pip install pytest
python -m pytest --noconftest -q tests/test_travel_parser.py tests/test_full_sandbox.py
```

GitHub Actions:
- `travel-parser-sandbox.yml` runs pure parser checks on Python 3.12 and 3.13.
- `travel-ha-sandbox.yml` runs fake-IMAP end-to-end checks and a Home Assistant 2026.11 runtime test (Python 3.14) with no real email.
- The actual HA test covers entity creation and unload plus UI configuration form, mock authentication failure, and password field masking.

## Privacy model

Travel Tracker itself processes email locally and does not write raw messages or attachments to disk. It stores credentials using Home Assistant's config-entry storage, so HA backups and machine administrators must still be protected. It exposes trip details in entity attributes; Home Assistant Recorder, backups and connected dashboards can retain that information.

An IMAP username, app password and TLS connection to the email provider are required. Sender-domain checking is only a *parsing heuristic*, not a guarantee of sender authenticity. No provider logins or personal booking emails are stored in the public repository.

## Known problems before external beta

- Gmail and Microsoft accounts may require additional authentication or OAuth. IMAP app passwords are not universally supported.
- Actual provider HTML templates are not yet covered by test examples.
- Multi-leg flights within a single message are not supported.
- A date change to a different day may appear as a new booking; same-day time updates do reconcile.
- Cancellation notices with full itinerary do **not** remove older confirmation emails.
- The trip builder groups by overlapping/adjacent dates and can merge unrelated trips.
- Travel history and message scanning are limited by the lookback and message caps.
- No live flight status or gate data, reauthentication flow, or robust migration from previous fork versions.
- No system-level end-user test on a complete disposable Home Assistant installation.

See [release checklist](RELEASE_CHECKLIST.md) before merging.
