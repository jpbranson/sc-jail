---
type: Source Quality Issue
title: XFER bookings the IML roster never shows
description: XFER lists about 135 held bookings the public IML roster never shows, a stable set of older active adult cases whose cause is unconfirmed.
tags: [iml, xfer, population, data-quality]
affects: IML vs XFER
first_seen: 2026-09-19
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T01:54:59Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:10:00Z }
sources:
  - id: source-quality-l28
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/docs/SOURCE_QUALITY.md?plain=1#L28-L28
    title: docs/SOURCE_QUALITY.md lines 28-28, before the OKF migration
    last_modified: 2026-10-04T17:51:48Z
    author: claude-code/claude-opus-5-5
---

# Issue

XFER lists about 135 held bookings that the public IML roster never shows. The cause is
unconfirmed: they are active adult cases, not duplicates or juveniles, and IML record pages show
only two locations (`JMS`, `JAILEAST`), which fits IML listing only people housed in those
facilities or withholding some records.

# Latest evidence

Daily medians 135 to 140.5 across 131 aligned workbook versions, Sept 19 to 30. In the Sept 30
13:34 UTC workbook: 135 bookings, 2 ever listed by IML; 134 have no IML row, held or released, with
the same surname and date of birth. All were booked more than a week earlier (91 more than a year,
against a third of shared bookings); 115 have a future court date; 33 include first-degree murder
(24%, against 12% of shared bookings); none were under 18 at booking (IML lists 23 who were);
committing authority mostly Memphis Police (69) and Sheriff (51), none federal or state; 23 marked
with a detainer. The set is stable: 133 of the 141 on Sept 19 were still hidden on Sept 30; 6
bookings later appeared on IML (after a median of about three days) and 2 left IML without a
release date while staying on XFER.

# Handling

[IML-based populations](../measures/iml-population.md) and [panels](../analysis/booking-panel.md)
exclude them; [XFER bookings](../measures/xfer-bookings.md) are a separate count. Treat IML as
roughly 4% short of the workbook when comparing totals. Only the Sheriff's Office can confirm why
IML omits them. See [source reconciliation](../analysis/source-reconciliation.md).
