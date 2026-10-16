---
type: Source Quality Issue
title: Server error page served as HTTP 200
description: The IML server can answer every request with a Java stack trace and HTTP 200; the scan is rejected and reported as an IML server error naming only the exception class.
tags: [iml, availability]
affects: IML roster
first_seen: 2026-10-15
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-15T16:20:00Z }
sources:
  - id: iml-parser
    resource: ../../src/sc_jail/iml.py
    title: IML roster parser
---

# Issue

When the county's IML application fails, it still returns HTTP 200, with a page beginning
"An abnormal error occured, and the error page could not be displayed" followed by a Java stack
trace. The retrying HTTP session treats it as a success, and the page has no result range.

# Latest evidence

On October 15, collector logs show no IML roster scan succeeding between the 14:00 UTC slot
(finished 14:03 UTC) and the 16:15 slot (finished 16:18 UTC). The 14:15 slot's two scans
failed on [pagination shifts](iml-pagination-shift.md); from 14:29 to 16:03 UTC every attempt,
roster and record pages alike, failed on read timeouts and a few connection resets. From
16:00 to 16:09 UTC four attempts received this error page,
`org.hibernate.SessionException: Session is closed!`, and the dashboard showed "IML result
range missing; possible login, error, or layout change". A manual request at 16:06 UTC got
the same page for both the landing page and the roster search. Record-page collection waited
for a complete roster throughout. The eight missed slots cannot be backfilled.

# Handling

The roster parser[^iml-parser] reports this page as "IML server error (<exception class>)",
so a county outage is not mistaken for a layout change. Only the class name is reported,
because collection errors appear on the public dashboard and an exception message could carry
query values. Health and retries are unchanged. See
[monitoring and limits](../operations/monitoring-and-limits.md).

[^iml-parser]: IML roster parser
