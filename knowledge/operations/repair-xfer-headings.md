---
type: Playbook
title: Repeated XFER heading correction
description: The parser skips the jail workbook's repeated column headings; a resumable repair command fixed historical observations and backs up every manifest first.
resource: ../../scripts/repair_xfer_headers.py
tags: [xfer, data-quality, operations]
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T01:54:59Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:06:36Z }
sources:
  - id: case-data-l181
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/docs/CASE_DATA.md?plain=1#L181-L199
    title: docs/CASE_DATA.md lines 181-199, before the OKF migration
    last_modified: 2026-09-22T16:39:10Z
---

The [jail XLS](../sources/xfer-jail-workbook.md) repeats its complete column headings between
printed pages ([source-quality entry](../source-quality/xfer-repeated-headings.md)). These
rows are now skipped after trimming surrounding whitespace; genuine duplicate
charge rows remain. The September 19 repair is already included in the migrated
cloud archive. This historical maintenance command is not a deployment step;
pause collection and let active work finish before any future repair:

```powershell
.\.venv\Scripts\python.exe scripts\repair_xfer_headers.py
```

The repair recomputes records, booking counts, cumulative seen IDs, and interval
changes, then rebuilds checkpoint/change-log chains and the public index. Every
original manifest is backed up under `private/repairs/xfer-headers-v1/` before any
replacement. The maintenance marker prevents XFER collection during an
interrupted repair; rerun the command to resume. Original raw spreadsheets and
earlier migration backups remain unchanged.

The repair's recorded results are in [tests, lint, and dependency refresh](verification.md);
see also the [decision to remove repeated headings](../decisions/2026-09-19-remove-xfer-repeated-headings.md).
