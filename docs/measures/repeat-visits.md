---
type: Metric
title: Repeat visits and time between visits
description: Distinct IML bookings per permanent person ID across the full archive, and calendar days from one booking's release to the next commitment.
tags: [repeat-visits, iml, dashboard]
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T01:54:59Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:06:36Z }
sources:
  - id: repeat-visits-l1
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/docs/REPEAT_VISITS.md?plain=1#L1-L31
    title: docs/REPEAT_VISITS.md lines 1-31, before the OKF migration
    last_modified: 2026-10-04T16:36:20Z
---

# Repeat visits

The dashboard uses the complete archived IML roster history to count distinct
booking numbers for each permanent person ID. A booking is counted once even if
it appears in hundreds of polls, disappears, or reappears after a collection gap.
Released bookings remain part of the observed history. Visits never captured by
this archive are unknown; these counts are not a lifetime history or a recidivism
rate. XFER does not provide a permanent person ID, so it is not used to link people.

The repeat section uses all archived observations, independently of the population
time-range selector. It shows people with at least two distinct bookings, the
number of bookings for those people, the number beyond their first booking, and
the distribution of visits per returning person. Single-booking people and the
total number of observed bookings are also shown.

# Time between visits

Time between visits is the number of calendar days from the earlier booking's
IML release date to the next booking's IML commitment date. Commitment dates come
from archived individual detail pages. They are dates, not precise admission or
release times. A same-day interval is zero calendar days. Malformed dates and
commitment dates after the detail observation's Memphis date are treated as
missing, not as measured intervals.

Bookings are ordered by commitment date. If any commitment date for a person's
observed bookings is missing, that person's intervals remain unmeasured rather
than bridging an unknown visit. Intervals with a missing prior release date are
also unmeasured. Overlapping dates, a release before commitment, or equal
commitment dates with ambiguous booking order are excluded from the histogram.
The dashboard separately reports measured, missing-date, and invalid/ambiguous
interval counts. Conflicting permanent IDs exclude the affected people's bookings.
A booking listed before IML assigns its permanent ID keeps its first-seen time (so it
counts in daily first-seen bookings) but belongs to no person until an ID appears.

# Related

- How the counts are computed and refreshed: [repeat-visit registry](../architecture/repeat-visit-registry.md).
- Source behaviors: [permanent IDs can change](../source-quality/iml-permanent-id-changes.md) and
  [bookings listed with a blank permanent ID](../source-quality/iml-blank-permanent-id.md).
- Commitment dates come from [IML record pages](../sources/iml-record-pages.md).
