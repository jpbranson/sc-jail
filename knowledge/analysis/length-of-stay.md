---
type: Analysis
title: Length of stay
description: Kaplan-Meier time from commitment to listed release for bookings first listed after collection began, grouped by the filled-in record page.
resource: ../../scripts/length_of_stay.py
tags: [analysis, iml-details]
stale_after: 2026-10-19T00:00:00Z
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:10:00Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:10:00Z }
sources:
  - id: analysis-l203
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/docs/ANALYSIS.md?plain=1#L203-L219
    title: docs/ANALYSIS.md lines 203-219, before the OKF migration
    last_modified: 2026-09-26T02:01:31Z
    author: claude-code/claude-opus-5-5
---

`scripts/length_of_stay.py` follows bookings first listed after collection began, from the
IML commitment date to the listed release date in whole days, with Kaplan-Meier estimates
([`src/sc_jail/survival.py`](../../src/sc_jail/survival.py)). Held bookings are censored at the latest roster; bookings that
leave without a release date are censored when last seen. A commitment date more than a
week before a booking was first listed marks an older stay, which is excluded.

Groups come from the record page [after it fills in](../source-quality/iml-details-fill-in.md), not the first page fetched
([decision](../decisions/2026-09-26-filled-in-record-page.md)): charges
and bond entries appear a median of 6.5 hours after first listing, and a bond decision
(any bond type other than "Not Assessed") a median of 20.5 hours after. Charge grade and
detainer use the first page with case entries; bond situation and amount use the first
page with a bond decision. Record pages keep being fetched while released bookings stay
listed (a median of 64 hours), so this does not require someone to remain held.

Preliminary (6 days, September 25): 526 new bookings, 256 released; median stay 3 days;
71% still held after 1 day and 40% after 3 days. The first readout needs 30 days.

Latest weekly run (September 30, 2026; 11 days): 881 new bookings, 499 released; median stay
3 days; 73% still held after 1 day and 46% after 3 days. Released bookings stayed listed a
median of 72 hours.
