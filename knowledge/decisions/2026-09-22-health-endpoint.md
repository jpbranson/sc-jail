---
type: Decision
title: Use /health for cloud process checks
description: Cloud process checks use /health, keeping /healthz only as a local alias because Google's frontend returned 404 for it.
tags: [monitoring, cloud]
decided: 2026-09-22
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T01:54:59Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:10:00Z }
sources:
  - id: decisions-l69
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/DECISIONS.md?plain=1#L69-L71
    title: DECISIONS.md lines 69-71, before the OKF migration
    last_modified: 2026-09-22T16:39:10Z
---

Use `/health` for cloud process checks. Keep `/healthz` as a local compatibility alias because
Google's frontend returned 404 for that path. Check `/api/status` and actual observation slots
to verify collection freshness.

Related: [Monitoring and limits](../operations/monitoring-and-limits.md).
