---
type: Analysis
title: Source reconciliation
description: Compares each XFER jail workbook version with the nearest IML roster by exact booking number, including shared fields and bookings only one source lists.
resource: ../../scripts/reconcile_sources.py
tags: [analysis, iml, xfer, data-quality]
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T01:54:59Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:10:00Z }
sources:
  - id: analysis-l185
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/docs/ANALYSIS.md?plain=1#L185-L201
    title: docs/ANALYSIS.md lines 185-201, before the OKF migration
    last_modified: 2026-10-04T17:51:48Z
    author: claude-code/claude-opus-5-5
---

`scripts/reconcile_sources.py` compares each [XFER jail workbook](../sources/xfer-jail-workbook.md) version
([regenerated about every two hours](../source-quality/xfer-two-hour-regeneration.md)) with the [IML roster](../sources/iml-roster.md) observation nearest the workbook's own timestamp,
within 20 minutes, by exact booking number. IML counts a booking as held with a blank or
future release date. It also compares book date, case numbers, detainer, and earliest
court date for bookings both list, and describes the bookings only one source lists by
committing authority, time since booking, and IML location.

September 25 (76 of 80 workbook versions aligned): 3,026 bookings were in both sources.
XFER listed 136 bookings the IML roster never showed, all booked more than a week earlier
(92 more than a year); 8 IML-held bookings were missing from XFER. Book dates matched IML
commitment dates for every shared booking and case-number sets matched for 2,913 of
3,026. September 30 (131 of 135 versions aligned): 3,057 in both, 135 only in XFER, and
8 IML-held bookings missing from XFER; book dates again matched for every shared booking.
The XFER-only bookings are a stable set of older, active adult cases that IML never
lists; the cause is unconfirmed. See the source-quality entries on
[bookings only XFER lists](../source-quality/iml-xfer-hidden-bookings.md),
[IML-held bookings missing from XFER](../source-quality/iml-xfer-missing-from-xfer.md), and
[shared fields](../source-quality/iml-xfer-shared-fields.md).
