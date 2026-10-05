---
type: Decision
title: Add no database, queue, or framework for this workload
description: Keep Cloud Run, Storage, and the four source adapters, adding no database, queue, or frameworks for this single-writer workload.
tags: [cloud, storage]
decided: 2026-09-23
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T01:54:59Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:06:36Z }
sources:
  - id: decisions-l78
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/DECISIONS.md?plain=1#L78-L81
    title: DECISIONS.md lines 78-81, before the OKF migration
    last_modified: 2026-09-23T02:40:21Z
---

Preserve Cloud Run/Storage and the four source adapters. Add no database, queue, frontend
framework, or generic repository framework for this single-writer workload. Extract only shared
archive recovery, XLS identifiers, and chart rendering where duplication or startup cost
justified a boundary.
