---
type: Decision
title: Group new bookings by the filled-in record page
description: New bookings are grouped by the record page after it fills in, not the first page fetched, which usually predates charges and bonds.
tags: [analysis, iml-details]
decided: 2026-09-26
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T01:54:59Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:06:36Z }
sources:
  - id: decisions-l105
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/DECISIONS.md?plain=1#L105-L107
    title: DECISIONS.md lines 105-107, before the OKF migration
    last_modified: 2026-09-26T02:01:31Z
    author: claude-code/claude-opus-5-5
---

Group new bookings by the record page after it fills in (case entries for charge and detainer,
a bond decision for bond), not the first page fetched, which usually predates charges and
bonds.

Related: [record pages fill in](../source-quality/iml-details-fill-in.md), [Length of stay](../analysis/length-of-stay.md).
