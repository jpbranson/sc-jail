---
type: Decision
title: Target Cloud Run, Scheduler, and private Cloud Storage
description: Run on scale-to-zero Cloud Run with Cloud Scheduler and private Cloud Storage, which fits near-zero cost better than an always-on server.
tags: [cloud, cost]
decided: 2026-09-19
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T01:54:59Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:10:00Z }
sources:
  - id: decisions-l6
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/DECISIONS.md?plain=1#L6-L7
    title: DECISIONS.md lines 6-7, before the OKF migration
    last_modified: 2026-09-22T16:39:10Z
---

Target Google Cloud Run, Scheduler, and private Cloud Storage. Scaling to zero is a better fit
for near-zero cost than an always-on server.

Related: [System architecture](../architecture/system.md).
