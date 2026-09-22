# Case detail and court-report collection

Population collection still runs every 15 minutes. After both population
adapters have committed their results, the same process spends bounded time on
court reports and IML individual pages. There is no additional cloud service,
database, or Scheduler job.

## IML individual pages

The collector initializes a normal IML search session and visits the detail
pages linked by the most recent complete roster. It checks both booking number
and permanent ID before accepting a response. It collects:

- Inmate and physical information, plus incarceration and housing fields.
- Aliases, charges (case number, offense date, code, description, grade, degree).
- Separate bond entries and their amounts, types, status, posting fields, and
  source totals. Bond status is not a court disposition.
- Hearing information and detainers, including complaint number/date and the
  issuing and setting authorities when published.

Dates, amounts, case numbers, and source labels retain their published meaning.
Do not sum repeated bond values across charge rows. Repeated charges and aliases
are preserved. Names are not used to join people or cases.

Each pass attempts at most 80 pages within 120 seconds. New/unfetched bookings,
changed roster entries, and then oldest overdue pages receive priority. A failed
page waits an hour before another attempt; three consecutive page failures end
the batch. The target revisit interval is 24 hours, subject to source availability
and the execution budget. Detail-only changes are found on that rotation, not
necessarily at the next 15-minute population poll. The initial roster takes
multiple passes to cover. The public dashboard shows actual coverage and backlog.

The current detail cache contains only bookings in the latest roster. When a
booking disappears, its previously collected details remain reconstructable in
historical observations; disappearance is not a confirmed release. Every detail
export includes its own last successful retrieval and last semantic change times.
A roster older than two hours is not used to start a detail pass.

## XFER court reports

The following public folders are monitored each cycle:

| Folder | Report family | Useful identifiers and fields |
| --- | --- | --- |
| GS-Criminalcourtcalendar | General Sessions calendar | Party, connection type, case number/type, hearing date/time, location, officer, hearing type |
| CriminalCourtCalendar | Criminal Court calendar | The same calendar fields; its .txt files contain CSV |
| StateCriminalCourtCalendar | Daily indictment list | Case number, cross references, indictment date, defendant, offenses, location/judge, next hearing, published address fields |
| StateCriminalCourtCalendar | Pending hearings | Case/booking/indictment/AG numbers, offenses, hearing date/time/type, officer, session, attorney |
| GS-CriminalCourtDispositions | Dispositions | Folder monitored; no files were published at initial verification |

New or changed files are downloaded, up to eight per pass within 60 seconds.
The newest report from each family is considered before older backfill. All
currently listed reports are eligible; the initial backlog is drained over
subsequent cycles. Files with unchanged size and modification time are fetched
again after 24 hours to detect silent replacements. A failed download waits an
hour before another attempt. Metadata checks cannot detect a silent replacement
immediately; this is a deliberate request-volume tradeoff for court reports.

Schemas for the four populated report families were checked against live
files. CSV and XLS disposition reports with an unambiguous case-number header
can be normalized if published. Unexpected filenames or layouts are retained
as raw files with an explicit unsupported status. An HTML error page or truncated
download is a failure, never an empty court report. Empty valid calendars and an
empty dispositions folder are legitimate source states.

Court calendars contain parties and cases beyond the jail roster. Booking
numbers can connect the pending-hearing and jail reports. Preserve case numbers
as strings, including spaces and leading zeroes, and retain court/report context:
one field may be a composite indictment/booking number. No automatic name-based
matching or inferred court dispositions are performed.

## Storage choices

Both supplemental collectors use daily normalized checkpoints and record change
logs. Their current-state caches are overwritten, not accumulated every interval.

For IML, retrieval timestamps are stored separately from the detail records.
A successful unchanged check does not create another HTML blob or pretend that
the record changed. Raw HTML is archived on the first successful retrieval and
whenever the normalized content changes. Presentation-only HTML changes are not
retained as new versions. A downloaded page that fails parsing or identity checks
is kept as an explicitly unparsed private artifact, and does not replace the
last valid record. Images, including photographs, are not downloaded.

For courts, each downloaded content version gets one compressed raw file, one
compressed normalized table when supported, and a small provenance manifest.
SHA-256 addresses reuse identical bytes, including across filenames. Unchanged
periodic verification updates only retrieval metadata. Current listings form a
bounded working catalog; older report versions remain under
`private/court-reports/` even after the county removes their filenames.

The original full-roster HTML and jail XLS retention policy remains unchanged.
No research archives, migration backups, or repair backups were deleted.

## Private exports

Exports are newline-delimited JSON, suitable for Python's json module or
`pandas.read_json(path, lines=True)`. Keep output under the ignored data directory.

These commands use `SCJ_BUCKET` when set; otherwise they read `SCJ_DATA_DIR`
(default `data/`). Since September 22, the active archive is in Cloud Storage
and the local directory is the cutover backup. Complete the
[cloud authentication and export setup](CLOUD.md#work-with-the-active-cloud-archive)
to export current cloud observations.

All currently collected detail pages:

```powershell
.\.venv\Scripts\python.exe scripts\export_cases.py --source iml-details --output data\exports\iml-details.jsonl
```

Add `--booking EXACT_BOOKING` or `--case "EXACT CASE"` to filter. Add
`--slot 2026-09-19T18:30:00Z` to reconstruct that successful archived observation,
including its retrieval metadata. An unavailable detail page is absent from the
export; compare the dashboard's available/eligible counts.

Latest downloaded pending-hearing report:

```powershell
.\.venv\Scripts\python.exe scripts\export_cases.py --source xfer-courts --family pending_hearings --output data\exports\pending-hearings.jsonl
```

Without `--family`, exports use the latest downloaded report per family.
`--all-versions` includes every archived report version, including files no
longer listed by the county. `--slot` instead selects the catalog as of a
successful collection. These two options are mutually exclusive. Rows include
the source filename, modification time, first capture time, content hash, and
revision key. An unsupported report produces an explicit inventory row with a
raw-file reference rather than disappearing silently.

`scripts/reconstruct_observation.py` also accepts sources `iml_details` and
`xfer_courts` for full normalized states. Population CSV exports remain limited
to the two population sources. No person-level export endpoint exists on the
public dashboard; `/api/coverage` exposes only aggregate collection status.

## Configuration

| Environment variable | Default |
| --- | ---: |
| SCJ_DETAIL_BATCH | 80 pages |
| SCJ_DETAIL_BUDGET | 120 seconds |
| SCJ_DETAIL_REFRESH_HOURS | 24 hours |
| SCJ_COURT_BATCH | 8 files |
| SCJ_COURT_BUDGET | 60 seconds |
| SCJ_COURT_VERIFY_HOURS | 24 hours |

The overall collection execution budget takes precedence over these settings.
Population observations commit first; supplementary failures preserve those
results and the last successful case records. Coverage status records partial
failures and overdue passes. Local scheduling and the existing Cloud Run
collector both use this same path. Increasing batch sizes may increase traffic,
compute use, and storage; the dashboard reports actual progress rather than
assuming the configured daily target was met.

## Repeated XFER heading correction

The jail XLS repeats its complete column headings between printed pages. These
rows are now skipped after trimming surrounding whitespace; genuine duplicate
charge rows remain. The September 19 repair is already included in the migrated
cloud archive. This historical maintenance command is not a deployment step;
pause collection and let active work finish before any future repair:

```powershell
.\.venv\Scripts\python.exe scripts\repair_xfer_headers.py
```

The repair recomputes records, booking counts, cumulative seen IDs, and interval
changes, then rebuilds checkpoint/change-log chains and the public index. Every
original manifest is backed up under `private/repairs/xfer-headers-v1/` before any
replacement. The maintenance marker prevents XFER collection during an
interrupted repair; rerun the command to resume. Original raw spreadsheets and
earlier migration backups remain unchanged.


## Initial live verification - 2026-09-19

The first expanded pass collected 80 of 3,268 listed IML bookings and 8 of 37
listed court reports with no parsing failures. It took approximately 55 seconds
for details and 5 seconds for court reports after the population observations.
At that rate, the initial detail queue needs about 41 successful passes (roughly
10 hours); this is an estimate, not a guarantee during outages or roster changes.

The 80 raw detail pages used 277,236 compressed bytes; their initial normalized
checkpoint used 34,560 bytes. The eight court files used 383,370 compressed bytes
for originals and 224,835 for normalized rows. These are small initial samples,
not steady-state growth forecasts. Routine unchanged detail checks create no new
raw HTML, while changed records, new reports, and daily checkpoints still grow
the archive. Both supplemental histories reconstructed successfully and private
exports returned 80 details and 3,246 rows from the latest report in each family.
