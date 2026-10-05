---
type: Source Quality Issue
title: 07:00 UTC roster shrinks mid-scan
description: The 07:00 UTC (2 a.m. Central) IML roster can fail completeness checks because its total falls during every attempt.
tags: [iml, population, data-quality]
affects: IML roster
first_seen: 2026-09-20
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:10:00Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:10:00Z }
sources:
  - id: source-quality-l11
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/docs/SOURCE_QUALITY.md?plain=1#L11-L11
    title: docs/SOURCE_QUALITY.md lines 11-11, before the OKF migration
    last_modified: 2026-09-26T02:01:31Z
    author: claude-code/claude-opus-5-5
---

# Issue

The 07:00 UTC (2 a.m. Central) roster fails completeness checks because its total falls during
every attempt, apparently while released records are purged.

# Latest evidence

Failed Sept 20, 21, and 23 only: the Sept 30 panel and collector logs show no 07:00 failure
from Sept 24 to Oct 5, apart from Oct 4, when every scan from 05:22 to 16:15 UTC was rejected
for an unrelated [blank permanent ID](iml-blank-permanent-id.md). The 07:15 slot succeeded
each time the 07:00 slot failed. It
triggered the [population alert](../operations/monitoring-and-limits.md) once (Sept 23
07:05–07:20 UTC).

# Handling

Keep the missed slot; never accept a shrinking roster as a population change. Missed slots are
listed in each [panel's](../analysis/booking-panel.md) `missing-slots.json`.
