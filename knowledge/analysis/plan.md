---
type: Plan
title: Further analysis plan
description: Staged plan to turn the archive into measures over time, from the booking panel to length of stay, money bond, court linkage, and trends.
tags: [analysis]
date: 2026-09-23
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T01:54:59Z }
sources:
  - id: plan-l254
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/PLAN.md?plain=1#L254-L284
    title: PLAN.md lines 254-284, before the OKF migration
    last_modified: 2026-09-23T07:42:39Z
    author: claude-code/claude-opus-5-5
---

The first [population profile](population-profile.md) describes who is held on one day.
The following steps turn the archive into measures of what happens over time. All
analysis reads local archive copies, keeps person-level files under ignored `data/`,
and publishes aggregates only.

1. **[Booking panel](booking-panel.md) (now).** Replay committed roster and detail observations into one
   private row per booking: first/last seen, presence spans, listed release date and
   when it appeared, outcome (held, released, disappeared without a release date),
   and dated changes in commitment date, case status, charge grade, bond, detainers,
   and next court date. Mark bookings present at coverage start as left-truncated and
   open bookings as censored. Record missed collection slots, including the recurring
   [07:00 UTC roster failures](../source-quality/iml-0700-roster-shrinks.md). Rebuild each archived IML population from the panel and
   require an exact match before later steps use it.
2. **[Length of stay](length-of-stay.md) for new bookings (first readout ~30 days).** Follow bookings first
   seen after coverage began. Estimate time to release with Kaplan-Meier curves by
   charge grade, bond type/amount, and detainer status, and report how many very short
   stays fall between collections.
3. **[Money bond](money-bond.md) and pretrial detention (~4-6 weeks).** Use detail changes to find bond
   reductions, increases, and new bonds; measure time from a change to release and
   waits for people held on low bonds. Keep bond status separate from court outcomes.
4. **[Court linkage](court-linkage.md) (~4-8 weeks).** Join pending hearings by booking number and
   calendars/indictments by exact case number, never by name. Measure match rates
   first, then court-date postponements and time from commitment to indictment for
   people without a sentenced case. [Dispositions remain unavailable](../source-quality/xfer-dispositions-empty.md).
5. **Trends and reporting (ongoing).** Rerun the profile [weekly](weekly-run.md) from fresh snapshots,
   track [composition over time](trends.md), [reconcile IML against XFER](source-reconciliation.md),
   add [repeat-booking measures](rebooking.md)
   after about 90 days of coverage, and keep a short record of [source-quality issues](../source-quality/index.md).

Order: 1, then 5's weekly run, then 2-4 as data accumulates.
