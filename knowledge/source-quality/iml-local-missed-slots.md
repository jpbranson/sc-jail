---
type: Source Quality Issue
title: Missed roster slots before the cloud cutover
description: Before the September 22 cloud cutover, local collection missed roughly one IML roster slot in five.
tags: [iml, local, data-quality]
affects: IML roster
first_seen: 2026-09-19
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:10:00Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:10:00Z }
sources:
  - id: source-quality-l16
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/docs/SOURCE_QUALITY.md?plain=1#L16-L16
    title: docs/SOURCE_QUALITY.md lines 16-16, before the OKF migration
    last_modified: 2026-09-26T02:01:31Z
    author: claude-code/claude-opus-5-5
---

# Issue

Before the Sept 22 [cloud cutover](../deployments/2026-09-22-cutover.md), local collection missed
roughly one slot in five.

# Latest evidence

45 missed slots by Sept 23, all but one before cutover. The Sept 30 panel puts 44 of its 53
missed slots before the cutover.

# Handling

[Adjacent-slot arrivals/departures](../measures/arrivals-departures.md) across gaps stay blank;
[daily flows](../analysis/population-profile.md) use first-seen and release dates instead.
