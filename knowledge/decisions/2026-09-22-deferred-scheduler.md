---
type: Decision
title: Separate service deployment from Scheduler activation
description: Deploy services before activating Scheduler so existing history can be copied and checksum-verified before cloud collection begins.
tags: [deployment, cloud]
decided: 2026-09-22
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T01:54:59Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:10:00Z }
sources:
  - id: decisions-l56
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/DECISIONS.md?plain=1#L56-L59
    title: DECISIONS.md lines 56-59, before the OKF migration
    last_modified: 2026-09-22T16:39:10Z
---

Separate initial service deployment from Scheduler activation so existing history can be copied
and checksum-verified before cloud collection begins. `--defer-scheduler` leaves an existing
job unchanged; pause it explicitly for later maintenance. `--scheduler-only` activates without
rebuilding.

Related: [Deploy to Google Cloud](../operations/deploy.md), [Move existing local history](../operations/migrate-local-history.md).
