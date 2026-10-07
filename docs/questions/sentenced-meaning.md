---
type: Open Question
title: 'What does "Sentenced" mean on a General Sessions case entry?'
description: The September 25 cohort contains 438 people potentially affected by the unresolved General Sessions "Sentenced" label; case-level court checks are still needed.
tags: [iml-details, courts, analysis, data-quality]
raised: 2026-09-25
generated: { by: codex/agent, at: 2026-10-07T18:03:26Z }
sources:
  - id: flight-log-l34
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/FLIGHT_LOG.md?plain=1#L34-L44
    title: FLIGHT_LOG.md lines 34-44, before the OKF migration
    last_modified: 2026-09-26T02:01:31Z
    author: claude-code/claude-opus-5-5
---

Found 2026-09-25, step 4 of the [next-steps run](../history/next-steps-run-2026-09.md).

Of 1,345 held people counted as "sentenced on some cases, others open", 438 have *only* General
Sessions (8-digit) entries marked "Sentenced" plus an open Criminal Court case. Of 35 bookings
matched to a daily indictment list, 32 have the indicted case open, but only 1 passes the
[plan's](../analysis/plan.md) "no case marked sentenced" test. If IML marks a General Sessions case
"Sentenced" when it is bound over to the grand jury, the [profile's](../analysis/population-profile.md)
pretrial count (1,416 on Sept 25) understates pretrial detention by up to about 440 people.

Still open as of October 7, 2026: no reviewed case record resolves it. The September 30
weekly run counted 1,471 held people with no case marked sentenced and 1,346 sentenced on some
cases with others open; of 55 bookings matched to an indictment list, 52 had the indicted case
open and 2 passed the "no case marked sentenced" test.

Needs a check against court records (a few case numbers on the public Criminal Court and General
Sessions sites) before changing any published definition. Nothing was changed; [court
linkage](../analysis/court-linkage.md) already uses the indicted case's own status. Evidence in the
[source-quality log](../source-quality/iml-details-sentenced-meaning.md).

See the [decision to keep the current definition](../decisions/2026-09-26-keep-sentenced-definition.md)
until this is checked.

# October 7 investigation

The [evidence review](../source-quality/iml-details-sentenced-meaning.md#october-7-investigation)
confirms that official guidance distinguishes bind-over from a guilty plea, but neither
source defines the IML label. The public repository records cohort counts, not the original
sample case identifiers; checked-in fixtures are synthetic. The court portal returned a
security block before case search. No individual case was traced and no classification or
published definition changed.

To resume, use the original private sample or a dated archive extract with IML bond entries
and case numbers, plus corresponding GS and Criminal Court histories/orders. The review
lists the required evidence and a small comparison set. The 438-person sensitivity applies
only to September 25; September 30 and current subgroups must be recomputed separately.
