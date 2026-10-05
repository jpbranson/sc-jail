---
type: Source Quality Issue
title: 'Meaning of "Sentenced" on General Sessions entries'
description: 'Most General Sessions entries are marked "Sentenced", which may mean disposed rather than serving a sentence; unverified, so the profile may understate pretrial detention.'
tags: [iml-details, courts, analysis, data-quality]
affects: IML details
first_seen: 2026-09-25
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:10:00Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:10:00Z }
sources:
  - id: source-quality-l26
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/docs/SOURCE_QUALITY.md?plain=1#L26-L26
    title: docs/SOURCE_QUALITY.md lines 26-26, before the OKF migration
    last_modified: 2026-09-26T02:01:31Z
    author: claude-code/claude-opus-5-5
---

# Issue

Most General Sessions case entries are marked "Sentenced", including for people with an open, newly
indicted Criminal Court case. "Sentenced" may mean disposed in General Sessions (for example bound
over) rather than serving a sentence. **Unverified; see the [human review
item](../questions/sentenced-meaning.md).**

# Latest evidence

Record pages on Sept 25: 2,396 General Sessions entries "Sentenced" and 650 "Open". Of 1,345 people
held and counted as sentenced on some cases, 438 have only General Sessions entries marked sentenced
plus an open Criminal Court case. 32 of 35 bookings matched to an indictment list have that indicted
case open, but only 1 has no case marked sentenced. Sept 30 weekly run (General Sessions split
not recomputed): 1,346 held people sentenced on some cases with others open; 55 bookings matched
to an indictment list, 52 with that indicted case open and 2 with no case marked sentenced.

# Handling

Until checked, the [profile's](../analysis/population-profile.md) "no case marked sentenced" count
may understate pretrial detention. [Court linkage](../analysis/court-linkage.md) uses the status of
the indicted case itself. See the [decision](../decisions/2026-09-26-keep-sentenced-definition.md).
