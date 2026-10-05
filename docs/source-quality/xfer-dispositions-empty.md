---
type: Source Quality Issue
title: Empty dispositions folder
description: The XFER dispositions folder has no files, so court outcomes are unavailable and bond status is not treated as a disposition.
tags: [xfer-courts, courts, data-quality]
affects: XFER courts
first_seen: 2026-09-19
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:10:00Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:10:00Z }
sources:
  - id: source-quality-l23
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/docs/SOURCE_QUALITY.md?plain=1#L23-L23
    title: docs/SOURCE_QUALITY.md lines 23-23, before the OKF migration
    last_modified: 2026-09-26T02:01:31Z
    author: claude-code/claude-opus-5-5
---

# Issue

The [dispositions folder](../sources/xfer-court-reports.md) has no files.

# Latest evidence

Still empty at the Oct 5 01:45 UTC collection, when the other three folders listed 34 files
(live `/api/coverage`); also empty on Sept 26 at 00:15 UTC, when they listed 36.

# Handling

Court outcomes are unavailable; bond status is not treated as a disposition.
