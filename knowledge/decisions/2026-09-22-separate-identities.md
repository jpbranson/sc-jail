---
type: Decision
title: Use separate least-privilege service identities
description: The collector, dashboard, scheduler, and builder each get their own identity, with dashboard storage limited to public/ and an authenticated collector.
tags: [security, cloud]
decided: 2026-09-22
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T01:54:59Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:10:00Z }
sources:
  - id: decisions-l60
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/DECISIONS.md?plain=1#L60-L64
    title: DECISIONS.md lines 60-64, before the OKF migration
    last_modified: 2026-09-22T16:39:10Z
---

Use separate collector, dashboard, scheduler, and builder identities. Restrict dashboard
storage access to `public/`, require authentication on the collector, and enforce public-access
prevention on the archive bucket. Allow the builder to read metadata only on its dedicated
build bucket, in addition to its object and repository permissions.

Related: [System architecture](../architecture/system.md).
