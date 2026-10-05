---
type: Milestone
title: Analysis steps result
description: The September 26, 2026 weekly analysis run and staged analyses, with readout dates and the source findings that changed the design.
tags: [history, analysis]
date: 2026-09-26
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T01:54:59Z }
sources:
  - id: plan-l299
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/PLAN.md?plain=1#L299-L320
    title: PLAN.md lines 299-320, before the OKF migration
    last_modified: 2026-09-26T02:01:31Z
    author: claude-code/claude-opus-5-5
---

Built the [weekly run](../analysis/weekly-run.md) (`scripts/weekly_analysis.py`) and scheduled it as the
`SC-Jail-Weekly-Analysis` Windows task (Wednesdays 09:00, runs late if missed). Each run
refreshes the `data/snapshots/current` mirror, rebuilds and validates the panel, and writes
the profile, trends, IML/XFER reconciliation, length of stay, money bond, court linkage,
and re-booking reports to `data/analysis/weekly/<date>/`. Started the
[source-quality log](../source-quality/index.md). See [analysis](../analysis/index.md) for
definitions and first results.

Step status ([plan](../analysis/plan.md)): 1 done; 5's weekly run, trends, reconciliation, and quality log done; step 4's
match rates done. Steps 2, 3, 4 (court-date and indictment timing), and 5's re-booking are
coded, tested, and run on current data, but their readouts wait for collection time:
October 17 (bond, court timing), October 19 (length of stay), and December 18
(re-booking). Each report is marked preliminary until then.

Findings that changed the design: record pages [fill in over the first day](../source-quality/iml-details-fill-in.md) (charges a
median of 6.5 hours after a booking appears, the bond decision 20.5 hours), so groups use
the filled-in page; XFER lists about 137 [long-held bookings the IML roster never shows](../source-quality/iml-xfer-hidden-bookings.md); and
most General Sessions entries are marked "Sentenced", which may make the profile's
pretrial count too low. That last point needs checking against court records before any
definition changes ([open question](../questions/sentenced-meaning.md)). Progress and open items are in the [next-steps run log](next-steps-run-2026-09.md).
