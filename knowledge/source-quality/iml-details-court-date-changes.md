---
type: Source Quality Issue
title: Court dates change after the hearing passes
description: Most court-date changes appear after a listed date passes, so daily refresh cannot tell a continuance from a scheduled next step.
tags: [iml-details, courts, data-quality]
affects: IML details
first_seen: 2026-09-25
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:10:00Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:10:00Z }
sources:
  - id: source-quality-l27
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/docs/SOURCE_QUALITY.md?plain=1#L27-L27
    title: docs/SOURCE_QUALITY.md lines 27-27, before the OKF migration
    last_modified: 2026-09-26T02:01:31Z
    author: claude-code/claude-opus-5-5
---

# Issue

Court dates rarely move before the hearing arrives; most changes appear after a listed date passes.

# Latest evidence

Sept 19 to 30: 1,891 changes where a passed date was replaced (median 9 days to the next date), 3
resets seen before the hearing date (Sept 30 court linkage). Sept 19 to 25: 1,212 and 1.

# Handling

Daily refresh cannot separate a continuance from a scheduled next step; report passed-and-replaced
dates, not "postponements". See [court linkage](../analysis/court-linkage.md).
