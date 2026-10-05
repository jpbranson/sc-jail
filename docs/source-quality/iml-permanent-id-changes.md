---
type: Source Quality Issue
title: Permanent person ID can change
description: IML can reassign a booking's permanent person ID, so counts use the ID in effect at each moment.
tags: [iml, population, repeat-visits, data-quality]
affects: IML roster
first_seen: 2026-09-19
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:10:00Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:10:00Z }
sources:
  - id: source-quality-l12
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/docs/SOURCE_QUALITY.md?plain=1#L12-L12
    title: docs/SOURCE_QUALITY.md lines 12-12, before the OKF migration
    last_modified: 2026-09-26T02:01:31Z
    author: claude-code/claude-opus-5-5
---

# Issue

A booking's permanent person ID can change.

# Latest evidence

182 of 4,174 bookings by Sept 30 (weekly panel); 54 of 3,584 by Sept 23.

# Handling

[Panel](../analysis/booking-panel.md) keeps a timed ID history; counts use the ID in effect at each
moment. [Repeat-visit counts](../measures/repeat-visits.md) exclude conflicting IDs.
