---
type: Source Quality Issue
title: Record pages refreshed about daily
description: IML record pages are refreshed about daily, so a detail change is dated when it is seen, not when it happened.
tags: [iml-details, data-quality]
affects: IML details
first_seen: 2026-09-19
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:10:00Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:10:00Z }
sources:
  - id: source-quality-l17
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/docs/SOURCE_QUALITY.md?plain=1#L17-L17
    title: docs/SOURCE_QUALITY.md lines 17-17, before the OKF migration
    last_modified: 2026-09-26T02:01:31Z
    author: claude-code/claude-opus-5-5
---

# Issue

[Record pages](../sources/iml-record-pages.md) are refreshed about daily, so a change is dated
when it is seen, not when it happened. A backlog after the Sept 23 [refresh-lead
change](../deployments/2026-09-23-detail-refresh-fix.md) kept detail freshness failing for a time.

# Latest evidence

3,291 of 3,291 eligible pages fresh at 01:47 UTC Oct 5 (oldest check Oct 4 05:47 UTC), after
the backlog from the Oct 4 [blank permanent ID](iml-blank-permanent-id.md) outage cleared
(live `/api/coverage`). 3,308 of 3,308 were fresh at 00:05 UTC Sept 26.

# Handling

Detail-based timing ([bond changes](../analysis/money-bond.md), [court-date
moves](../analysis/court-linkage.md)) has up to about a day of uncertainty.
