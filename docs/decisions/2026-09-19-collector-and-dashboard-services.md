---
type: Decision
title: Separate the collector and dashboard services
description: Cloud deployment uses one authenticated HTTP collection service and a separate aggregate-only dashboard, both with zero minimum instances.
tags: [cloud, security, dashboard]
decided: 2026-09-19
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T01:54:59Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:10:00Z }
sources:
  - id: decisions-l30
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/DECISIONS.md?plain=1#L30-L31
    title: DECISIONS.md lines 30-31, before the OKF migration
    last_modified: 2026-09-22T16:39:10Z
---

Cloud deployment uses one authenticated HTTP service for collection and a separate
aggregate-only dashboard, both with zero minimum instances.

Related: [System architecture](../architecture/system.md).
