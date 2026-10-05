---
type: Reference
title: Retention and storage growth
description: All raw roster HTML and jail XLS stay archived with deduplication; raw originals remain the largest part of archive growth.
tags: [storage, cost]
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T01:54:59Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:06:36Z }
sources:
  - id: storage-l121
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/docs/STORAGE.md?plain=1#L121-L133
    title: docs/STORAGE.md lines 121-133, before the OKF migration
    last_modified: 2026-09-22T16:39:10Z
---

All original roster HTML and jail XLS files remain archived with content
deduplication and are still fetched every 15 minutes. New individual-detail HTML
is retained on semantic changes; new court reports use selective downloads and
daily verification. Both expansions reuse the checkpoint/change-log format.
See [case-data storage](case-data-storage.md) for the precise policies.

The [normalized history](normalized-history.md) optimization reduces normalized-history and
manifest growth. Raw originals remain the largest component, so it does not promise a
comparable reduction in total archive size. Daily checkpoints add roughly one compressed
normalized state per source per day; change-log size depends on actual record changes.
The current-state cache has a roughly fixed size, apart from cumulative seen IDs.

Measured growth is recorded in [measured usage and cost](../cost/measured-usage-2026-09-26.md).
