# Population profile

`scripts/profile_population.py` summarizes who is currently listed as held, using
the IML roster and the latest archived record page for each booking. It writes a
private `summary.json` and a self-contained `report.html` with aggregate counts only.
Counts from 1 to 9 appear as "<10" in the HTML report.

## Running it

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

## Definitions

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

## First results, September 23, 2026

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
