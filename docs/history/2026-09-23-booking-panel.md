---
type: Milestone
title: Booking panel result
description: The September 23, 2026 booking panel replayed 333 roster observations into 3,584 bookings and reproduced every archived IML population.
tags: [history, analysis]
date: 2026-09-23
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T01:54:59Z }
sources:
  - id: plan-l286
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/PLAN.md?plain=1#L286-L297
    title: PLAN.md lines 286-297, before the OKF migration
    last_modified: 2026-09-23T07:42:39Z
    author: claude-code/claude-opus-5-5
---

Implemented `scripts/build_panel.py`. It replays the September 23 snapshot's 333 roster
observations into 3,584 booking rows with presence spans, release-date history,
permanent-ID history, outcomes, truncation flags, and dated detail-fact changes. Every
archived IML population is reproduced exactly; the build fails on any mismatch.

Validation exposed two source behaviors the first design missed: 54 bookings changed
[permanent ID](../source-quality/iml-permanent-id-changes.md), and one release date was [withdrawn and relisted](../source-quality/iml-release-date-relisted.md). Both are now kept as
timed histories. The [07:00 UTC roster slot](../source-quality/iml-0700-roster-shrinks.md) failed on September 20, 21, and 23 while the
roster shrank mid-scan. See [analysis](../analysis/booking-panel.md) for fields and
results. Next: schedule the weekly profile (step 5), then steps 2-4 as data accumulates
(see the [analysis plan](../analysis/plan.md)).
