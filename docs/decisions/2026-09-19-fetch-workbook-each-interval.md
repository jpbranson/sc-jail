---
type: Decision
title: Fetch the jail spreadsheet every interval
description: Download the jail spreadsheet each interval and deduplicate by content hash, because filename and file size cannot reliably detect changes.
tags: [xfer, storage]
decided: 2026-09-19
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T01:54:59Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:06:36Z }
sources:
  - id: decisions-l21
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/DECISIONS.md?plain=1#L21-L22
    title: DECISIONS.md lines 21-22, before the OKF migration
    last_modified: 2026-09-22T16:39:10Z
---

Fetch the jail spreadsheet each interval and deduplicate by its content hash. Filename and file
size alone cannot reliably detect changes.

Related: [XFER jail workbook](../sources/xfer-jail-workbook.md).
