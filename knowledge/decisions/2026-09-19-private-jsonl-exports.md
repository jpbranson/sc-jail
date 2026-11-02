---
type: Decision
title: Export individual records privately as JSON lines
description: Individual records stay private and are exported as JSON lines; the dashboard adds only aggregate coverage, freshness, and collection health.
tags: [privacy, dashboard]
decided: 2026-09-19
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T01:54:59Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:06:36Z }
sources:
  - id: decisions-l49
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/DECISIONS.md?plain=1#L49-L50
    title: DECISIONS.md lines 49-50, before the OKF migration
    last_modified: 2026-09-22T16:39:10Z
---

Keep individual records private and export them as JSON lines. The dashboard adds only
aggregate coverage, freshness, and collection health.

Related: [Private exports](../operations/exports.md).
