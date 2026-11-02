---
type: Decision
title: Collect IML detail pages in bounded batches
description: IML detail pages are collected in bounded batches after the population runs, aiming for a daily refresh with visible coverage and per-record check times.
tags: [iml-details]
decided: 2026-09-19
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T01:54:59Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:06:36Z }
sources:
  - id: decisions-l43
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/DECISIONS.md?plain=1#L43-L44
    title: DECISIONS.md lines 43-44, before the OKF migration
    last_modified: 2026-09-22T16:39:10Z
---

Collect IML detail pages in bounded batches after the population runs, aiming for daily
refresh. Show actual coverage and per-record check times.

Related: [IML record pages](../sources/iml-record-pages.md), [Case-data collection](../architecture/case-data-collection.md).
