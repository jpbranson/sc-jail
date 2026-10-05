---
type: Source Quality Issue
title: Roster lists recently released bookings
description: The IML roster also lists recently released bookings with their release date, so the population counts only blank or future release dates.
tags: [iml, population, data-quality]
affects: IML roster
first_seen: 2026-09-19
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:10:00Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:10:00Z }
sources:
  - id: source-quality-l15
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/docs/SOURCE_QUALITY.md?plain=1#L15-L15
    title: docs/SOURCE_QUALITY.md lines 15-15, before the OKF migration
    last_modified: 2026-09-26T02:01:31Z
    author: claude-code/claude-opus-5-5
---

# Issue

The roster also lists recently released bookings with their release date.

# Latest evidence

In the Sept 30 13:30 UTC roster, 241 of the 3,306 bookings listed had a release date on or
before that day and were not counted as held (weekly reconciliation). 200 of 3,257 roster rows
had a release date on Sept 23.

# Handling

[Population](../measures/iml-population.md) counts only blank or future release dates.
