---
type: Decision
title: Base time-based analysis on a validated booking panel
description: Time-based analysis uses a booking panel that must reproduce every archived IML population, keeping ID and release-date changes as timed histories.
tags: [analysis, iml]
decided: 2026-09-23
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T01:54:59Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:06:36Z }
sources:
  - id: decisions-l95
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/DECISIONS.md?plain=1#L95-L98
    title: DECISIONS.md lines 95-98, before the OKF migration
    last_modified: 2026-09-23T07:42:39Z
    author: claude-code/claude-opus-5-5
---

Base time-based analysis on a booking panel that must reproduce every archived IML population.
Keep permanent-ID and release-date changes as timed histories rather than final values, and
count daily movement from first-seen and listed release dates rather than adjacent-slot
changes, which skip collection gaps.

Related: [Booking panel](../analysis/booking-panel.md), [Arrivals and departures](../measures/arrivals-departures.md).
