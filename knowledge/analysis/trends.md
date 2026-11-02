---
type: Analysis
title: Trends
description: Lines up weekly profile summaries by roster date and shows 23 measures side by side with the change since the previous run.
resource: ../../scripts/analysis_trends.py
tags: [analysis, population]
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:10:00Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:10:00Z }
sources:
  - id: analysis-l177
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/docs/ANALYSIS.md?plain=1#L177-L183
    title: docs/ANALYSIS.md lines 177-183, before the OKF migration
    last_modified: 2026-09-26T02:01:31Z
    author: claude-code/claude-opus-5-5
---

`scripts/analysis_trends.py` lines up weekly [profile](population-profile.md) summaries (and the September 23
baseline) by roster date and shows 23 measures side by side with the change since the
previous run: people held, time held, case status, charge grades, money bonds,
detainers, violation charges, court dates, and recent daily bookings and releases.
Rosters from different times of day can differ; each column names its roster time.

Latest weekly run (September 30, 2026): three columns (the September 23 baseline,
September 25, and September 30); people held rose by 36 since September 25.
