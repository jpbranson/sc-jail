---
type: Playbook
title: Move existing local history to Cloud Storage
description: Maintenance-window procedure for copying a local archive into an empty cloud archive and activating collection; the deployed project's cutover is complete.
tags: [cloud, storage, operations]
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T01:54:59Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:10:00Z }
sources:
  - id: cloud-l355
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/docs/CLOUD.md?plain=1#L355-L380
    title: docs/CLOUD.md lines 355-380, before the OKF migration
    last_modified: 2026-09-22T16:39:10Z
---

The [cutover](../deployments/2026-09-22-cutover.md) is complete for the deployed project.
Do not copy the frozen local backup over its newer cloud archive. For another migration,
use a maintenance window so no collector modifies the data during copy:

1. For initial setup, use `--defer-scheduler` (see [deployment](deploy.md)) so no cloud
   job exists yet. For an existing deployment, pause the job:
   `gcloud scheduler jobs pause sc-jail-quarter-hour --location us-central1 --project YOUR_PROJECT_ID`.
2. Wait for any cloud collection to finish; pausing Scheduler does not cancel
   an active request. Let the local collection finish, then stop local processes
   using `scripts/stop-local.ps1` and confirm the restart task is disabled.
3. If the cloud bucket already contains research observations, back it up and
   reconcile overlapping slots first. Do not overwrite a newer cloud index with
   an older local copy.
4. For an empty destination archive, copy:
   `gcloud storage rsync data/private gs://YOUR_PROJECT_ID-sc-jail-data/private --recursive --checksums-only --exclude='.*\.tmp$'`
   and
   `gcloud storage rsync data/public gs://YOUR_PROJECT_ID-sc-jail-data/public --recursive --checksums-only --exclude='.*\.tmp$'`.
   Compare source/destination object inventories, sizes, and CRC32C checksums
   before activation. Exclude transient files; retain all research backups.
5. For initial setup, create and invoke the job:
   `.\.venv\Scripts\python.exe scripts\deploy_gcp.py --project YOUR_PROJECT_ID --scheduler-only`.
   For an existing paused job, resume it:
   `gcloud scheduler jobs resume sc-jail-quarter-hour --location us-central1 --project YOUR_PROJECT_ID`.
6. Confirm both sources update in the next slot. Keep the local files as a backup.
