---
type: Decision
title: Use a Python Flask dashboard with minimal charts
description: A Flask dashboard with Shiny-like styling and minimal charts serves short HTTP requests, avoiding the cost of persistent dashboard sessions.
tags: [dashboard, cost]
decided: 2026-09-19
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T01:54:59Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:06:36Z }
sources:
  - id: decisions-l10
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/DECISIONS.md?plain=1#L10-L11
    title: DECISIONS.md lines 10-11, before the OKF migration
    last_modified: 2026-09-22T16:39:10Z
---

Use a Python Flask dashboard with Shiny-like styling and minimal charts. Short HTTP requests
avoid paying for persistent dashboard sessions.
