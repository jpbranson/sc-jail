---
type: Architecture
title: Cloud architecture
description: One private Cloud Run collector, one public read-only dashboard, one Scheduler job, a private Storage archive, and a daily backup, all scaling to zero.
tags: [cloud, storage, security]
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T01:54:59Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:10:00Z }
sources:
  - id: cloud-l133
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/docs/CLOUD.md?plain=1#L133-L164
    title: docs/CLOUD.md lines 133-164, before the OKF migration
    last_modified: 2026-09-23T03:04:09Z
---

# Components

One private Cloud Run collector, one public read-only Cloud Run dashboard,
one Cloud Scheduler job, a private regional Cloud Storage archive, and a separate
daily Storage Transfer Service backup to another private bucket in `us-central1`.
Cloud Monitoring checks freshness and backup failures. Both Cloud Run services
have zero minimum instances, a configured maximum of one instance per revision,
0.25 vCPU, 512 MiB RAM, request-based billing, and
first-generation execution. The collector lease also prevents overlapping
collection across revisions.
The collector runs synchronously inside an authenticated request; it does not
depend on background threads surviving after a request ends.

The deployed resources are listed in [cloud deployment](../operations/cloud-deployment.md);
the [backup](../operations/backup-and-restore.md) and
[monitoring](../operations/monitoring-and-limits.md) have their own concepts.

# Identities

Scheduler calls `POST /collect` every 15 minutes using its own service account
and an OIDC token with the service URL as audience. Only that identity gets
`roles/run.invoker` on the collector. The dashboard cannot run collection and
its identity can read only the archive's `public/` objects. The collector gets
object access to its dedicated archive bucket. A separate builder account can
write only its build bucket and Artifact Registry repository.

# Concurrency and recovery

A conditional Cloud Storage lease prevents overlapping collectors; generation
preconditions protect updates. Source observations are immutable and recoverable
after a partially completed write. Retries skip sources already completed in a
slot. A Scheduler retry that arrives after its original 15-minute slot is
discarded instead of pretending to collect historical data.

Normalized records use daily full checkpoints and embedded change logs.
The mutable working state avoids replaying cloud objects during normal
collection. Raw source archives remain intact. See
[normalized history storage](normalized-history.md).

The bucket holds durable state; container filesystems are temporary. There is no
database server, VM, load balancer, NAT gateway, or paid domain.
