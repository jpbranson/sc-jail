---
type: Deployment
title: September 23 detail-refresh fix
description: Collector-only update at 04:55 UTC on September 23 that queues IML record pages for refresh at 20 hours, ahead of the 24-hour freshness limit.
tags: [deployment, cloud, iml-details]
status: deprecated
deployed: 2026-09-23
source_revision: source-3b79f7a94a05796d4e7f
image: sha256:cab94e326b8ca956088a552e329c20f242f44e96d738f3ca859ce805062edb5b
cloud_build: b053b757-05fd-4e79-8894-c835ebc66c75
revisions: { collector: sc-jail-collector-00005-ddm }
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T01:54:59Z }
sources:
  - id: cloud-l86
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/docs/CLOUD.md?plain=1#L86-L102
    title: docs/CLOUD.md lines 86-102, before the OKF migration
    last_modified: 2026-09-26T13:07:32Z
---

Superseded by [September 26 deployment](2026-09-26.md).

**September 23 detail-refresh fix.** The collector received an
early-detail-refresh fix at 04:55 UTC on September 23 and served revision
`sc-jail-collector-00005-ddm`, built from `source-3b79f7a94a05796d4e7f`, with the
`cab94e…` image (see [retained images](retained-images.md)). Cloud Build
`b053b757-05fd-4e79-8894-c835ebc66c75` passed all 138 tests and lint on Linux/Python
3.13; Windows checks also passed. Only the collector image changed then; the dashboard
kept the [0.2.0 release](2026-09-23-release-0-2-0.md) image until September 26. Details
queue at 20 hours with oldest-first rotation, while the freshness limit remains 24 hours.
See [case-data settings](../architecture/configuration.md) for the configurable lead and
its request-volume tradeoff.

The first scheduled pass on that revision (05:00 UTC) refreshed 80 details with
zero page failures, finishing the detail stage at 05:03:47 UTC. It retained all
3,249 available records; 3,169 were fresh and 80 still overdue as the existing
daily-expiry wave continued. The oldest check advanced from 03:56 to 04:47 UTC
on September 22. The freshness endpoint correctly remained HTTP 503. This
verified the deployed collection path, not full backlog recovery. The backlog had
cleared by September 26: all 3,308 eligible pages were fresh at 00:05 UTC.
