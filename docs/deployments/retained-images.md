---
type: Reference
title: Retained images and rollback
description: Which container images remain available for rollback under the image cleanup policy, as recorded after the October 15 deployment.
tags: [deployment, cloud, operations]
generated: { by: claude-code/claude-fable-5-1, at: 2026-10-15T20:30:00Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-15T16:50:00Z }
sources:
  - id: cloud-l77
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/docs/CLOUD.md?plain=1#L77-L84
    title: docs/CLOUD.md lines 77-84, before the OKF migration
    last_modified: 2026-10-04T16:37:08Z
    author: claude-code/claude-opus-5-5
---

For rollback, the image before the [October 15 deployment](2026-10-15.md) is the
[October 6 collector build](2026-10-06.md)
(`sha256:9d502c1d69a68f09a4379df99484f72a434bfa9cbde95b4d9f7f4b7e3d776166`). It was built
from commit `dad628b`, so it differs from the current image only in reporting the county's
IML error page as a possible layout change, and its dashboard code differs from the
October 4 image only by a docstring, so it can serve both services.

As of October 15, 2026, 16:45 UTC, the repository held four images: the October 15 build
(`0785da0f…`, tagged `latest`), the untagged October 6 build (`9d502c1d…`), the untagged
October 4, 16:24 UTC build (`2276038d…`), and the [September 23 image](2026-09-23-detail-refresh-fix.md)
(`sha256:cab94e326b8ca956088a552e329c20f242f44e96d738f3ca859ce805062edb5b`, still tagged
`detail-refresh-20260923`). The October 4, 16:06 UTC build (`2c651baa…`) had been removed.
The cleanup policy keeps the two most recent images and removes other untagged images seven
days after they were built, so `2276038d…` can be deleted at the next cleanup run; tag it to
keep it.
Deploy a retained digest with `--image` as described in
[owner setup and deployment](../operations/deploy.md).
