---
type: Data Source
title: IML record pages
description: IML individual detail pages for bookings on the latest complete roster, identity-checked and refreshed about daily in bounded batches.
resource: https://imljail.shelbycountytn.gov/IML
tags: [iml-details, iml]
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T01:54:59Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:06:36Z }
sources:
  - id: case-data-l10
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/docs/CASE_DATA.md?plain=1#L10-L45
    title: docs/CASE_DATA.md lines 10-45, before the OKF migration
    last_modified: 2026-09-23T05:06:55Z
---

# Fields collected

The collector initializes a normal IML search session and visits the detail
pages linked by the most recent complete [roster](iml-roster.md). It checks both booking number
and permanent ID before accepting a response. It collects:

- Inmate and physical information, plus incarceration and housing fields.
- Aliases, charges (case number, offense date, code, description, grade, degree).
- Separate bond entries and their amounts, types, status, posting fields, and
  source totals. Bond status is not a court disposition.
- Hearing information and detainers, including complaint number/date and the
  issuing and setting authorities when published.

Dates, amounts, case numbers, and source labels retain their published meaning.
Do not sum repeated bond values across charge rows. Repeated charges and aliases
are preserved. Names are not used to join people or cases.

# Refresh

By default, each pass attempts at most 80 pages within 120 seconds. Changed roster
entries, new/unfetched bookings, oldest overdue pages, and then early refreshes
receive priority. Age takes precedence over release status so older pages are not
continually deferred by newer active bookings. A failed page waits an hour before
another attempt; three consecutive page failures end
the batch. Pages enter the refresh queue at 20 hours by default, leaving four
hours for bounded batches and retries before the strict 24-hour freshness limit.
Pages awaiting an early refresh remain fresh until that limit; failed requests
and genuinely overdue pages still make the product check unhealthy. Actual
revisits depend on source availability and the execution budget. Detail-only
changes are found on that rotation, not necessarily at the next 15-minute
population poll. The initial roster takes
multiple passes to cover. The public dashboard shows actual coverage and backlog.

The defaults are set in [configuration](../architecture/configuration.md); the pass runs inside
the collector request as described in [case-data collection](../architecture/case-data-collection.md).

# Cache and exports

The current detail cache contains only bookings in the latest roster. When a
booking disappears, its previously collected details remain reconstructable in
historical observations; disappearance is not a confirmed release. Every detail
[export](../operations/exports.md) includes its own last successful retrieval and last semantic
change times. A roster older than two hours is not used to start a detail pass.

How versions are stored is in [case-data storage](../architecture/case-data-storage.md).

# Known behaviors

- [Pages are refreshed about daily](../source-quality/iml-details-daily-refresh.md), so changes are dated when seen.
- [Pages fill in over the first day or two](../source-quality/iml-details-fill-in.md).
- Others are in the [source-quality log](../source-quality/index.md).
