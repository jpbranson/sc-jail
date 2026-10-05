---
type: Playbook
title: Work with the active cloud archive
description: Authenticate with Application Default Credentials and set SCJ_BUCKET to export from or maintain the live cloud archive, pausing Scheduler for maintenance.
tags: [cloud, storage, operations]
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T01:54:59Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:10:00Z }
sources:
  - id: cloud-l382
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/docs/CLOUD.md?plain=1#L382-L415
    title: docs/CLOUD.md lines 382-415, before the OKF migration
    last_modified: 2026-09-23T02:40:21Z
---

From the repository root, use the [CLI PATH setup](deploy.md) and authenticate the
local Python client with Application Default Credentials. `gcloud auth login`
for deployment does not itself configure these credentials. The account needs
access to the private archive; the dashboard service account intentionally lacks
that access.

```powershell
gcloud auth application-default login
$env:SCJ_BUCKET = 'sc-jail-research-20260922-sc-jail-data'
.\.venv\Scripts\python.exe scripts\export_archive.py --output data\exports\history.csv
```

The same `SCJ_BUCKET` selection applies to case exports, reconstruction, repairs,
and analytics updates. Export commands read the cloud archive and write their
output locally. Maintenance commands can modify the selected archive; pause
scheduling and let active collection finish before using them. Resume after
verification:

```powershell
gcloud scheduler jobs pause sc-jail-quarter-hour --location us-central1 --project sc-jail-research-20260922
# Wait for active collection to finish, perform maintenance, and verify results.
gcloud scheduler jobs resume sc-jail-quarter-hour --location us-central1 --project sc-jail-research-20260922
```

For subsequent commands that should use the local archive, clear the selection:

```powershell
Remove-Item Env:SCJ_BUCKET -ErrorAction SilentlyContinue
```

The local `data/` directory remains the September 22 cutover backup. It must not
be used to overwrite newer cloud observations.
