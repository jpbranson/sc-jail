---
type: Decision
title: Treat immutable observations as the commit journal
description: Immutable observations are the commit journal, and checkpoints and indexes are repairable projections reconciled across slot boundaries.
tags: [storage, provenance]
decided: 2026-09-23
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T01:54:59Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:06:36Z }
sources:
  - id: decisions-l75
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/DECISIONS.md?plain=1#L75-L77
    title: DECISIONS.md lines 75-77, before the OKF migration
    last_modified: 2026-09-23T03:04:09Z
---

Treat immutable observations as the commit journal and mutable checkpoints/indexes as
repairable projections. Reconcile across slot boundaries, isolate corrupt source caches, and
keep repeat-analysis rebuilds resumable.

Related: [Normalized history storage](../architecture/normalized-history.md), [Rebuild derived state](../operations/rebuild-derived-state.md), [Repeat-visit registry](../architecture/repeat-visit-registry.md).
