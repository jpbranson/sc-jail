---
type: Decision
title: Run the weekly analysis as a local Windows task
description: The weekly analysis runs as a local Windows task under the owner's sign-in from a gcloud-synced mirror, keeping person-level analysis off the cloud services.
tags: [analysis, local, privacy]
decided: 2026-09-26
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T01:54:59Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:06:36Z }
sources:
  - id: decisions-l100
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/DECISIONS.md?plain=1#L100-L104
    title: DECISIONS.md lines 100-104, before the OKF migration
    last_modified: 2026-09-26T02:01:31Z
    author: claude-code/claude-opus-5-5
---

Run the weekly analysis as a local Windows task under the owner's sign-in, reading a local
mirror refreshed with `gcloud storage rsync`. This keeps person-level analysis off the cloud
services and needs no stored credentials; a missed run starts at the next opportunity. Readouts
are marked preliminary until each analysis has enough collection time.

Related: [Weekly analysis run](../analysis/weekly-run.md).
