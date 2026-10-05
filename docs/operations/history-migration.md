---
type: Playbook
title: History migration and verification
description: Convert an archive to schema-2 history under the collector lease and verify every observation by chronological checksum replay.
resource: ../../scripts/migrate_history.py
tags: [storage, operations, provenance]
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T01:54:59Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:06:36Z }
sources:
  - id: storage-l69
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/docs/STORAGE.md?plain=1#L69-L103
    title: docs/STORAGE.md lines 69-103, before the OKF migration
    last_modified: 2026-09-23T03:04:09Z
---

New collectors can start against an old archive without migration: the first
new-format collection becomes a checkpoint. Old observations remain readable.
The format is described in [normalized history storage](../architecture/normalized-history.md).

# Migrate

The deployed archive already includes the September 19 migration; these are
maintenance commands, not required deployment steps. To convert another archive,
pause its scheduler, let any active collection finish, and run:

```powershell
.\.venv\Scripts\python.exe scripts\migrate_history.py
.\.venv\Scripts\python.exe scripts\migrate_history.py --verify-only
```

These commands use `SCJ_DATA_DIR` or `SCJ_BUCKET` like the collector. Migration
holds the collector lease, verifies the reconstructed normalized state, and uses
atomic/generation-checked manifest replacement. It resumes safely if interrupted.
Maintenance leases renew with generation preconditions while work progresses;
losing the lease stops further writes safely. Completed conversions remain
readable. Migration of a large archive requires a planned maintenance window and
an administrative identity; the collector cannot replace historical manifests.

Original manifests are retained under `private/legacy/observations/`, and their
original normalized blobs remain available. This is a one-time migration backup:
conversion does not immediately reclaim those bytes. Future observations use
only the new format. Daily cloud backup is configured separately; no live
raw-archive deletion is configured. See [backup and restoration](backup-and-restore.md).

# Verify

Verification replays every observation in chronological order. Missing data or
checksum failures stop verification rather than silently replacing history.
`--verify-only` leaves observations and projections unchanged but still acquires
the collector lease, so a cloud identity needs read access plus write access to
`private/collector-lease.json`. Run it against a separate recovery copy or during
paused maintenance. After migration, verify a real collection and the public
status endpoint.
