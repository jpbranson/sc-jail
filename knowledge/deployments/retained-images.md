---
type: Reference
title: Retained images and rollback
description: Which container images remain available for rollback under the image cleanup policy, as recorded after the November 19 deployment.
tags: [deployment, cloud, operations]
generated: { by: claude-code/claude-fable-5-2, at: 2026-11-19T02:37:00Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-15T16:50:00Z }
sources:
  - id: cloud-l77
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/docs/CLOUD.md?plain=1#L77-L84
    title: docs/CLOUD.md lines 77-84, before the OKF migration
    last_modified: 2026-10-04T16:37:08Z
    author: claude-code/claude-opus-5-5
---

For rollback, the image before the [November 19 deployment](2026-11-19.md) is the
[November 13 build](2026-11-13.md)
(`sha256:d50c9473300410c58dd0b97852869366357621d51669ef8925230e34a40f346e`), built from
`main` at `da316ed`. It can serve both services. It lacks the slow-read warning, and its
dashboard makes every request wait for an index reload, as before November 19. Deploying it
with the current script still gives the dashboard 1 vCPU and concurrency 4.

As of November 19, 2026, 02:30 UTC, the repository held five images: the November 19 build
(`ae482ae4…`, tagged `latest`), the untagged image from that day's first attempt
(`21a09b7d…`, same source), the untagged November 13 build (`d50c9473…`), the untagged
[November 11 build](2026-11-11.md) (`c2211ebf…`), and the
[September 23 image](2026-09-23-detail-refresh-fix.md)
(`sha256:cab94e326b8ca956088a552e329c20f242f44e96d738f3ca859ce805062edb5b`, still tagged
`detail-refresh-20260923`). The [November 2 build](2026-11-02.md) (`d9f10157…`) has been
removed. The cleanup policy keeps the two most recent images and removes other untagged
images seven days after they were built, so `d50c9473…` and `c2211ebf…` can be deleted at
the next cleanup run that finds them seven days old; tag `d50c9473…` to keep the rollback
image.
Deploy a retained digest with `--image` as described in
[owner setup and deployment](../operations/deploy.md).
