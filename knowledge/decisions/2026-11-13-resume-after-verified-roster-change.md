---
type: Decision
title: Resume an IML scan after a verified roster change
description: When the IML roster total changes mid-scan, the collector re-reads the last accepted page and continues against the new total only if that page is unchanged, instead of rejecting every shifted scan.
tags: [iml, population, data-quality]
decided: 2026-11-13
status: draft
generated: { by: claude-code/claude-opus-5-5, at: 2026-11-13T04:00:00Z }
sources:
  - id: collector
    resource: ../../src/sc_jail/iml.py
    title: IML roster collector, verify_prefix and collect
  - id: pagination-shift
    resource: ../source-quality/iml-pagination-shift.md
    title: Roster pagination shifts mid-scan, evidence through November 13, 2026
---

The IML roster lists rows in booking-number order, and nearly every addition or removal lands
past the point a scan has reached. So a changed total no longer rejects the scan by itself.
The collector re-reads the last page it accepted, at the same offset. If that page's range and
all its result IDs are unchanged, the pages already read are still in place, and the scan
continues against the new total. Otherwise the scan is rejected as before, with the same
"IML pagination shifted during collection" message. A change found right after the first page
still rejects, because that page comes from the search itself. A second change found before
any further page is accepted also rejects, so every check is followed by progress and a
constantly changing roster still fails within about twice the normal page
requests.[^collector]

The owner chose this over keeping the strict rule with an in-run restart, which rarely fits
the time budget on the slow evenings when slots are missed, and over recording the findings
only. Before it, 20 to 50 scans a day failed this way. In replays of archived scans with one
roster change between page reads, about 92% would have been accepted, with no record missed
or duplicated; the rest were rejected.[^pagination-shift]

Known limits, pending the owner's review of the replay results (hence draft):

- A pair of offsetting changes inside the pages already read, plus another change past them,
  all between the same two page reads, goes undetected. Today's rule already misses an
  offsetting pair in one page gap; this adds the third change. Its rate is not measured.
- Fields such as a release date reflect the moment each page was read, as in any accepted
  scan before this decision.
- Pages archived after a verified change show the new total in their "of N" range, so
  `iml-pages.json` can hold more than one total. Accepted pages are still contiguous; the
  re-read check pages are not stored.

Related: [IML roster](../sources/iml-roster.md),
[07:00 UTC roster shrinks](../source-quality/iml-0700-roster-shrinks.md),
[monitoring and limits](../operations/monitoring-and-limits.md).

[^collector]: IML roster collector, verify_prefix and collect
[^pagination-shift]: Roster pagination shifts mid-scan, evidence through November 13, 2026
