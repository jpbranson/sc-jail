# Analysis

Private analysis products are built from local archive copies:

- A **population profile** of who is held on one day (below).
- A **booking panel** that follows each booking through time; see
  [Booking panel](#booking-panel).
- Weekly **trends**, an **IML/XFER reconciliation**, **length of stay**, **money bond**,
  **court linkage**, and **re-booking** analyses, all rebuilt by the
  [weekly run](#weekly-analysis-run).

The staged analysis plan is recorded in [PLAN.md](../PLAN.md#further-analysis-plan---2026-09-23).
Source behaviors that affect these measures are kept in the
[source-quality log](SOURCE_QUALITY.md).

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
  grade, bond total, money-bond-only status, no-bond-set, bond types, detainer count,
  violation charge, earliest next court date, or case numbers, stamped with the detail
  collection time. Bond types were added on September 26 to tell a bond not yet
  assessed from other situations; panels built earlier lack the field. Detail pages are checked about daily, so changes are dated to
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


## Weekly analysis run

`scripts/weekly_analysis.py` refreshes a local mirror of the cloud archive and rebuilds
every product into `data/analysis/weekly/<Central date>/`, with `index.html` (status and
links), `run.json` (per-step status, timing, and readout readiness), and `logs/`.

```powershell
$env:PATH = "$PWD\.runtime\google-cloud-sdk\bin;$env:PATH"
.\.venv\Scripts\python.exe scripts\weekly_analysis.py
```

- The mirror is `data/snapshots/current`. `gcloud storage rsync` downloads only new or
  changed objects (seconds after the first copy), using the normal `gcloud auth login`
  sign-in. The run fails if the newest roster slot is more than three hours old.
- Steps run in separate processes: mirror, booking panel, profile, trends,
  reconciliation, length of stay, money bond, court linkage, and re-booking. If the panel
  fails its population check, the steps that use it are skipped and the run is marked
  incomplete; the others still run.
- Work goes to a `.partial-*` folder and is renamed at the end. A second run on the same
  date keeps the earlier folder as `<date>.previous-<time>`; nothing is deleted.
  A file lock prevents overlapping runs.
- `--skip-sync` rebuilds from the mirror as it is, and `--output-root` writes elsewhere.

The `SC-Jail-Weekly-Analysis` Windows task runs this on Wednesdays at 09:00 through
`scripts/run-weekly-analysis.ps1`, which adds the bundled gcloud CLI to `PATH` and
appends one line per run to `.runtime/weekly-analysis.log` (full output in
`weekly-analysis.out.log` and `.err.log`). The task runs only while the owner is signed
in, stores no password, and starts at the next opportunity if a run was missed. Install
or update it with `scripts\install-weekly-task.ps1`; remove it with
`Unregister-ScheduledTask SC-Jail-Weekly-Analysis`. If a run fails with an rsync error,
run `gcloud auth login` again.

Readouts: each analysis records whether it has enough collection time for its first
readout (`readout_ready` in its `summary.json`). Before then its report is marked
preliminary. Collection began on September 19, 2026, so readouts become available on or
after October 17 (bond, court timing), October 19 (length of stay), and December 18
(re-booking). Reconciliation and court match rates are usable now.

## Trends

`scripts/analysis_trends.py` lines up weekly profile summaries (and the September 23
baseline) by roster date and shows 23 measures side by side with the change since the
previous run: people held, time held, case status, charge grades, money bonds,
detainers, violation charges, court dates, and recent daily bookings and releases.
Rosters from different times of day can differ; each column names its roster time.

## Source reconciliation

`scripts/reconcile_sources.py` compares each XFER jail workbook version (regenerated about
every two hours) with the IML roster observation nearest the workbook's own timestamp,
within 20 minutes, by exact booking number. IML counts a booking as held with a blank or
future release date. It also compares book date, case numbers, detainer, and earliest
court date for bookings both list, and describes the bookings only one source lists by
committing authority, time since booking, and IML location.

September 25 (76 of 80 workbook versions aligned): 3,026 bookings were in both sources.
XFER listed 136 bookings the IML roster never showed, all booked more than a week earlier
(92 more than a year); 8 IML-held bookings were missing from XFER. Book dates matched IML
commitment dates for every shared booking and case-number sets matched for 2,913 of
3,026. See the [source-quality log](SOURCE_QUALITY.md).

## Length of stay

`scripts/length_of_stay.py` follows bookings first listed after collection began, from the
IML commitment date to the listed release date in whole days, with Kaplan-Meier estimates
(`src/sc_jail/survival.py`). Held bookings are censored at the latest roster; bookings that
leave without a release date are censored when last seen. A commitment date more than a
week before a booking was first listed marks an older stay, which is excluded.

Groups come from the record page after it fills in, not the first page fetched: charges
and bond entries appear a median of 6.5 hours after first listing, and a bond decision
(any bond type other than "Not Assessed") a median of 20.5 hours after. Charge grade and
detainer use the first page with case entries; bond situation and amount use the first
page with a bond decision. Record pages keep being fetched while released bookings stay
listed (a median of 64 hours), so this does not require someone to remain held.

Preliminary (6 days, September 25): 526 new bookings, 256 released; median stay 3 days;
71% still held after 1 day and 40% after 3 days. The first readout needs 30 days.

## Money bond

`scripts/bond_analysis.py` compares consecutive record-page versions with case entries to
find each booking's first new court-assessed bond, reduction, increase, recognizance entry,
or cleared total, and follows each to release. It also describes people held now on money
bond alone at or below $1,000, $5,000, and $10,000, and new bookings whose first bond
decision was that low. Changes are dated when seen (record pages refresh about daily).
Bond status is never treated as a court outcome.

Preliminary (September 25): 53 reductions (median cut 66%), followed by release a median
of 1 day later; 79 people held on money bond alone of $5,000 or less, a median of 19 days
so far, 36 of them more than 30 days. The first readout needs about four weeks.

## Court linkage

`scripts/court_linkage.py` joins the latest pending-hearings report to bookings by exact
booking number, and every archived calendar and indictment version by exact case number.
It classifies changes in each booking's earliest listed court date and measures time from
commitment to indictment, by the status of the indicted case itself.

Match rates (September 25): 518 of 519 pending-hearing rows matched to a booking list that
case on the booking's record; the report listed 327 of 3,027 held bookings. 1,223 held
bookings had a case on a Criminal Court calendar during collection and 586 on a General
Sessions calendar. Most court-date changes (1,212) are a passed date replaced by a new one,
a median of 10 days later; the daily record refresh cannot tell a continuance from a
scheduled next step. Court-date and indictment timing need four to eight weeks.

## Re-booking

`scripts/rebooking.py` follows each release listed during collection until the same IML
permanent ID is booked again, with Kaplan-Meier estimates. People whose permanent ID was
ever reassigned are left out (51 of 533 releases on September 25). This covers only this
jail during collection and is not a recidivism rate. The readout needs about 90 days.
