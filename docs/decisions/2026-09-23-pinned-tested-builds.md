---
type: Decision
title: Pin and test builds before publishing images
description: Pin build tools and the container base, test in Cloud Build before publishing an image, preserve deployment tuning, and record parser and build provenance.
tags: [deployment, testing, provenance]
decided: 2026-09-23
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T01:54:59Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:10:00Z }
sources:
  - id: decisions-l89
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/DECISIONS.md?plain=1#L89-L91
    title: DECISIONS.md lines 89-91, before the OKF migration
    last_modified: 2026-09-23T02:40:21Z
---

Pin build tools/container base, test in Cloud Build before image publication, preserve
deployment environment tuning, and record parser/build provenance. See [the
audit](../history/2026-09-23-technical-audit.md) for costs and remaining tradeoffs.
