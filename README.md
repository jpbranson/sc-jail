# Shelby County jail

Two Python source collectors, case detail archives, and a small Flask dashboard.
Cloud collections run on UTC quarter hours; the local scheduler also attempts a
collection when started. The two county sources are measured separately:

- **IML:** distinct permanent IDs with a blank release date or one after today's
  Memphis date. The complete result set includes recently released records,
  which remain in the private archive but are excluded from the current count.
- **XFER:** distinct booking numbers in `/SCSO-InJail/SCSO-InJail.xls`. A person
  can have several charge rows and potentially several bookings.

IML individual pages and the relevant XFER criminal court reports are collected
in bounded batches after the population runs. Detail pages target a daily
refresh; court folders are checked each interval and unchanged files are verified
daily. See [case data, private exports, and refresh settings](docs/CASE_DATA.md).
The dashboard shows actual detail coverage and report backlog. It also charts
[repeat visits and time between visits](docs/REPEAT_VISITS.md) using distinct
bookings linked by IML permanent ID across the full archive.

The dashboard uses Shiny-like controls, Inter text, and minimal SVG charts.
All interface and chart text is at least 16 CSS px (12 pt). The public surface
contains aggregates; names, dates of birth, and source records stay in private
storage.

## Running now

As of September 23, 2026 UTC, the collectors and dashboard are deployed to Google
Cloud in `us-central1`.

- Dashboard: https://sc-jail-dashboard-xcucxqzc2q-uc.a.run.app
- Project: `sc-jail-research-20260922`.
- Cloud Scheduler invokes the private collector on UTC quarter hours.
- `/health` checks the dashboard process; `/api/freshness` returns HTTP 503 when
  population collection is unhealthy. `/api/status` retains the detailed status.
- The private archive is `gs://sc-jail-research-20260922-sc-jail-data`.
- A $15 monthly budget alert is configured; it is not a spending cap.

The migration verified all 5,858 files (about 136 MiB) by size and CRC32C.
The local collector, dashboard, temporary tunnel, and `SC-Jail-Local` restart
task were stopped during cutover. The local `data/` directory remains as a
backup of the migrated history; it no longer receives new cloud observations.

The first regular 9:00 a.m. Central cloud run completed successfully for both
population sources. See [cloud deployment and operations](docs/CLOUD.md).
The 0.2.0 audit improvements and release evidence are recorded in the
[technical audit](docs/AUDIT.md) and [verification record](docs/RELEASE_0_2_0.md).
The local setup below remains available for development or fallback. Starting
it does not pause Cloud Scheduler or synchronize the cloud archive. Before a
production fallback, pause the cloud job, let any active collection finish, and
copy the current cloud archive into a separate local directory; the cutover
backup no longer contains the full history.

## Local setup

Requires Python 3.12 or newer; development and the container use 3.13.
The launcher below starts collection, a dashboard, and a temporary tunnel; the
last command installs automatic local restart. These are not needed to operate
the deployed cloud services. For local work, leave `SCJ_BUCKET` unset and use a
separate `SCJ_DATA_DIR` if the cutover backup should remain unchanged.

PowerShell:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock
.\.venv\Scripts\python.exe -m pip install -r requirements-build.lock
.\.venv\Scripts\python.exe -m pip install --no-build-isolation --no-deps -e .
.\scripts\start-local.ps1
.\scripts\install-local-task.ps1
```

The existing workspace already has these dependencies and a verified
Cloudflare `cloudflared` binary under `.runtime/`. On a new machine, install
`cloudflared` from its official release and put the executable at
`.runtime/cloudflared.exe`, or run a tunnel separately:

```powershell
cloudflared tunnel --url http://127.0.0.1:8050
```

Direct commands also work on Linux/macOS using the environment's Python:

```text
python -m sc_jail collect
python -m sc_jail schedule
python -m sc_jail dashboard --port 8050
python -m sc_jail status
```

The dashboard binds to loopback unless `--host` is explicitly supplied. It has
no collection or file browsing endpoint. Use an OS service to supervise the two
long-running commands on Linux; Cloud Run uses a different request-driven mode.

Stop this project's local processes and disable its automatic restart:

```powershell
.\scripts\stop-local.ps1
```

Restart Python after changing code, retaining the tunnel URL and restart task:

```powershell
.\scripts\stop-local.ps1 -KeepTask -KeepTunnel
.\scripts\start-local.ps1
```

Logs and process IDs are in `.runtime/`. The launcher checks process identity
before acting, and shutdown includes the Python children of Windows' venv
launchers.

## Configuration

| Variable | Default | Meaning |
| --- | --- | --- |
| `SCJ_DATA_DIR` | `data` | Local archive root |
| `SCJ_BUCKET` | unset | Use a private Google Cloud Storage bucket instead of local disk |
| `SCJ_USER_AGENT` | project research identifier | HTTP identification; optionally add a contact URL |
| `PORT` | `8050` | Server port unless `--port` is provided |
| `SCJ_IML_TIMEOUT_SECONDS` | `420` | IML roster scan budget in seconds (maximum 480) |
| `SCJ_IML_PAGE_WORKERS` | `2` | Concurrent IML roster page requests (1 or 2) |

Both county appliances require the legacy TLS initial-handshake option.
Certificate and hostname checks remain enabled; no global TLS settings change.
The collectors use normal sessions, bounded retries, and at least 150 ms between
roster page request starts. IML reads at most two pages concurrently and validates
each page's exact range, the stable total, and unique result IDs before accepting
a complete roster. IML returns 30 records per page, so the number of requests
varies with roster size. Its scan has a seven-minute budget; population sources share
a nine-minute deadline so a slow IML scan leaves a bounded allowance for XFER.
IML logs progress every 20 pages and records successful scan duration. A shifted
or incomplete roster is rejected and the last good count remains visible.
They do not use browsers or download unrelated county folders.

## Storage and meaning

```text
data/
  public/index.json                 # aggregate dashboard index, latest 90 days
  private/checkpoints/*.json.gz     # latest normalized state and cumulative seen IDs
  private/observations/...          # daily checkpoints + quarter-hour change logs
  private/blobs/...                 # compressed originals and checkpoint data
  private/legacy/observations/...   # original manifests retained during migration
  private/court-reports/...         # immutable raw/normalized court report versions
  private/repairs/...               # backups before derived-data corrections
  private/failures/...              # durable failed-attempt records
```

Original XLS files and full IML result pages are retained. SHA-256 content keys
avoid storing identical downloads repeatedly; every successful polling interval
still gets an observation. Manifests contain collection start/end times, source
file modification time where available, counts, checksums, and blob references.
Snapshots are collected over a period of time, not at a single instant.
New observations also record application, parser, and source-build versions;
older manifests remain readable without those optional fields.

Normalized history now uses a full checkpoint on the first successful collection
of each UTC day, followed by record and ID changes. Duplicate charge rows are
preserved; unchanged collections need only a reference and checksum. The latest
state is cached for efficient collection. Raw source files remain unchanged.
See [storage, reconstruction, and migration](docs/STORAGE.md) for commands and
format details. Legacy migration backups are retained.

A failed or incomplete source never becomes a zero count. Last good data remains
visible with a failure or overdue notice. The two sources fail independently.
The unchanged XFER jail file is still downloaded each time so a same-size replacement
cannot be missed. Repeated successful work in the same quarter hour is skipped.

Arrivals/departures mean IDs appearing/disappearing between adjacent successful
slots no more than 20 minutes apart. The first observation and comparisons over
gaps have blank changes. They are not independently confirmed jail events.
Release dates have no time-of-day precision. The XFER file can update less often
than the collector; the dashboard shows both timestamps.

The 90-day dashboard index is a view limit, not a deletion policy. Export all
aggregate history from the selected archive:

```powershell
.\.venv\Scripts\python.exe scripts\export_archive.py --output data\exports\history.csv
```

With `SCJ_BUCKET` unset, this reads the local archive, which stopped updating at
cloud cutover. For the active archive, follow the
[cloud authentication and export setup](docs/CLOUD.md#work-with-the-active-cloud-archive).
That setup also applies to private exports and reconstruction commands.

Treat `data/` as private. It, local logs, downloaded reference code, environments,
and credentials are excluded from Git and cloud/container build contexts.
For a local archive, back up the whole data directory while collection is stopped.
The local cutover backup does not include subsequent cloud observations. Cloud manifests
and blobs remain in the regional bucket indefinitely; monitor growth. No
automatic deletion of research data is configured.

## Verification

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.lock
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check src tests scripts
```

Tests cover checkpoint/change-log reconstruction, migration, corruption,
retry recovery, parsers, synthetic Excel data, pagination and shifted results,
time zones, duplicates, interrupted writes, failure isolation, cloud generation
checks/leases, and dashboard empty/stale/error states. The checked-in Excel
fixtures contain only invented records.

Cloud Build runs the same tests and lint checks before building a deployable
image. Runtime, development, build-tool, and container-base versions are pinned.
To deliberately refresh runtime dependencies, run `python scripts/lock_dependencies.py`,
review `requirements.lock`, and repeat the checks above. See the
[technical audit and refactoring decisions](docs/AUDIT.md) for the recovery,
backup, performance, and failure-mode changes.

The repeated-heading correction repaired 39 historical XFER observations,
removing 20,168 heading rows across those observations. The latest repaired report
contained 3,128 bookings and 22,754 charge rows. All 77 observations then in the
archive passed reconstruction checks. Older reported counts included the heading
error; corrected manifests and dashboard history are authoritative. Counts will
change with later observations.

Desktop (1440 px) and mobile (390 px) browser checks passed: no page overflow,
charts loaded, range filtering worked, and visible UI text was at least 16 px.
The locked dependencies were built successfully in the Linux/Python 3.13 container.
The container passed endpoint checks at 0.25 CPU and 512 MiB, and both services
were deployed to Google Cloud. Live checks covered dashboard endpoints, all
four SVG charts, the aggregate CSV, the private collector's authentication, and
archive access policies. Deployment staging and service-account propagation
retries have regression checks.

Original references:
[jpbranson/shelby.county](https://github.com/jpbranson/shelby.county) and
[jpbranson/memphis.xfer](https://github.com/jpbranson/memphis.xfer).
See [PLAN.md](PLAN.md) and [DECISIONS.md](DECISIONS.md).
