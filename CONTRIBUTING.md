# Contributing to Travel Tracker

This is an early beta and is not ready for users' actual confirmation emails.

1. Create a feature branch based on the Travel Tracker development branch.
2. Write tests using *invented* booking details. Do not commit real emails, PNRs, confirmation codes, identity data, boarding passes, loyalty numbers or payment details.
3. Keep email parsing local and ensure only approved itinerary fields reach Home Assistant sensors and logs.
4. Run the simulated mailbox test suite and the Home Assistant smoke test before requesting a merge.
5. Preserve the MIT LICENSE and upstream Mail and Packages attribution.

Note that a successful simulated email parse does not establish production support for an airline's actual emails.
