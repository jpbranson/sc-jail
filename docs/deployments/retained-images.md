---
type: Reference
title: Retained images and rollback
description: Which container images remain available for rollback under the image cleanup policy, as recorded after the October 4 deployments.
tags: [deployment, cloud, operations]
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:12:00Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:10:00Z }
sources:
  - id: cloud-l77
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/docs/CLOUD.md?plain=1#L77-L84
    title: docs/CLOUD.md lines 77-84, before the OKF migration
    last_modified: 2026-10-04T16:37:08Z
    author: claude-code/claude-opus-5-5
---

For rollback, the image before the [October 4 fix](2026-10-04-1624.md) is the
[September 28 build](2026-09-28.md) (`sha256:144ed915…`), but it rejects the roster
while a blank permanent ID is listed. The cleanup policy keeps only the two most recent
images (now both October 4 builds) and removes other untagged images seven days after
they were built, so the September 27 and 28 images are due for removal; tag one to keep
it. The [September 23 image](2026-09-23-detail-refresh-fix.md)
(`sha256:cab94e326b8ca956088a552e329c20f242f44e96d738f3ca859ce805062edb5b`) is
still tagged `detail-refresh-20260923`.
As of October 5, 2026, 02:05 UTC, the repository held four images: the two October 4
builds (`2276038d…`, tagged `latest`, and `2c651baa…`), the untagged September 28 build
(`144ed915…`, past its seven days, so the next cleanup run can delete it), and the tagged
September 23 image; the September 26 and 27 images had been removed.
Deploy a retained digest with `--image` as described in
[owner setup and deployment](../operations/deploy.md).
