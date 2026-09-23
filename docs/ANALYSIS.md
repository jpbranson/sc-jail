# Analysis

Two private analysis products are built from local archive copies:

- A **population profile** of who is held on one day (below).
- A **booking panel** that follows each booking through time; see
  [Booking panel](#booking-panel).

The staged analysis plan is recorded in [PLAN.md](../PLAN.md#further-analysis-plan---2026-09-23).

## Population profile

`scripts/profile_population.py` summarizes who is currently listed as held, using
the IML roster and the latest archived record page for each booking. It writes a
private `summary.json` and a self-contained `report.html` with aggregate counts only.
Counts from 1 to 9 appear as "<10" in the HTML report.

### Running it

The script reads a local copy of the archive, never the live bucket, so analysis
cannot touch collection state or its lease. Copy the cloud archive into the ignored
`data/` directory with the bundled gcloud CLI (a normal `gcloud auth login` is
enough; Application Default Credentials are not required):

```powershell
$env:PATH = "$PWD\.runtime\google-cloud-sdk\bin;$env:PATH"
gcloud storage rsync -r gs://sc-jail-research-20260922-sc-jail-data data\snapshots\2026-09-23
.\.venv\Scripts\python.exe scripts\profile_population.py --data-dir data\snapshots\2026-09-23 --output data\analysis\baseline
```

Re-running `rsync` into the same folder downloads only new objects. The snapshot is
a point-in-time copy, not a backup; the independent cloud backup remains authoritative.

### Definitions

- **Held:** a booking in the latest complete roster with no release date. The
  roster also lists recently released bookings, which are excluded.
- **Time held so far:** days from the record page's commitment date to the Central
  date of the roster. A current population over-represents long stays compared with
  everyone booked over a period, so this is not a length-of-stay estimate.
- **Case status:** from each case's bond-entry status. "Sentenced" cases are counted
  as sentenced; open, no-bond, and blank statuses are not. People with both are shown
  separately.
- **Most serious charge:** the highest charge grade, in the order FM (all listed
  FM charges are murder charges), felony classes A–E, misdemeanor classes A–C, then
  I/IE violation grades (probation, parole, and diversion violations).
- **Money bond alone:** every case is open with a court-assessed bond, the listed
  grand total is positive, and the record shows no detainer or violation charge.
  In the September 23 snapshot, the grand total matched the sum of case bond amounts
  for every such person.
- **Daily movement:** booking numbers first seen that Central day, and bookings with
  that listed release date, from the repeat-visit registry. Bookings present in the
  first observation, and the partial first and last days, are excluded. Missed
  collection slots delay when a booking is seen but do not drop it; very short stays
  between collections can be missed.

Adjacent-slot arrivals and departures on the dashboard are not used for daily totals:
before September 22, IML missed roughly one slot in five, and changes across those
gaps are intentionally left blank.

### First results, September 23, 2026

From the roster observed at 06:48 UTC (3,057 held; 3,055 with record pages):

- Median time held so far was 186 days; 34% had been held more than a year and 15%
  more than two years.
- 1,452 people (48%) had no case marked sentenced, with a median of 66 days held;
  245 of them had been held more than a year. Another 1,339 were sentenced on some
  cases with others open.
- 770 people were held on money bond alone. Their median total bond was $100,000;
  88 had totals of $5,000 or less and 125 of $10,000 or less.
- 675 people had a detainer, 643 a probation/parole/diversion violation charge, and
  539 at least one case with no bond set.
- About 72–90 new bookings were first seen per day on September 20–22, against
  43–89 listed releases.

These are descriptive counts from Sheriff-published fields, which can lag court
records. The archive began on September 19, so trends, seasonality, and repeat
bookings need more collection time.

## Booking panel

`scripts/build_panel.py` replays every committed IML roster and detail observation
into `bookings.jsonl`, one private row per booking, plus `summary.json` and
`missing-slots.json`. It omits names and dates of birth.

```powershell
.\.venv\Scripts\python.exe scripts\build_panel.py --data-dir data\snapshots\2026-09-23 --output data\analysis\panel
```

The build then recomputes every archived IML population from the panel, using
the collector's rule (distinct permanent IDs with a blank release date or one after
that moment's Central date). Any mismatch writes the files but exits with an error,
so later analysis should not use them. A four-day archive takes about three minutes,
mostly to verify detail history.

Each row contains:

- `first_seen_at`, `last_seen_at`, and `spans`: presence intervals across complete
  rosters. A missed collection slot does not split a span; absence from a successful
  roster does. `reappearances` counts extra spans.
- `release_history` and the final `release_date`/`release_listed_at`. The roster can
  list, withdraw, and relist a release date, so each change is kept.
- `permanent_id_history`: IML sometimes reassigns a booking's permanent ID. Counting
  uses the ID in effect at each moment; counting every ID ever seen inflates the
  population.
- `outcome`: `released` (release date listed), `held` (on the latest roster without
  one), or `disappeared` (left the roster without a listed release date).
- `left_truncated`: present in the first observation, so the booking began before
  coverage and its full stay is unknown. Held bookings are right-censored.
- `details`: one entry per change in commitment date, case status, most serious
  grade, bond total, money-bond-only status, no-bond-set, detainer count, violation
  charge, earliest next court date, or case numbers, stamped with the detail
  collection time. Detail pages are checked about daily, so changes are dated to
  when they were seen, not when they happened.

### Panel results, September 23, 2026

- 3,584 bookings from 333 roster observations; all 333 populations matched.
- 3,285 were present at coverage start. By the snapshot, 526 had a listed release,
  3,057 were held, and 1 left the roster without a release date.
- 54 bookings changed permanent ID (the same bookings the repeat-visit summary
  excludes as conflicting). One release date was withdrawn and relisted. No booking
  left and later reappeared.
- 45 quarter-hour roster slots were missed, all but one before the September 22
  cloud cutover. The 07:00 UTC slot also fails most nights; see
  [cloud monitoring](CLOUD.md#monitoring-and-limits).
- Detail versions recorded 724 next-court-date changes, 251 bond-total changes,
  186 case-status changes, and 123 changes in most serious grade.

