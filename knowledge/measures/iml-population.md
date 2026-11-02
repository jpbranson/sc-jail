---
type: Metric
title: IML population
description: The IML population is the count of distinct permanent IDs whose release date is blank or after today's Memphis date.
resource: https://imljail.shelbycountytn.gov/IML
tags: [iml, population]
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T01:54:59Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:06:36Z }
sources:
  - id: readme-l7
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/README.md?plain=1#L7-L10
    title: README.md lines 7-10, before the OKF migration
    last_modified: 2026-10-04T16:36:20Z
---

# Definition

Distinct permanent IDs with a blank release date or one after today's
Memphis date. The complete result set includes recently released records,
which remain in the private archive but are excluded from the current count.
A booking listed before IML assigns its permanent ID is archived but counts no one.

Measured from the [IML roster](../sources/iml-roster.md). The related source behaviors are
[recently released bookings on the roster](../source-quality/iml-lists-recent-releases.md) and
[bookings listed with a blank permanent ID](../source-quality/iml-blank-permanent-id.md).
It is counted separately from [XFER bookings](xfer-bookings.md).
