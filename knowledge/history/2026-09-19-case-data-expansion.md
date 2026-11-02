---
type: Milestone
title: Detail and court-report expansion
description: September 19, 2026 plan and result for collecting IML record pages and XFER court reports, with the repeated-heading repair and first live sizes.
tags: [history, iml-details, xfer-courts]
date: 2026-09-19
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T01:54:59Z }
sources:
  - id: plan-l175
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/PLAN.md?plain=1#L175-L229
    title: PLAN.md lines 175-229, before the OKF migration
    last_modified: 2026-09-22T16:39:10Z
  - id: case-data-l201
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/docs/CASE_DATA.md?plain=1#L201-L215
    title: docs/CASE_DATA.md lines 201-215, before the OKF migration
    last_modified: 2026-09-22T16:39:10Z
---

# Plan

1. Reject [repeated XFER column-heading rows](../source-quality/xfer-repeated-headings.md) while preserving genuine duplicate
   charge rows. Repair all affected normalized observations, counts, ID sets,
   change logs, and the public index under the collector lock. Back up every
   original manifest before replacement and make repair safe to resume.
2. Inspect live IML detail sections and criminal court report layouts. Preserve
   repeated cases, bonds, hearings, aliases, and detainers as structured data;
   validate identity and required sections before accepting a detail page.
3. Keep the 15-minute population collections first. Use the remaining bounded
   execution time for a rotating IML detail queue, prioritizing new or changed
   bookings and then overdue records. Expose coverage and retrieval times;
   do not imply every detail page is refreshed every 15 minutes.
4. Monitor the General Sessions and Criminal/State Criminal court calendar,
   indictment, pending-hearing, and disposition folders. Download new/changed
   reports in bounded batches, recheck unchanged files periodically, and keep
   unsupported layouts explicit rather than silently losing columns or rows.
5. Reuse compressed content-addressed blobs and checkpoint/change-log history
   for detail records. Store court reports once per version with structured
   rows and provenance. Keep images out of collection and avoid new copies of
   semantically unchanged detail HTML. Preserve existing raw archives.
6. Provide private exports and aggregate coverage/status on the dashboard.
   Test parsing, history repair/recovery, selective refresh, failures, and
   storage reuse; run live bounded checks and restart local scheduled work.

# Result

- [Corrected](../operations/repair-xfer-headings.md) 39 historical XFER observations, removing 20,168 repeated heading
  rows across them. Rebuilt counts, seen IDs, interval changes, caches, and the
  public history; verified all 77 observations then present. Original manifests
  and raw reports remain available. Historical XFER counts in earlier [milestone records](2026-09-19-initial-implementation.md)
  predate this correction; use the repaired archive for analysis.
- Implemented identity-checked IML details, including charges, bonds, hearings,
  aliases, incarceration fields, and detainers. Added a bounded daily refresh
  queue, separate check timestamps, daily checkpoints/change logs, and private
  HTML versions for semantic changes. Images are not fetched.
- Added selective collection of General Sessions and Criminal Court calendars,
  indictments, and pending hearings; monitor the empty dispositions directory.
  Preserve raw and normalized content versions, periodically verify unchanged
  files, and expose unsupported formats explicitly.
- Added private JSON-lines exports with provenance and an aggregate dashboard
  coverage panel. Population observations remain independent and commit first.
- Restarted local collection and the dashboard while retaining the existing
  Quick Tunnel and Windows supervisor. The initial live pass successfully saved
  80 details and 8 court reports; histories and exports verified. The remaining
  backlog will be collected by subsequent scheduled passes.

See [record pages](../sources/iml-record-pages.md) and [court reports](../sources/xfer-court-reports.md)
for field coverage, [configuration](../architecture/configuration.md) for refresh settings,
[case-data storage](../architecture/case-data-storage.md) for storage tradeoffs, and
[exports](../operations/exports.md) for export commands; initial measured sizes are under
*Initial live verification* below. Cloud account setup remains pending.

Final verification: all 95 tests and lint checks pass. Both private export CLI
commands ran successfully. The local dashboard and existing Quick Tunnel return
current aggregate coverage, and the Windows supervisor is enabled with the final
collector and dashboard code running.

# Initial live verification - 2026-09-19

The first expanded pass collected 80 of 3,268 listed IML bookings and 8 of 37
listed court reports with no parsing failures. It took approximately 55 seconds
for details and 5 seconds for court reports after the population observations.
At that rate, the initial detail queue needs about 41 successful passes (roughly
10 hours); this is an estimate, not a guarantee during outages or roster changes.

The 80 raw detail pages used 277,236 compressed bytes; their initial normalized
checkpoint used 34,560 bytes. The eight court files used 383,370 compressed bytes
for originals and 224,835 for normalized rows. These are small initial samples,
not steady-state growth forecasts. Routine unchanged detail checks create no new
raw HTML, while changed records, new reports, and daily checkpoints still grow
the archive. Both supplemental histories reconstructed successfully and private
exports returned 80 details and 3,246 rows from the latest report in each family.
