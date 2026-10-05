---
type: Source Quality Issue
title: Shared IML and XFER fields mostly agree
description: For bookings both sources list, book dates always match and case-number sets mostly match; court-date and detainer differences are partly timing.
tags: [iml, xfer, data-quality]
affects: IML vs XFER
first_seen: 2026-09-25
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:10:00Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:10:00Z }
sources:
  - id: source-quality-l30
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/docs/SOURCE_QUALITY.md?plain=1#L30-L30
    title: docs/SOURCE_QUALITY.md lines 30-30, before the OKF migration
    last_modified: 2026-09-26T02:01:31Z
    author: claude-code/claude-opus-5-5
---

# Issue

Shared fields mostly agree for bookings both list.

# Latest evidence

Of 3,057 shared bookings in the Sept 30 13:34 UTC comparison: book date equals IML commitment
date for all; case-number sets identical for 2,931; detainer flags disagree for 68 (2%); earliest
court date differs for 83 and is listed by only one source for 116. On Sept 25, of 3,026: 2,913
identical case-number sets, 69 detainer disagreements, and court dates differing for 163 and
listed by one source for 168.

# Handling

[Detail pages refresh about daily](./iml-details-daily-refresh.md), so part of the court-date and
detainer differences is timing.
