---
type: Decision
title: Run analysis on local archive copies and publish aggregates only
description: Analysis reads local archive copies under the ignored data/ directory, never the live bucket, and publishes only aggregates with counts below ten suppressed.
tags: [analysis, privacy]
decided: 2026-09-23
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T01:54:59Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:06:36Z }
sources:
  - id: decisions-l93
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/DECISIONS.md?plain=1#L93-L94
    title: DECISIONS.md lines 93-94, before the OKF migration
    last_modified: 2026-09-23T07:42:39Z
    author: claude-code/claude-opus-5-5
---

Run analysis on local archive copies under ignored `data/`, never the live bucket, and publish
aggregate results only, with counts below ten suppressed.

Related: [Analysis](../analysis/index.md).
