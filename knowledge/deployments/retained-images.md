---
type: Reference
title: Retained images and rollback
description: Which container images remain available for rollback under the image cleanup policy, as recorded after the November 2 deployment.
tags: [deployment, cloud, operations]
generated: { by: claude-code/claude-fable-5-1, at: 2026-11-02T03:05:00Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-15T16:50:00Z }
sources:
  - id: cloud-l77
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/docs/CLOUD.md?plain=1#L77-L84
    title: docs/CLOUD.md lines 77-84, before the OKF migration
    last_modified: 2026-10-04T16:37:08Z
    author: claude-code/claude-opus-5-5
---

For rollback, the image before the [November 2 deployment](2026-11-02.md) is the
[October 15 build](2026-10-15.md)
(`sha256:0785da0f1fcb166e55a76178484ee6535d79f87c56b9ce604d22267ce8af8c1f`), built from
`main` at `b80fab0`. It differs from the current image only by the dashboard's population
forecast panel, so it can serve both services.

As of November 2, 2026, 03:00 UTC, the repository held four images: the November 2 build
(`d9f10157…`, tagged `latest`), the untagged October 15 build (`0785da0f…`), the untagged
[October 6 build](2026-10-06.md) (`9d502c1d…`), and the
[September 23 image](2026-09-23-detail-refresh-fix.md)
(`sha256:cab94e326b8ca956088a552e329c20f242f44e96d738f3ca859ce805062edb5b`, still tagged
`detail-refresh-20260923`). The October 4 build (`2276038d…`) has been removed.
The cleanup policy keeps the two most recent images and removes other untagged images seven
days after they were built, so `9d502c1d…` can be deleted at the next cleanup run; tag it to
keep it.
Deploy a retained digest with `--image` as described in
[owner setup and deployment](../operations/deploy.md).
