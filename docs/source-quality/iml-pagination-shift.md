---
type: Source Quality Issue
title: Roster pagination shifts mid-scan
description: The IML roster total often changes during a scan, shifting pagination, so the scan is rejected and retried (about 18 times a day).
tags: [iml, population, cost, data-quality]
affects: IML roster
first_seen: 2026-09-23
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:10:00Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:10:00Z }
sources:
  - id: source-quality-l31
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/docs/SOURCE_QUALITY.md?plain=1#L31-L31
    title: docs/SOURCE_QUALITY.md lines 31-31, before the OKF migration
    last_modified: 2026-09-26T02:01:31Z
    author: claude-code/claude-opus-5-5
---

# Issue

The roster total often changes during a 111-page scan, shifting pagination; the scan is rejected
and retried.

# Latest evidence

Sept 26 to Oct 4 05:00 UTC: 205 failed IML attempts (about 25 a day), about 200 of them
pagination shifts and the rest read timeouts (collector logs). After retries, 13 roster slots
were missed from the [cloud cutover](../deployments/2026-09-22-cutover.md) to Oct 5 02:00 UTC,
besides the 44 slots (Oct 4 05:15 to 16:00 UTC) lost to a
[blank permanent ID](iml-blank-permanent-id.md). Sept 23–26: 53 of 55 IML collection failures
(about 18 a day); 5 roster slots missed after retries by Sept 26.

# Handling

Rejecting shifted scans keeps populations exact. Failed scans and retries use about 11% of collector
time (see [measured usage and cost](../cost/measured-usage-2026-09-26.md)).
