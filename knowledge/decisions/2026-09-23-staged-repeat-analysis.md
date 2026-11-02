---
type: Decision
title: Stage repeat analysis and keep dashboard data through outages
description: Repeat-analysis progress is staged privately and only complete results are published; the dashboard keeps validated data through storage outages.
tags: [repeat-visits, dashboard]
decided: 2026-09-23
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T01:54:59Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:06:36Z }
sources:
  - id: decisions-l86
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/DECISIONS.md?plain=1#L86-L88
    title: DECISIONS.md lines 86-88, before the OKF migration
    last_modified: 2026-09-23T02:40:21Z
---

Stage repeat-analysis progress privately and publish only complete fixed-target results. Keep
validated dashboard data through storage outages, aggregate long-range change bars, and cache
rendered charts with bounded size.

Related: [Repeat-visit registry](../architecture/repeat-visit-registry.md), [Monitoring and limits](../operations/monitoring-and-limits.md).
