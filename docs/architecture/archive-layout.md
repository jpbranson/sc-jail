---
type: Reference
title: Archive layout and meaning
description: The data/ (or bucket) layout of public index, private checkpoints, observations, blobs, court reports, analytics, repairs, and failure records, and what it retains.
tags: [storage, privacy, provenance]
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T01:54:59Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:06:36Z }
sources:
  - id: readme-l157
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/README.md?plain=1#L157-L190
    title: README.md lines 157-190, before the OKF migration
    last_modified: 2026-09-23T03:04:09Z
  - id: readme-l198
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/README.md?plain=1#L198-L198
    title: README.md line 198, before the OKF migration
    last_modified: 2026-09-22T16:39:10Z
  - id: readme-l210
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/README.md?plain=1#L210-L215
    title: README.md lines 210-215, before the OKF migration
    last_modified: 2026-09-22T16:39:10Z
---

# Layout

```text
data/
  public/index.json                 # aggregate dashboard index, latest 90 days
  private/checkpoints/*.json.gz     # latest normalized state and cumulative seen IDs
  private/observations/...          # daily checkpoints + quarter-hour change logs
  private/blobs/...                 # compressed originals and checkpoint data
  private/legacy/observations/...   # original manifests retained during migration
  private/court-reports/...         # immutable raw/normalized court report versions
  private/analytics/...             # repeat-visit registry and resumable progress
  private/repairs/...               # backups before derived-data corrections
  private/failures/...              # durable failed-attempt records
```

# Observations

Original XLS files and full IML result pages are retained. SHA-256 content keys
avoid storing identical downloads repeatedly; every successful polling interval
still gets an observation. Manifests contain collection start/end times, source
file modification time where available, counts, checksums, and blob references.
Snapshots are collected over a period of time, not at a single instant.
New observations also record application, parser, and source-build versions;
older manifests remain readable without those optional fields.

Normalized history now uses a full checkpoint on the first successful collection
of each UTC day, followed by record and ID changes. Duplicate charge rows are
preserved; unchanged collections need only a reference and checksum. The latest
state is cached for efficient collection. Raw source files remain unchanged.
See [normalized history storage](normalized-history.md) for format details, and
[exports](../operations/exports.md) and [history migration](../operations/history-migration.md)
for commands. Legacy migration backups are retained.

# Failures

A failed or incomplete source never becomes a zero count. Last good data remains
visible with a failure or overdue notice. The two sources fail independently.
Repeated successful work in the same quarter hour is skipped.
(The [XFER jail workbook](../sources/xfer-jail-workbook.md) is still downloaded every time.)

# Retention and privacy

The 90-day dashboard index is a view limit, not a deletion policy; all aggregate history
can be [exported](../operations/exports.md).

Treat `data/` as private. It, local logs, downloaded reference code, environments,
and credentials are excluded from Git and cloud/container build contexts.
For a local archive, back up the whole data directory while collection is stopped.
The local cutover backup does not include subsequent cloud observations. Cloud manifests
and blobs remain in the regional bucket indefinitely; monitor growth. No
automatic deletion of research data is configured. See [storage growth](storage-growth.md).
