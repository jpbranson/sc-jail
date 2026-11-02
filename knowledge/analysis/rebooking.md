---
type: Analysis
title: Re-booking
description: Kaplan-Meier time from a listed release until the same IML permanent ID is booked again, for releases seen during collection.
resource: ../../scripts/rebooking.py
tags: [analysis, repeat-visits]
stale_after: 2026-12-18T00:00:00Z
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:10:00Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:10:00Z }
sources:
  - id: analysis-l248
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/docs/ANALYSIS.md?plain=1#L248-L254
    title: docs/ANALYSIS.md lines 248-254, before the OKF migration
    last_modified: 2026-10-04T16:36:20Z
    author: claude-code/claude-opus-5-5
---

`scripts/rebooking.py` follows each release listed during collection until the same IML
permanent ID is booked again, with Kaplan-Meier estimates. People whose permanent ID was
ever [reassigned](../source-quality/iml-permanent-id-changes.md) are left out (51 of 533 releases on September 25), as are releases of a
booking that [never had a permanent ID](../source-quality/iml-blank-permanent-id.md); both count in `excluded_reassigned_ids`. This covers only this
jail during collection and is not a recidivism rate. The readout needs about 90 days.

Latest weekly run (September 30, 2026): 850 releases listed during collection, 108 of them
left out for a reassigned or missing permanent ID; 23 of the remaining 742 were followed by
a new booking of the same person so far.
