---
type: Source Quality Issue
title: Roster pagination shifts mid-scan
description: The IML roster total often changes during a scan, shifting pagination, so the scan is rejected and retried (about 20 to 50 times a day).
tags: [iml, population, cost, data-quality]
affects: IML roster
first_seen: 2026-09-23
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-15T16:50:00Z }
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

Rejecting shifted scans keeps populations exact. Failed scans and retries use about 11% of collector
time (see [measured usage and cost](../cost/measured-usage-2026-09-26.md)).
