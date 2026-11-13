---
type: Reference
title: Retained images and rollback
description: Which container images remain available for rollback under the image cleanup policy, as recorded after the November 13 deployment.
tags: [deployment, cloud, operations]
generated: { by: claude-code/claude-opus-5-5, at: 2026-11-13T04:40:00Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-15T16:50:00Z }
sources:
  - id: cloud-l77
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/docs/CLOUD.md?plain=1#L77-L84
    title: docs/CLOUD.md lines 77-84, before the OKF migration
    last_modified: 2026-10-04T16:37:08Z
    author: claude-code/claude-opus-5-5
---

For rollback, the image before the [November 13 deployment](2026-11-13.md) is the
[November 11 build](2026-11-11.md)
(`sha256:c2211ebf83d59ecdab9c703b7a5ef305547aec9eb8b6ff58f7773b6891952739`), built from
`main` at `e37682f`. It differs from the current image only by the collector's IML scan,
so it can serve both services, but it brings back the rejection of every roster scan whose
total changes mid-scan (see the
[pagination-shift issue](../source-quality/iml-pagination-shift.md)).

As of November 13, 2026, 04:40 UTC, the repository held four images: the November 13 build
(`d50c9473…`, tagged `latest`), the untagged November 11 build (`c2211ebf…`), the untagged
[November 2 build](2026-11-02.md) (`d9f10157…`), and the
[September 23 image](2026-09-23-detail-refresh-fix.md)
(`sha256:cab94e326b8ca956088a552e329c20f242f44e96d738f3ca859ce805062edb5b`, still tagged
`detail-refresh-20260923`). The [October 15 build](2026-10-15.md) (`0785da0f…`) has been
removed. The cleanup policy keeps the two most recent images and removes other untagged
images seven days after they were built, so `d9f10157…` can be deleted at the next cleanup
run; tag it to keep it.
Deploy a retained digest with `--image` as described in
[owner setup and deployment](../operations/deploy.md).
