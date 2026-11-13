---
type: Source Quality Issue
title: Roster pagination shifts mid-scan
description: The IML roster total often changes during a scan, shifting pagination, so the scan is rejected and retried (about 20 to 50 times a day).
tags: [iml, population, cost, data-quality]
affects: IML roster
first_seen: 2026-09-23
generated: { by: claude-code/claude-opus-5-5, at: 2026-11-13T04:00:00Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:10:00Z }
sources:
  - id: source-quality-l31
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/docs/SOURCE_QUALITY.md?plain=1#L31-L31
    title: docs/SOURCE_QUALITY.md lines 31-31, before the OKF migration
    last_modified: 2026-09-26T02:01:31Z
    author: claude-code/claude-opus-5-5
---

# Issue

The roster total often changes during a scan of about 110 pages, shifting pagination; the scan is rejected
and retried.

# Latest evidence

Nov 13 investigation, using the local archive mirror through Nov 11 and aggregates only:

- **Order.** Rows are ordered by booking number in all 50 sampled scans. Records present in
  both of two consecutive scans kept their order in all 699 pairs.
- **Where changes land.** In 699 consecutive pairs, additions (636) landed about 91% or 99.9%
  of the way through the roster. Removals (650) landed mostly between 61% and 98%.
- **What a shift looks like.** In all 1,617 archived shift failures the page began at the
  requested row and only the total moved: 832 rose and 785 fell, and 39 moved by 2 or more.
  They were detected a mean of 81 seconds into the scan.
- **Simulated scans.** These served the earlier scan's pages up to a point and the later
  scan's after it.
  - In the ID-only simulation (46,985 cases), cases with one change between scans
    (18,213) were all rejected by the old rule. Re-reading the last accepted page would
    have accepted 91.5%, each matching the later scan exactly.
  - In 156 single-change runs of the real collector, the new code accepted 143, with no
    record missed or duplicated. In two of those, one or two records kept the earlier
    scan's field values (fields reflect when each page was read). The other 13 were
    rejected.
  - With two changes, the old and new code both accepted the same two rosters with one
    record missing and one extra. This is an existing blind spot when an addition and a
    removal offset each other between page reads.
  - With two switches in one scan (40 runs), the new code accepted 36, of which two had
    missing or extra records. These collapse 30 minutes of changes into two page gaps.
- **Page size.** No request field was found that enlarges the 30-row page, which would
  shorten scans (see [IML roster](../sources/iml-roster.md)).

Nov 11 15:00 UTC to Nov 13 03:00 UTC: 49 pagination shifts (4, 33, and 12 a day) and four
roster slots missed after retries, all after 22:30 UTC on Nov 12 while scans averaged 220 to
320 seconds instead of about 130 (collector logs; see
[monitoring and limits](../operations/monitoring-and-limits.md)).
Oct 8 to 14: 264 pagination shifts (19, 46, 40, 34, 43, 50, and 32 a day; about 38 a day),
and 35 roster slots missed after retries (2, 5, 5, 6, 4, 10, and 3 a day); the other five
failed IML scans that week exceeded the time budget (collector logs). Scans took 108 or
109 pages.
Oct 2, 3, and 5: 28, 27, and 40 pagination shifts; Oct 6 to 20:15 UTC: 23 (collector failure
records). Seven roster slots were missed after retries from Oct 2 to Oct 6 20:15 UTC, apart
from Oct 4, and runs of shifted scans met the population alert condition three times (see
[monitoring and limits](../operations/monitoring-and-limits.md)).
Sept 26 to Oct 4 05:00 UTC: 205 failed IML attempts (about 25 a day), about 200 of them
pagination shifts and the rest read timeouts (collector logs). After retries, 13 roster slots
were missed from the [cloud cutover](../deployments/2026-09-22-cutover.md) to Oct 5 02:00 UTC,
besides the 44 slots (Oct 4 05:15 to 16:00 UTC) lost to a
[blank permanent ID](iml-blank-permanent-id.md). Sept 23–26: 53 of 55 IML collection failures
(about 18 a day); 5 roster slots missed after retries by Sept 26.

# Handling

Before November 13, every scan whose total changed was rejected and retried. Failed scans and
retries used about 11% of collector time (see
[measured usage and cost](../cost/measured-usage-2026-09-26.md)). Under the
[November 13 decision](../decisions/2026-11-13-resume-after-verified-roster-change.md), the
scan instead re-reads the last accepted page. It continues against the new total only if
that page is unchanged; otherwise it is rejected as before. It has been live since the
[November 13 deployment](../deployments/2026-11-13.md) at 04:11 UTC; the 04:30 UTC scan was the
first to continue after a change (3,304 to 3,305 at row 2,131) and was accepted.
