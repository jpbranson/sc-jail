---
type: Cloud Deployment
title: Google Cloud deployment
description: The live sc-jail deployment in sc-jail-research-20260922 (us-central1), with its services, archive, backup, Scheduler, monitoring, budget, and identities.
resource: https://console.cloud.google.com/home/dashboard?project=sc-jail-research-20260922
tags: [cloud, deployment, operations]
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T01:54:59Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:10:00Z }
sources:
  - id: cloud-l1
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/docs/CLOUD.md?plain=1#L1-L9
    title: docs/CLOUD.md lines 1-9, before the OKF migration
    last_modified: 2026-10-04T16:37:08Z
  - id: cloud-l104
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/docs/CLOUD.md?plain=1#L104-L115
    title: docs/CLOUD.md lines 104-115, before the OKF migration
    last_modified: 2026-09-26T02:01:31Z
  - id: cloud-l122
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/docs/CLOUD.md?plain=1#L122-L125
    title: docs/CLOUD.md lines 122-125, before the OKF migration
    last_modified: 2026-09-22T16:39:10Z
  - id: readme-l33
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/README.md?plain=1#L33-L60
    title: README.md lines 33-60, before the OKF migration
    last_modified: 2026-09-26T02:01:31Z
---

# Current deployment

As of September 23, 2026 UTC, the collectors and dashboard are deployed to Google
Cloud in `us-central1`. Initially deployed September 22, 2026; updated to 0.2.0 on
September 23 UTC and redeployed on September 26, 27, and 28 and twice on October 4.
The live service configuration, Scheduler, backup settings, and public endpoints were
rechecked on September 23 and October 4. See the
[0.2.0 release record](../deployments/2026-09-23-release-0-2-0.md) for that release's
validation. The current deployment record is
[October 4, 16:24 UTC](../deployments/2026-10-04-1624.md); every deployment is listed
in [deployments](../deployments/index.md).

# Resources

- Project: `sc-jail-research-20260922` (number `564083380783`).
- Region: `us-central1`.
- Dashboard: https://sc-jail-dashboard-xcucxqzc2q-uc.a.run.app
- Private collector: https://sc-jail-collector-xcucxqzc2q-uc.a.run.app
- Archive: `gs://sc-jail-research-20260922-sc-jail-data` (private).
- Daily backup: `gs://sc-jail-research-20260922-sc-jail-backup`, at 05:10 UTC.
- Scheduler: `sc-jail-quarter-hour`, `*/15 * * * *` in UTC. Cloud Scheduler invokes the
  private collector on UTC quarter hours.
- Health: `/health` checks the dashboard process; `/api/freshness` returns HTTP 503 when
  population collection is unhealthy. `/api/status` retains the detailed status. See
  [monitoring and limits](monitoring-and-limits.md).
- Monitoring: four freshness uptime checks and a backup-error alert, with an
  enabled email notification channel.
- Monthly budget: $5 since September 26, 2026 (was $15), matching the
  [owner's target](../decisions/2026-09-26-under-5-dollars.md) of under $5 a month, with
  actual-spend alerts at 50%, 90%, and 100%, and a forecast alert at 100%. The budget
  does not cap spending. See [measured usage and cost](../cost/measured-usage-2026-09-26.md).

# Identities and access

The deployment uses dedicated collector, dashboard, scheduler, and builder
service accounts. The dashboard reads only `public/` objects, the archive
enforces public-access prevention, and unauthenticated collector calls return
403. The public `/health`, charts, API routes, and CSV export were checked live.

# Cutover and local fallback

The migration verified all 5,858 files (about 136 MiB) by size and CRC32C.
The local collector, dashboard, temporary tunnel, and `SC-Jail-Local` restart
task were stopped during cutover. The local `data/` directory remains as a
backup of the migrated history; it no longer receives new cloud observations.

The first regular 9:00 a.m. Central cloud run completed successfully for both
population sources. See the [cutover record](../deployments/2026-09-22-cutover.md).
The 0.2.0 audit improvements and release evidence are recorded in the
[technical audit](../history/2026-09-23-technical-audit.md) and
[verification record](../deployments/2026-09-23-release-0-2-0.md).
The [local setup](local-setup.md) remains available for development or fallback. Starting
it does not pause Cloud Scheduler or synchronize the cloud archive. Before a
production fallback, pause the cloud job, let any active collection finish, and
copy the current cloud archive into a separate local directory; the cutover
backup no longer contains the full history.
