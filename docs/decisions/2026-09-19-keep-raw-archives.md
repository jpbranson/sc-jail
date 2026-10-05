---
type: Decision
title: Keep raw source archives unchanged
description: Raw source archives and downloads stay unchanged, and original manifests and blobs are kept as private backups when history is migrated.
tags: [storage, provenance]
decided: 2026-09-19
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T01:54:59Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:06:36Z }
sources:
  - id: decisions-l38
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/DECISIONS.md?plain=1#L38-L39
    title: DECISIONS.md lines 38-39, before the OKF migration
    last_modified: 2026-09-22T16:39:10Z
---

Keep all raw source archives and source downloads unchanged. Preserve original manifests/blobs
as private backups when migrating history.

Related: [Archive layout](../architecture/archive-layout.md), [History migration](../operations/history-migration.md).
