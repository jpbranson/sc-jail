---
type: Storage Format
title: Case-data storage
description: IML detail HTML is kept only on semantic changes and court reports once per content version, both with daily checkpoints and change logs.
tags: [storage, iml-details, xfer-courts]
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T01:54:59Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:06:36Z }
sources:
  - id: case-data-l80
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/docs/CASE_DATA.md?plain=1#L80-L101
    title: docs/CASE_DATA.md lines 80-101, before the OKF migration
    last_modified: 2026-09-22T16:39:10Z
---

Both supplemental collectors use daily normalized checkpoints and record change
logs ([normalized history storage](normalized-history.md)). Their current-state caches are
overwritten, not accumulated every interval.

# IML record pages

For [IML](../sources/iml-record-pages.md), retrieval timestamps are stored separately from the
detail records. A successful unchanged check does not create another HTML blob or pretend that
the record changed. Raw HTML is archived on the first successful retrieval and
whenever the normalized content changes. Presentation-only HTML changes are not
retained as new versions. A downloaded page that fails parsing or identity checks
is kept as an explicitly unparsed private artifact, and does not replace the
last valid record. Images, including photographs, are not downloaded.

# Court reports

For [courts](../sources/xfer-court-reports.md), each downloaded content version gets one
compressed raw file, one compressed normalized table when supported, and a small provenance
manifest. SHA-256 addresses reuse identical bytes, including across filenames. Unchanged
periodic verification updates only retrieval metadata. Current listings form a
bounded working catalog; older report versions remain under
`private/court-reports/` even after the county removes their filenames.

# Retention

The original full-roster HTML and jail XLS retention policy remains unchanged.
No research archives, migration backups, or repair backups were deleted.
See [storage growth](storage-growth.md).
