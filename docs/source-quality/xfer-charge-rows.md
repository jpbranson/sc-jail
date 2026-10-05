---
type: Source Quality Issue
title: One workbook row per charge
description: The XFER jail workbook has one row per charge with bond values repeated across rows, so count distinct bookings and never sum bonds across rows.
tags: [xfer, bonds, data-quality]
affects: XFER jail workbook
first_seen: 2026-09-19
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T01:54:59Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:10:00Z }
sources:
  - id: source-quality-l21
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/docs/SOURCE_QUALITY.md?plain=1#L21-L21
    title: docs/SOURCE_QUALITY.md lines 21-21, before the OKF migration
    last_modified: 2026-09-26T02:01:31Z
    author: claude-code/claude-opus-5-5
---

# Issue

One row per charge, with bond values repeated across charge rows.

# Handling

Count [distinct bookings](../measures/xfer-bookings.md); never sum bond values across rows. See the
[decision](../decisions/2026-09-19-xfer-distinct-bookings.md).
