---
type: Analysis
title: Booking panel
description: Private one-row-per-booking history replayed from every committed IML roster and detail observation and validated against every archived population.
resource: ../../scripts/build_panel.py
tags: [analysis, iml, iml-details, privacy]
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:10:00Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:10:00Z }
sources:
  - id: analysis-l86
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/docs/ANALYSIS.md?plain=1#L86-L137
    title: docs/ANALYSIS.md lines 86-137, before the OKF migration
    last_modified: 2026-10-04T16:36:20Z
    author: claude-code/claude-opus-5-5
---

`scripts/build_panel.py` replays every committed IML roster and detail observation
into `bookings.jsonl`, one private row per booking, plus `summary.json` and
`missing-slots.json`. It omits names and dates of birth.

```powershell
.\.venv\Scripts\python.exe scripts\build_panel.py --data-dir data\snapshots\2026-09-23 --output data\analysis\panel
```

The build then recomputes every archived IML population from the panel, using
the collector's [rule](../measures/iml-population.md) (distinct permanent IDs with a blank release date or one after
that moment's Central date). Any mismatch writes the files but exits with an error,
so later analysis should not use them. A four-day archive takes about three minutes,
mostly to verify detail history.

Each row contains:

- `first_seen_at`, `last_seen_at`, and `spans`: presence intervals across complete
  rosters. A missed collection slot does not split a span; absence from a successful
  roster does. `reappearances` counts extra spans.
- `release_history` and the final `release_date`/`release_listed_at`. The roster can
  list, withdraw, and relist a release date, so each change is kept
  ([source-quality entry](../source-quality/iml-release-date-relisted.md)).
- `permanent_id_history`: IML [sometimes reassigns](../source-quality/iml-permanent-id-changes.md) a booking's
  permanent ID. Counting
  uses the ID in effect at each moment; counting every ID ever seen inflates the
  population. A [blank ID](../source-quality/iml-blank-permanent-id.md) (a booking listed before IML assigned one) counts no one and
  is left out of `permanent_ids`.
- `outcome`: `released` (release date listed), `held` (on the latest roster without
  one), or `disappeared` (left the roster without a listed release date).
- `left_truncated`: present in the first observation, so the booking began before
  coverage and its full stay is unknown. Held bookings are right-censored.
- `details`: one entry per change in commitment date, case status, most serious
  grade, bond total, money-bond-only status, no-bond-set, bond types, detainer count,
  violation charge, earliest next court date, or case numbers, stamped with the detail
  collection time. Bond types were added on September 26 to tell a bond not yet
  assessed from other situations; panels built earlier lack the field. Detail pages are [checked about daily](../source-quality/iml-details-daily-refresh.md), so changes are dated to
  when they were seen, not when they happened.

# Panel results, September 23, 2026

- 3,584 bookings from 333 roster observations; all 333 populations matched.
- 3,285 were present at coverage start. By the snapshot, 526 had a listed release,
  3,057 were held, and 1 left the roster without a release date.
- 54 bookings changed permanent ID (the same bookings the [repeat-visit summary](../measures/repeat-visits.md)
  excludes as conflicting). One release date was withdrawn and relisted. No booking
  left and later reappeared.
- 45 quarter-hour roster slots were missed, all but one before the September 22
  cloud cutover. The 07:00 UTC slot also fails most nights; see
  [cloud monitoring](../operations/monitoring-and-limits.md).
- Detail versions recorded 724 next-court-date changes, 251 bond-total changes,
  186 case-status changes, and 123 changes in most serious grade.

Latest weekly run (September 30, 2026): 4,174 bookings from 1,025 roster observations, and
every archived population matched; 182 bookings had changed permanent ID. 53 roster slots
were missed, 9 of them after the cutover, and the 07:00 UTC slot had not failed since
September 23 (it failed on September 20, 21, and 23; see the
[source-quality entry](../source-quality/iml-0700-roster-shrinks.md)).
