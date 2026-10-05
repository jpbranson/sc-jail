---
type: Playbook
title: Rebuild derived state
description: Rebuild all four source checkpoints and the public index from committed history during paused maintenance; repeat analytics rebuild separately.
resource: ../../scripts/rebuild_index.py
tags: [storage, operations]
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T01:54:59Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:06:36Z }
sources:
  - id: storage-l105
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/docs/STORAGE.md?plain=1#L105-L119
    title: docs/STORAGE.md lines 105-119, before the OKF migration
    last_modified: 2026-09-23T02:40:21Z
---

If the public index is missing or malformed, normal collection repairs its
population projections from committed observations. For a complete rebuild of
all four source checkpoints and the public index during paused maintenance:

```powershell
.\.venv\Scripts\python.exe scripts\rebuild_index.py
```

This validates retained normalized history, preserves original manifests/blobs,
and keeps only the latest 90 days in the public population view. It preserves an
existing repeat summary; rebuild repeat analytics separately if that projection
was lost (see the [repeat-visit registry](../architecture/repeat-visit-registry.md)).
Missing or corrupt immutable history is an error requiring
[restoration](backup-and-restore.md), not a reason to fabricate a collection or silently skip
data.
