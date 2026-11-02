---
type: Data Source
title: XFER jail workbook
description: The SCSO-InJail.xls workbook on the public XFER file service, one row per charge, downloaded every interval and deduplicated by content hash.
resource: https://xfer.shelbycountytn.gov/SCSO-InJail/SCSO-InJail.xls
tags: [xfer, population]
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T01:54:59Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:06:36Z }
sources:
  - id: readme-l11
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/README.md?plain=1#L11-L12
    title: README.md lines 11-12, before the OKF migration
    last_modified: 2026-09-22T16:39:10Z
  - id: readme-l189
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/README.md?plain=1#L189-L190
    title: README.md lines 189-190, before the OKF migration
    last_modified: 2026-09-22T16:39:10Z
  - id: readme-l195
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/README.md?plain=1#L195-L196
    title: README.md lines 195-196, before the OKF migration
    last_modified: 2026-09-22T16:39:10Z
---

The jail report is `/SCSO-InJail/SCSO-InJail.xls` on the XFER file service. A person
can have several charge rows and potentially several bookings; the population measure is
[distinct booking numbers](../measures/xfer-bookings.md). Connection behavior is in
[county server connections](county-connections.md).

# Collection

The unchanged XFER jail file is still downloaded each time so a same-size replacement
cannot be missed. The XFER file can update less often than the collector; the dashboard
shows both timestamps.

# Known behaviors

- [Repeated column headings between printed pages](../source-quality/xfer-repeated-headings.md),
  removed by the parser; historical observations were fixed with the
  [heading repair](../operations/repair-xfer-headings.md).
- [Regenerated about every two hours](../source-quality/xfer-two-hour-regeneration.md),
  independently of polling.
- [One row per charge, with bond values repeated](../source-quality/xfer-charge-rows.md).
