---
type: Milestone
title: Checkpoint and change-log storage
description: September 19, 2026 plan and result for daily normalized checkpoints with quarter-hour change logs, including migration of 40 existing observations.
tags: [history, storage]
date: 2026-09-19
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T01:54:59Z }
sources:
  - id: plan-l134
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/PLAN.md?plain=1#L134-L173
    title: PLAN.md lines 134-173, before the OKF migration
    last_modified: 2026-09-22T16:39:10Z
---

# Plan

1. Save a complete normalized checkpoint on the first successful collection of
   each UTC day. Store record additions/removals and ID-set changes in later
   observation manifests; unchanged collections need only a history reference.
2. Canonicalize row order, preserve duplicate rows, and verify before/after
   state hashes. Use another full checkpoint if a change log would be larger.
3. Cache the latest normalized state in the existing mutable collector state
   so regular collection does not replay a day of cloud objects.
4. Support reconstruction of both old snapshots and new change logs, with
   explicit failure for missing, corrupt, or inconsistent history.
5. Migrate existing manifests under the collector lock, verify reconstruction,
   and retain original manifests/blobs as private migration backups. Keep all
   raw source files and existing download behavior.
6. Test day rollover, duplicate rows, corrections, unchanged data, corruption,
   retry recovery, migration, and local/cloud storage; restart local collection
   and verify a live observation uses the new format.

# Result

Implemented daily normalized checkpoints, embedded quarter-hour change logs,
checksum-verified reconstruction, and a mutable current-state cache. Added
migration and reconstruction commands, with operating details in [normalized history storage](../architecture/normalized-history.md).

All 65 tests and lint checks pass. Converted and verified 40 existing observations,
preserving original manifests and blobs as private backups. A historical export
reconstructed all 23,353 records from the original XFER observation. The
dashboard and tunnel remained running during the collector restart.

Both sources saved and verified new-format observations for the 13:30 UTC slot:
IML used a 514-byte unchanged manifest, and XFER used a 2,522-byte change-log
manifest. Reconstruction matched the original HTML/XLS data, including duplicate
rows and ID sets. IML's initial source request hit the existing time limit; its
automatic retry succeeded. Both sources now report normal collection.

Raw-source retention, source requests, dashboard behavior, and the 15-minute
schedule are unchanged. Temporary validation copies were removed; migration
backups remain. Cloud deployment still awaits the account setup described in the
[initial implementation](2026-09-19-initial-implementation.md) record.
