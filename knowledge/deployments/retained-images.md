---
type: Reference
title: Retained images and rollback
description: Which container images remain available for rollback under the image cleanup policy, as recorded after the November 11 deployment.
tags: [deployment, cloud, operations]
generated: { by: claude-code/claude-opus-5-5, at: 2026-11-11T15:10:00Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-15T16:50:00Z }
sources:
  - id: cloud-l77
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/docs/CLOUD.md?plain=1#L77-L84
    title: docs/CLOUD.md lines 77-84, before the OKF migration
    last_modified: 2026-10-04T16:37:08Z
    author: claude-code/claude-opus-5-5
---

For rollback, the image before the [November 11 deployment](2026-11-11.md) is the
[November 2 build](2026-11-02.md)
(`sha256:d9f10157830d9c25ad671087fef9e7750bfcbb5a167168467d2d756d9afd41b4`), built from
`analysis/time-series-forecast` at `89f3ddf`. It differs from the current image only by the
collector's repeat-visit and supplement-publishing fix, so it can serve both services, but
it brings back the overrun described in
[monitoring and limits](../operations/monitoring-and-limits.md).

As of November 11, 2026, 15:00 UTC, the repository held four images: the November 11 build
(`c2211ebf…`, tagged `latest`), the untagged November 2 build (`d9f10157…`), the untagged
[October 15 build](2026-10-15.md) (`0785da0f…`), and the
[September 23 image](2026-09-23-detail-refresh-fix.md)
(`sha256:cab94e326b8ca956088a552e329c20f242f44e96d738f3ca859ce805062edb5b`, still tagged
`detail-refresh-20260923`). The [October 6 build](2026-10-06.md) (`9d502c1d…`) has been
removed. The cleanup policy keeps the two most recent images and removes other untagged
images seven days after they were built, so `0785da0f…` can be deleted at the next cleanup
run; tag it to keep it.
Deploy a retained digest with `--image` as described in
[owner setup and deployment](../operations/deploy.md).
