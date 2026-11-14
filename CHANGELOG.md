# Changelog

## Unreleased: Travel Tracker v0.2 beta

- Replaced the Mail and Packages runtime with Home Assistant travel sensors,
  read-only IMAP polling and a local itinerary parser.
- Added initial American Airlines, Hilton and National *example-format* parsing.
- Added preliminary trip grouping and same-day schedule-update deduplication.
- Added privacy safeguards and tests for misplaced booking codes.
- Added simulated email and real Home Assistant test harness workflows.
- Removed inherited shipping-specific code, fixtures, translations, images and CI.
- Updated HACS metadata, docs and original-project attribution.

**Not production-ready:** unsupported provider formats, cancellations,
rebooking and multi-leg flight itineraries remain development priorities.
