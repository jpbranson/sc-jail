---
type: Analysis
title: Court linkage
description: Joins pending hearings by booking number and calendars and indictments by exact case number to measure match rates, court-date changes, and indictment timing.
resource: ../../scripts/court_linkage.py
tags: [analysis, courts, xfer-courts]
stale_after: 2026-10-17T00:00:00Z
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:10:00Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:10:00Z }
sources:
  - id: analysis-l234
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/docs/ANALYSIS.md?plain=1#L234-L246
    title: docs/ANALYSIS.md lines 234-246, before the OKF migration
    last_modified: 2026-09-26T02:01:31Z
    author: claude-code/claude-opus-5-5
---

`scripts/court_linkage.py` joins the latest [pending-hearings report](../sources/xfer-court-reports.md) to bookings by exact
booking number, and every archived calendar and indictment version by exact [case number](../source-quality/case-number-formats.md).
It classifies changes in each booking's earliest listed court date and measures time from
commitment to indictment, by the status of the indicted case itself
([decision](../decisions/2026-09-26-keep-sentenced-definition.md)).

Match rates (September 25): 518 of 519 pending-hearing rows matched to a booking list that
case on the booking's record; the report listed 327 of 3,027 held bookings. 1,223 held
bookings had a case on a Criminal Court calendar during collection and 586 on a General
Sessions calendar. Most [court-date changes](../source-quality/iml-details-court-date-changes.md) (1,212) are a passed date replaced by a new one,
a median of 10 days later; the daily record refresh cannot tell a continuance from a
scheduled next step. Court-date and indictment timing need four to eight weeks.

Latest weekly run (September 30, 2026): 638 of 639 pending-hearing rows matched to a booking
list that case on the booking's record, and the report listed 406 of 3,066 held bookings;
1,429 held bookings had a case on a Criminal Court calendar and 634 on a General Sessions
calendar; 1,891 passed dates were replaced (a median of 9 days later) against 3 resets
before the hearing; 55 bookings matched an indictment list, 52 with the indicted case open.
