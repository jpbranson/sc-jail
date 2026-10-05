---
type: Source Quality Issue
title: IML-held bookings missing from XFER
description: About 10 IML-held bookings are missing from the XFER workbook at any time, not explained by its two-hour refresh.
tags: [iml, xfer, data-quality]
affects: IML vs XFER
first_seen: 2026-09-19
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T01:54:59Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:10:00Z }
sources:
  - id: source-quality-l29
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/docs/SOURCE_QUALITY.md?plain=1#L29-L29
    title: docs/SOURCE_QUALITY.md lines 29-29, before the OKF migration
    last_modified: 2026-10-04T17:51:48Z
    author: claude-code/claude-opus-5-5
---

# Issue

About 10 IML-held bookings are missing from the XFER workbook at any time, not explained by the
[two-hour refresh](./xfer-two-hour-regeneration.md).

# Latest evidence

8 in the Sept 30 13:34 UTC comparison (0 first listed in the prior two hours; 6 at `JMS`, 2 at
`JAILEAST`); daily medians 8 to 11 through Sept 30.

# Handling

Reported by the weekly [reconciliation](../analysis/source-reconciliation.md); too few to affect
totals.
