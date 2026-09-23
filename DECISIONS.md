# Decisions

Entries describe decisions at the date shown. The September 22 cloud cutover and
September 23 reliability release supersede the initial local-only operating state.

- 2026-09-19: Target Google Cloud Run, Scheduler, and private Cloud Storage.
  Scaling to zero is a better fit for near-zero cost than an always-on server.
- 2026-09-19: Keep the two sources independent. One source failing must not
  erase the other source's observations or the last successful population.
- 2026-09-19: Use a Python Flask dashboard with Shiny-like styling and minimal
  charts. Short HTTP requests avoid paying for persistent dashboard sessions.
- 2026-09-19: Keep person-level source files private; the dashboard exposes
  aggregates and collection health.

- 2026-09-19: Scope XFER to the jail report, rather than downloading unrelated
  county court, health, and purchasing folders from the old project.
- 2026-09-19: The XFER report has multiple charge rows per booking. Display
  distinct bookings separately from IML's distinct permanent IDs.
- 2026-09-19: Both county servers require a legacy TLS handshake option. Enable
  it only in their HTTP sessions; keep certificate and hostname verification.
- 2026-09-19: Fetch the jail spreadsheet each interval and deduplicate by its
  content hash. Filename and file size alone cannot reliably detect changes.
- 2026-09-19: Retain private observations indefinitely; keep 90 days in the
  dashboard index. This preserves research history while keeping queries small.
- 2026-09-19: No Google Cloud login or project is configured locally. Start the
  local fallback now and supply a repeatable cloud deployment script.

- 2026-09-19: Local collection now starts on UTC quarter hours, retries a failed
  source within the slot, and is supervised by a one-minute Windows check.
- 2026-09-19: Cloud deployment uses one authenticated HTTP service for collection
  and a separate aggregate-only dashboard, both with zero minimum instances.
- 2026-09-19: A Cloudflare Quick Tunnel provides temporary remote viewing. Its URL
  is temporary and the computer must stay awake and connected.

- 2026-09-19: Store daily normalized checkpoints and quarter-hour record/ID
  changes, preserving duplicate charge rows. Verify history with checksums and
  cache the current state to keep routine cloud reads small.
- 2026-09-19: Keep all raw source archives and source downloads unchanged.
  Preserve original manifests/blobs as private backups when migrating history.

- 2026-09-19: Remove repeated spreadsheet headings from XFER records and repair
  historical counts and change logs. Keep original reports and repair backups.
- 2026-09-19: Collect IML detail pages in bounded batches after the population
  runs, aiming for daily refresh. Show actual coverage and per-record check times.
- 2026-09-19: Expand XFER to criminal calendars, indictments, pending hearings,
  and the dispositions folder. Download changed reports and verify others daily.
- 2026-09-19: Keep detail HTML when its meaningful fields change, and skip images.
  Keep each court file version compressed with structured rows and provenance.
- 2026-09-19: Keep individual records private and export them as JSON lines.
  The dashboard adds only aggregate coverage, freshness, and collection health.

- 2026-09-22: Deploy in the dedicated `sc-jail-research-20260922` project in
  `us-central1`. Cloud Scheduler now owns quarter-hour collection; stop the local
  collector, dashboard, temporary tunnel, and Windows restart task. Keep the
  migrated local history as a backup, not as the current archive.
- 2026-09-22: Separate initial service deployment from Scheduler activation so
  existing history can be copied and checksum-verified before cloud collection
  begins. `--defer-scheduler` leaves an existing job unchanged; pause it explicitly
  for later maintenance. `--scheduler-only` activates without rebuilding.
- 2026-09-22: Use separate collector, dashboard, scheduler, and builder identities.
  Restrict dashboard storage access to `public/`, require authentication on the
  collector, and enforce public-access prevention on the archive bucket. Allow
  the builder to read metadata only on its dedicated build bucket, in addition
  to its object and repository permissions.
- 2026-09-22: Configure a $15 monthly budget with actual-spend alerts at 50%, 90%,
  and 100%, plus a 100% forecast alert. This is a notification threshold, not a
  spending cap. Retain research data indefinitely; apply cleanup only to build
  artifacts and old container images.
- 2026-09-22: Use `/health` for cloud process checks. Keep `/healthz` as a local
  compatibility alias because Google's frontend returned 404 for that path.
  Check `/api/status` and actual observation slots to verify collection freshness.

See [cloud operations](docs/CLOUD.md) for the deployed resources and verification.

- 2026-09-23: Treat immutable observations as the commit journal and mutable
  checkpoints/indexes as repairable projections. Reconcile across slot boundaries,
  isolate corrupt source caches, and keep repeat-analysis rebuilds resumable.
- 2026-09-23: Preserve Cloud Run/Storage and the four source adapters. Add no
  database, queue, frontend framework, or generic repository framework for this
  single-writer workload. Extract only shared archive recovery, XLS identifiers,
  and chart rendering where duplication or startup cost justified a boundary.
- 2026-09-23: Give the collector create/read access to historical objects and
  overwrite access only to mutable projections. Enable seven-day archive recovery
  and an independently permissioned, versioned daily backup without source-delete
  propagation. Monitor freshness, supplemental coverage, and backup errors.
- 2026-09-23: Stage repeat-analysis progress privately and publish only complete
  fixed-target results. Keep validated dashboard data through storage outages,
  aggregate long-range change bars, and cache rendered charts with bounded size.
- 2026-09-23: Pin build tools/container base, test in Cloud Build before image
  publication, preserve deployment environment tuning, and record parser/build
  provenance. See [the audit](docs/AUDIT.md) for costs and remaining tradeoffs.

- 2026-09-23: Run analysis on local archive copies under ignored `data/`, never the
  live bucket, and publish aggregate results only, with counts below ten suppressed.
- 2026-09-23: Base time-based analysis on a booking panel that must reproduce every
  archived IML population. Keep permanent-ID and release-date changes as timed
  histories rather than final values, and count daily movement from first-seen and
  listed release dates rather than adjacent-slot changes, which skip collection gaps.

