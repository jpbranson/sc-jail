---
type: Decision
title: Narrow collector access and add an independent backup
description: The collector can create and read history but overwrite only projections, backed by seven-day recovery and a separately permissioned, versioned daily backup.
tags: [security, backup, monitoring]
decided: 2026-09-23
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T01:54:59Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:10:00Z }
sources:
  - id: decisions-l82
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/DECISIONS.md?plain=1#L82-L85
    title: DECISIONS.md lines 82-85, before the OKF migration
    last_modified: 2026-09-23T02:40:21Z
---

Give the collector create/read access to historical objects and overwrite access only to
mutable projections. Enable seven-day archive recovery and an independently permissioned,
versioned daily backup without source-delete propagation. Monitor freshness, supplemental
coverage, and backup errors.

Related: [Backup and restoration](../operations/backup-and-restore.md), [Monitoring and limits](../operations/monitoring-and-limits.md).
