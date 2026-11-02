---
type: Metric
title: XFER bookings
description: The XFER measure is the count of distinct booking numbers in the XFER jail workbook, which has several charge rows per booking.
resource: https://xfer.shelbycountytn.gov/SCSO-InJail/SCSO-InJail.xls
tags: [xfer, population]
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T01:54:59Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:06:36Z }
sources:
  - id: readme-l11
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/README.md?plain=1#L11-L12
    title: README.md lines 11-12, before the OKF migration
    last_modified: 2026-09-22T16:39:10Z
---

# Definition

Distinct booking numbers in `/SCSO-InJail/SCSO-InJail.xls`. A person
can have several charge rows and potentially several bookings.

Measured from the [XFER jail workbook](../sources/xfer-jail-workbook.md), which has
[one row per charge](../source-quality/xfer-charge-rows.md). It is counted separately from the
[IML population](iml-population.md) of distinct permanent IDs.
