---
type: Decision
title: Store daily checkpoints and quarter-hour change logs
description: Normalized history is stored as daily checkpoints plus quarter-hour record and ID changes, checksum-verified, with a cached current state to keep cloud reads small.
tags: [storage]
decided: 2026-09-19
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T01:54:59Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:06:36Z }
sources:
  - id: decisions-l35
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/DECISIONS.md?plain=1#L35-L37
    title: DECISIONS.md lines 35-37, before the OKF migration
    last_modified: 2026-09-22T16:39:10Z
---

Store daily normalized checkpoints and quarter-hour record/ID changes, preserving duplicate
charge rows. Verify history with checksums and cache the current state to keep routine cloud
reads small.

Related: [Normalized history storage](../architecture/normalized-history.md).
