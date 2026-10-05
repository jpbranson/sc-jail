---
type: Source Quality Issue
title: Repeated column headings in the jail workbook
description: The XFER jail workbook repeats its column headings between printed pages; the parser skips them and historical observations were repaired.
tags: [xfer, data-quality]
affects: XFER jail workbook
first_seen: 2026-09-19
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T01:54:59Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:10:00Z }
sources:
  - id: source-quality-l19
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/docs/SOURCE_QUALITY.md?plain=1#L19-L19
    title: docs/SOURCE_QUALITY.md lines 19-19, before the OKF migration
    last_modified: 2026-09-26T02:01:31Z
    author: claude-code/claude-opus-5-5
---

# Issue

The [workbook](../sources/xfer-jail-workbook.md) repeats its column headings between printed pages.

# Latest evidence

20,168 heading rows removed across 39 historical observations.

# Handling

Parser skips them; historical observations [repaired](../operations/repair-xfer-headings.md) with
backups kept. See the [decision](../decisions/2026-09-19-remove-xfer-repeated-headings.md).
