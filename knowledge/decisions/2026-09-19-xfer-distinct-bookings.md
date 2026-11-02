---
type: Decision
title: Count distinct XFER bookings separately from IML people
description: The XFER report has several charge rows per booking, so it is shown as distinct bookings, separate from IML's distinct permanent IDs.
tags: [xfer, iml, population]
decided: 2026-09-19
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T01:54:59Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:06:36Z }
sources:
  - id: decisions-l17
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/DECISIONS.md?plain=1#L17-L18
    title: DECISIONS.md lines 17-18, before the OKF migration
    last_modified: 2026-09-22T16:39:10Z
---

The XFER report has multiple charge rows per booking. Display distinct bookings separately from
IML's distinct permanent IDs.

Related: [XFER bookings](../measures/xfer-bookings.md), [IML population](../measures/iml-population.md).
