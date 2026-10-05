---
type: Analysis
title: Money bond
description: Finds new bonds, reductions, increases, and recognizance entries from record-page changes and follows each to release; also describes low money bonds.
resource: ../../scripts/bond_analysis.py
tags: [analysis, bonds]
stale_after: 2026-10-17T00:00:00Z
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:10:00Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:10:00Z }
sources:
  - id: analysis-l221
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/docs/ANALYSIS.md?plain=1#L221-L232
    title: docs/ANALYSIS.md lines 221-232, before the OKF migration
    last_modified: 2026-09-26T02:01:31Z
    author: claude-code/claude-opus-5-5
---

`scripts/bond_analysis.py` compares consecutive record-page versions with case entries to
find each booking's first new court-assessed bond, reduction, increase, recognizance entry,
or cleared total, and follows each to release. It also describes people held now on [money
bond alone](population-profile.md) at or below $1,000, $5,000, and $10,000, and new bookings whose first bond
decision was that low. Changes are dated when seen (record pages [refresh about daily](../source-quality/iml-details-daily-refresh.md)).
Bond status is never treated as a court outcome.

Preliminary (September 25): 53 reductions (median cut 66%), followed by release a median
of 1 day later; 79 people held on money bond alone of $5,000 or less, a median of 19 days
so far, 36 of them more than 30 days. The first readout needs about four weeks.

Latest weekly run (September 30, 2026): 87 reductions (median cut 67%), followed by release a
median of 1 day later; 85 people held on money bond alone of $5,000 or less, a median of 19
days so far, 35 of them more than 30 days.
