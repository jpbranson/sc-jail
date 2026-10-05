---
type: Data Source
title: IML roster
description: The public Shelby County IML roster, read 30 records per page with at most two concurrent pages and accepted only when its range, total, and IDs validate.
resource: https://imljail.shelbycountytn.gov/IML
tags: [iml, population]
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T01:54:59Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:06:36Z }
sources:
  - id: readme-l145
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/README.md?plain=1#L145-L155
    title: README.md lines 145-155, before the OKF migration
    last_modified: 2026-09-22T16:39:10Z
---

The IML roster supplies the [IML population](../measures/iml-population.md) and links to the
[IML record pages](iml-record-pages.md). Connection behavior shared with XFER is in
[county server connections](county-connections.md).

# Scan

IML reads at most two pages concurrently and validates
each page's exact range, the stable total, and unique result IDs before accepting
a complete roster. IML returns 30 records per page, so the number of requests
varies with roster size. Its scan has a seven-minute budget; population sources share
a nine-minute deadline so a slow IML scan leaves a bounded allowance for XFER.
IML logs progress every 20 pages and records successful scan duration. A shifted
or incomplete roster is rejected and the last good count remains visible.

The budget and page concurrency are set by `SCJ_IML_TIMEOUT_SECONDS` and
`SCJ_IML_PAGE_WORKERS` ([configuration](../architecture/configuration.md)).

# Known behaviors

- [Pagination shifts when the total changes mid-scan](../source-quality/iml-pagination-shift.md).
- [The 07:00 UTC roster shrinks during every attempt](../source-quality/iml-0700-roster-shrinks.md).
- [The roster also lists recently released bookings](../source-quality/iml-lists-recent-releases.md).
- Other roster entries are in the [source-quality log](../source-quality/index.md).
