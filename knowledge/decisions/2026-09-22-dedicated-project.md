---
type: Decision
title: Deploy in a dedicated project and stop local collection
description: Deploy in the dedicated sc-jail-research-20260922 project in us-central1, hand quarter-hour collection to Cloud Scheduler, and keep local history as a backup.
tags: [cloud, deployment, local]
decided: 2026-09-22
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T01:54:59Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:10:00Z }
sources:
  - id: decisions-l52
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/DECISIONS.md?plain=1#L52-L55
    title: DECISIONS.md lines 52-55, before the OKF migration
    last_modified: 2026-09-22T16:39:10Z
---

Deploy in the dedicated `sc-jail-research-20260922` project in `us-central1`. Cloud Scheduler
now owns quarter-hour collection; stop the local collector, dashboard, temporary tunnel, and
Windows restart task. Keep the migrated local history as a backup, not as the current archive.

Related: [Cloud deployment](../operations/cloud-deployment.md), [September 22 cutover](../deployments/2026-09-22-cutover.md).
