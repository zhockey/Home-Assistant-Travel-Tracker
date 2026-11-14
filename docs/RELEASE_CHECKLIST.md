# Travel Tracker release checklist

## Development checks
- [x] New travel-specific Python runtime, not a shipping tracker
- [x] Remove inherited shipping tests, documentation, translations and assets
- [x] Preserve original Mail and Packages MIT attribution
- [x] Isolated parser tests for three provider *example formats*
- [x] Mock IMAP, including read-only folder and non-marking fetch
- [x] Home Assistant 2026.11 test harness creates and unloads entities
- [x] Home Assistant config form uses password-style selector
- [x] Test no booking codes or card details in parsed output
- [x] Basic updated same-day flight notifications replace earlier time
- [ ] A full disposable Home Assistant UI install (not only the test harness)
- [ ] Provider-specific realistic redacted HTML/text email templates
- [ ] Cancellations and date changes reconcile against old confirmations
- [ ] Multi-leg flights and crossing time zones
- [ ] Correct trip grouping for simultaneous/unrelated travel
- [ ] Reauthentication and credentials rotation
- [ ] Failure recovery when an IMAP mailbox disappears or messages are deleted
- [ ] Home Assistant manifest/HACS validation on a tagged beta
- [ ] Check dashboard states, Recorder, long attributes, and rate limiting
- [ ] Human review of security and migration

## Publishing policy

Keep PR #3 draft until required tests pass. Do not publish a release or merge to
the default branch before completing the relevant items above. Use invented test
reservations and remove any identifying information from issue reports.

## Manual pilot process

On a disposable Home Assistant instance: install Travel Tracker under
`custom_components/travel_tracker`, reboot, configure a *test-only* mailbox,
send synthetic plain text / HTML confirmations, verify eight entities, reload
the integration, then introduce a malformed email and simulate a server outage.

Only after that should we discuss installing it on a real Home Assistant.
