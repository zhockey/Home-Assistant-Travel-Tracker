# Travel Tracker for Home Assistant ✈️

**Beta development branch. Not suitable for production Home Assistant.**

Travel Tracker scans a dedicated IMAP mailbox/folder **locally**, extracts simple travel itinerary fields, groups nearby reservations into tentative trips, and publishes Home Assistant sensors.

## Current functionality

- Example-format American Airlines, Hilton, and National rental confirmations (not comprehensive provider support).
- 6 sensors: next trip, next flight, next hotel, next rental car, days until next trip, upcoming trips.
- 2 binary sensors: travel today and travel within the next 7 days.
- Secure IMAP (TLS, port 993 default), read-only mailbox selection, and `BODY.PEEK[]`.
- No raw email or attachments persisted by Travel Tracker. No confirmation numbers, ticket numbers, payment details or loyalty numbers intentionally retained.
- No analytics processing outside your HA instance; mailbox connection itself is to your mail provider.
- Up to 300 of the most recent messages from the last 365 days scanned per refresh; default refresh every 30 minutes.

## Installation: only in an isolated test Home Assistant

Do **not** install this branch over an existing integration or a live HA instance yet.
A disposable Home Assistant install is the supported test target while we validate emails and migrations.

1. In your isolated HA config directory create `custom_components/travel_tracker` with the integration's files.
2. Restart the test HA instance, then use **Settings → Devices & services → Add integration → Travel Tracker**.
3. Configure your IMAP host, port, username, app password, dedicated folder and poll interval.
4. Use a dedicated, non-sensitive test mailbox. Do not paste real credentials into GitHub issues or tests.

## Run isolated tests

```bash
python -m pip install pytest
python -m pytest --noconftest -q tests/test_travel_parser.py tests/test_full_sandbox.py
```

GitHub Actions runs these tests, plus a test using the actual Home Assistant test harness and a mocked mailbox. See `.github/workflows/travel-ha-sandbox.yml`.

## Known limitations

- The email parser expects explicit labels and dates in a few example formats, not production provider templates.
- Trips are grouped by overlapping/adjacent dates, so unrelated trips can be grouped incorrectly.
- Each parsed email currently yields one booking; multi-segment flights aren't fully supported.
- Cancellations, schedule changes, time zones, boarding data, live flight status, OAuth login and reauthentication need additional work.
- Mailbox access is bounded by age and message count. Older confirmations can be missed.
- Travel details are stored as Home Assistant entity states and may be retained by HA Recorder and backups.
- Sender-domain recognition is **not** sender authentication (SPF/DKIM).

## Project links

- [Development PR](https://github.com/zhockey/Home-Assistant-Travel-Tracker/pull/3)
- [Beta notes](docs/TRAVEL_TRACKER_BETA.md)
- [Issue tracker](https://github.com/zhockey/Home-Assistant-Travel-Tracker/issues)

## Credit and license

Originally forked from [Mail and Packages](https://github.com/moralmunky/Home-Assistant-Mail-And-Packages) by Moralmunky and its contributors. The original MIT license and copyright attribution remain in [LICENSE](LICENSE). The current travel-specific runtime is a rewrite, not a published release.
