---
type: Storage Format
title: Normalized history storage
description: Schema 2 stores each source's normalized data as a daily full checkpoint plus checksummed quarter-hour change logs inside immutable observation manifests.
resource: ../../src/sc_jail/history.py
tags: [storage, provenance]
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T01:54:59Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:06:36Z }
sources:
  - id: storage-l1
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/docs/STORAGE.md?plain=1#L1-L48
    title: docs/STORAGE.md lines 1-48, before the OKF migration
    last_modified: 2026-09-23T02:40:21Z
---

Each successful quarter-hour collection has an immutable private observation
manifest. Schema 2 stores normalized data as a daily checkpoint plus change logs.
The population download schedule is unchanged. Supplemental detail and court
report policies are described in [case-data storage](case-data-storage.md).

Since September 22, 2026, Cloud Storage holds the active archive. The local
`data/` directory is the cutover backup and does not receive cloud observations.
The commands that read or maintain this history ([reconstruction and exports](../operations/exports.md),
[migration and verification](../operations/history-migration.md), and
[rebuilding derived state](../operations/rebuild-derived-state.md)) use `SCJ_BUCKET` when set,
otherwise `SCJ_DATA_DIR` (default `data/`). Use the
[cloud archive setup](../operations/active-cloud-archive.md)
for current exports, reconstruction, or maintenance.

# Representation

- The first successful collection of each **UTC day** is a full checkpoint.
  It contains normalized records, active IDs, and the IDs present in that report.
  A new day's checkpoint does not depend on any earlier observation.
- Later collections contain additions and removals relative to the previous
  successful collection. A corrected row is a removal plus an addition.
- Duplicate rows retain their multiplicity, including identical XFER charge
  rows. Normalized row order is canonical, not the source's display order.
  The original HTML/XLS preserves the source's ordering and exact bytes.
- Active IDs and observed IDs also use additions/removals, so the manifests
  do not repeat thousands of IDs every 15 minutes.
- Unchanged data needs only an unchanged-state reference and checksums.
  Each poll still records its own times, metrics, and source artifact references.
- If a compressed change log would be larger than a checkpoint, a new
  checkpoint is saved early.
- SHA-256 checks cover the checkpoint, the state before a change, and the state
  after it. Missing, damaged, forward, or cross-day links raise an error.
  A single observation requires at most 96 manifests to reconstruct.
- Collection gaps remain gaps. Changes are relative to the last successful
  observation; they do not assert when an event happened during an outage.

# Working cache and recovery

The mutable file at `private/checkpoints/{source}.json.gz` contains the current
normalized state, active IDs, and cumulative seen IDs. This working cache is
overwritten, not appended, and lets collection calculate changes with one state
read instead of replaying cloud history. Before collecting, `archive.reconcile_source`
finds committed manifests after either projection cursor, including previous slots,
and finishes checkpoint/index writes without downloading those observations again.
A malformed cache is rebuilt by checksum-verified replay inside that source's
failure boundary. A storage access failure is reported, not treated as an empty
archive. Recovery saves its cursor before the collection deadline and resumes.

# Objects

Full normalized checkpoints use the existing compressed, content-addressed
`private/blobs/` objects. Change logs live inside their observation manifests;
they do not require an extra cloud object per poll. The full directory layout is in
[archive layout](archive-layout.md).
