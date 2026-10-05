---
type: Playbook
title: Backup and restoration
description: Daily Storage Transfer backup of the archive, how to monitor it, and how to restore into a separate location and rebuild projections.
tags: [backup, storage, operations]
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T01:54:59Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:10:00Z }
sources:
  - id: cloud-l417
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/docs/CLOUD.md?plain=1#L417-L443
    title: docs/CLOUD.md lines 417-443, before the OKF migration
    last_modified: 2026-09-23T02:40:21Z
---

The deployment configures Storage Transfer Service to copy the archive into
`gs://YOUR_PROJECT_ID-sc-jail-backup` daily at 05:10 UTC. Changed objects are copied;
objects missing from the source are retained in the backup. The transient
collector lease is excluded. The collector and dashboard have no backup access.
The backup has versioning and seven-day soft deletion. Its lifecycle removes only
noncurrent versions older than 30 days with at least two newer versions. Live
backup objects have no deletion lifecycle. This adds storage and request costs;
it is a same-project recovery copy, not protection from a compromised project owner.

Failed copy/find operations are logged and monitored. Check the transfer job's
last successful operation as well as the failure alert: a disabled job cannot
emit copy failures. Scheduled copies can overlap collection and do not form an
atomic snapshot. Immutable manifests are commit records; rebuild projections
after a restore. For a release checkpoint or restore drill, pause Scheduler,
wait for active collection to finish, run the transfer job, and compare both
inventories by object name, size, and CRC32C (excluding the lease).

After accidental deletion, first inspect the archive's soft-deleted generations
and the backup's live/noncurrent versions. Restore into a **separate private
bucket or local directory**, not over the active archive. Never restore the lease.
Use `scripts/migrate_history.py --verify-only` to check reconstruction, then
`scripts/rebuild_index.py` and `scripts/update_repeat_visits.py --rebuild` to
recreate projections. Compare counts and latest slots before switching the
collector/dashboard `SCJ_BUCKET` and resuming Scheduler. Keep the original
archive and recovery copy until validation is complete.

A rehearsal of this procedure is recorded in the
[restore drill of 2026-09-26](restore-drill-2026-09-26.md).
