# Shelby County jail collection and dashboard

Written before implementation: 2026-09-19.

**Current status (2026-09-23 UTC):** Release 0.2.0 is deployed to Google Cloud. The
collector and dashboard run in `sc-jail-research-20260922`; local collection and
its restart task are stopped. See [current operations](docs/CLOUD.md) and
[release verification](docs/RELEASE_0_2_0.md). The dated results below preserve the
original sequence; statements about pending cloud setup describe September 19,
not current status.

## Outcome

Collect the two sources used by `jpbranson/shelby.county` and
`jpbranson/memphis.xfer` every 15 minutes with Python. Preserve observations and
source files, expose collection health, and show a small aggregate dashboard.
Run locally immediately if cloud account setup requires the owner.

## Source investigation

1. Review both original R scrapers and inspect the live public sources.
2. Implement an independent adapter for the Shelby County IML roster and one
   for the public XFER file service. Use normal HTTP sessions rather than a
   browser where possible; retain TLS verification.
3. Determine current pagination, public login behavior, file metadata, and
   report formats from actual responses. Do not mistake an error/login page,
   truncated roster, or changed format for a successful empty observation.
4. Preserve the original useful measurements: roster records, distinct people,
   current population, and observed arrivals/departures. Treat changes across
   long collection gaps as uncertain. XFER is a separate report archive; only
   label a report as population after verifying its contents and definition.

## Cloud choice and cost

Target **Google Cloud Run**, **Cloud Scheduler**, and private **Cloud Storage**
in `us-central1`. Use a private HTTP collector triggered on UTC quarter hours,
plus a separate read-only Python dashboard. Both scale to zero. A small
fractional-CPU collector avoids Cloud Run Jobs' one-minute, one-CPU minimum.
Use authenticated scheduling, bounded request duration, one maximum collector
instance, retries, and idempotent observation keys. No always-on VM, managed
database, paid load balancer, or NAT gateway is necessary.

At 96 collections/day, one Scheduler job fits its three-job free allowance.
Cloud Run request-based billing and regional Storage free allowances should
cover light use; object operations and retained data may cost cents. Measure
run duration and compressed data sizes before making a firmer estimate.
Free allowances are shared across a billing account and are not a spending
cap. Document storage growth, image storage, network use, and budget alerts.

Alternatives considered: GitHub Actions schedules can be delayed or dropped;
Oracle free VMs can be reclaimed as idle; Google's free VM still incurs an
external IPv4 charge. Cloudflare's free Worker CPU allowance is too small for
the likely multi-page Python parsing workload.

Pricing and limitations checked 2026-09-19:

- https://cloud.google.com/run/pricing
- https://cloud.google.com/scheduler/pricing
- https://cloud.google.com/storage/pricing
- https://docs.cloud.google.com/free/docs/free-cloud-features
- https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule
- https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm
- https://cloud.google.com/vpc/network-pricing
- https://developers.cloudflare.com/workers/platform/limits/

## Implementation

1. Create a small installable Python package, explicit configuration, locked
   dependencies, and command-line entry points.
2. Build source adapters with connection/read timeouts, bounded retries,
   polite pagination, schema checks, and independent failure reporting.
3. Store timestamped manifests and compressed, content-addressed source data.
   Keep historical records separate from a compact dashboard index. Provide
   the same file/object interface for local disk and Cloud Storage; make
   state updates atomic and reject concurrent conflicting writes.
4. Run local collection on UTC-aligned 15-minute boundaries with overlap
   protection and logs. Record failures and preserve the last good data.
5. Build a Flask dashboard in Python with a plain Bootstrap/Shiny-like
   sidebar, white surfaces, blue controls, and minimal chart decoration.
   Use Inter or a similar sans-serif at a minimum of 16 CSS px (12 pt),
   including chart labels. Show source freshness, population history, observed
   changes, and XFER collection status. Public views contain aggregates only;
   archive files are private and excluded from source control.
6. Provide a container and repeatable Google Cloud deployment configuration,
   least-privilege service accounts, a protected collector endpoint, and
   operational instructions. If no usable cloud account is configured, start
   the collector and dashboard locally and expose the dashboard through a
   Cloudflare Quick Tunnel if available.

## Verification and handoff

- Test pagination/completeness, date interpretation, duplicate observations,
  failure isolation, changed report detection, atomic persistence, and the
  dashboard's honest empty/stale states with synthetic fixtures.
- Run a real collection and inspect its counts, completeness, timing, and
  stored artifacts; do not present synthetic fixtures as collected data.
- Verify dashboard routes, readable chart output, and deployment configuration.
- Leave local processes running if cloud deployment is blocked. Record exact
  startup/stop commands, the local/remote URLs, and the required cloud setup.
- Keep `DECISIONS.md` as a brief plain-English record, adding only decisions
  that affect data quality, cost, operation, or user-visible behavior.

## Progress

- [x] Review original scraper source and current provider documentation.
- [x] Write initial design before implementation.
- [x] Verify live source behavior.
- [x] Implement and test collection/storage.
- [x] Implement and verify dashboard.
- [x] Add cloud deployment and operating instructions.
- [x] Run collection and dashboard locally or in the cloud; record results.
- [x] Deploy to Google Cloud, verify the archive migration, and stop the local
  fallback (2026-09-22).


## Execution result — 2026-09-19

Implemented both source adapters, immutable private archives, atomic local/cloud
storage, a quarter-hour scheduler, the dashboard, tests, a container, and a
repeatable Google Cloud deployment script. The XFER adapter focuses on the
verified jail workbook rather than unrelated county folders.

Both sources have completed multiple live collections. A 09:00 UTC scheduled
run completed with 110 roster pages and 3,003 current people; the report had
3,151 distinct bookings. The dashboard is running at http://127.0.0.1:8050 and
through the Quick Tunnel recorded in README.md. Windows checks for stopped
local processes every minute while the user is signed in.

Cloud setup is ready for the owner to run, but no cloud resources were created:
Google Cloud login, project selection, and billing setup are still needed.
The deployment dry run and Linux dependency resolution pass; actual cloud
execution remains unverified. See docs/CLOUD.md for cost estimates and setup.

## Checkpoint and change-log storage - 2026-09-19

1. Save a complete normalized checkpoint on the first successful collection of
   each UTC day. Store record additions/removals and ID-set changes in later
   observation manifests; unchanged collections need only a history reference.
2. Canonicalize row order, preserve duplicate rows, and verify before/after
   state hashes. Use another full checkpoint if a change log would be larger.
3. Cache the latest normalized state in the existing mutable collector state
   so regular collection does not replay a day of cloud objects.
4. Support reconstruction of both old snapshots and new change logs, with
   explicit failure for missing, corrupt, or inconsistent history.
5. Migrate existing manifests under the collector lock, verify reconstruction,
   and retain original manifests/blobs as private migration backups. Keep all
   raw source files and existing download behavior.
6. Test day rollover, duplicate rows, corrections, unchanged data, corruption,
   retry recovery, migration, and local/cloud storage; restart local collection
   and verify a live observation uses the new format.


## Checkpoint implementation result - 2026-09-19

Implemented daily normalized checkpoints, embedded quarter-hour change logs,
checksum-verified reconstruction, and a mutable current-state cache. Added
migration and reconstruction commands, with operating details in docs/STORAGE.md.

All 65 tests and lint checks pass. Converted and verified 40 existing observations,
preserving original manifests and blobs as private backups. A historical export
reconstructed all 23,353 records from the original XFER observation. The
dashboard and tunnel remained running during the collector restart.

Both sources saved and verified new-format observations for the 13:30 UTC slot:
IML used a 514-byte unchanged manifest, and XFER used a 2,522-byte change-log
manifest. Reconstruction matched the original HTML/XLS data, including duplicate
rows and ID sets. IML's initial source request hit the existing time limit; its
automatic retry succeeded. Both sources now report normal collection.

Raw-source retention, source requests, dashboard behavior, and the 15-minute
schedule are unchanged. Temporary validation copies were removed; migration
backups remain. Cloud deployment still awaits the account setup described above.


## Detail and court-report expansion - 2026-09-19

1. Reject repeated XFER column-heading rows while preserving genuine duplicate
   charge rows. Repair all affected normalized observations, counts, ID sets,
   change logs, and the public index under the collector lock. Back up every
   original manifest before replacement and make repair safe to resume.
2. Inspect live IML detail sections and criminal court report layouts. Preserve
   repeated cases, bonds, hearings, aliases, and detainers as structured data;
   validate identity and required sections before accepting a detail page.
3. Keep the 15-minute population collections first. Use the remaining bounded
   execution time for a rotating IML detail queue, prioritizing new or changed
   bookings and then overdue records. Expose coverage and retrieval times;
   do not imply every detail page is refreshed every 15 minutes.
4. Monitor the General Sessions and Criminal/State Criminal court calendar,
   indictment, pending-hearing, and disposition folders. Download new/changed
   reports in bounded batches, recheck unchanged files periodically, and keep
   unsupported layouts explicit rather than silently losing columns or rows.
5. Reuse compressed content-addressed blobs and checkpoint/change-log history
   for detail records. Store court reports once per version with structured
   rows and provenance. Keep images out of collection and avoid new copies of
   semantically unchanged detail HTML. Preserve existing raw archives.
6. Provide private exports and aggregate coverage/status on the dashboard.
   Test parsing, history repair/recovery, selective refresh, failures, and
   storage reuse; run live bounded checks and restart local scheduled work.


## Detail and court-report expansion result - 2026-09-19

- Corrected 39 historical XFER observations, removing 20,168 repeated heading
  rows across them. Rebuilt counts, seen IDs, interval changes, caches, and the
  public history; verified all 77 observations then present. Original manifests
  and raw reports remain available. Historical XFER counts earlier in this plan
  predate this correction; use the repaired archive for analysis.
- Implemented identity-checked IML details, including charges, bonds, hearings,
  aliases, incarceration fields, and detainers. Added a bounded daily refresh
  queue, separate check timestamps, daily checkpoints/change logs, and private
  HTML versions for semantic changes. Images are not fetched.
- Added selective collection of General Sessions and Criminal Court calendars,
  indictments, and pending hearings; monitor the empty dispositions directory.
  Preserve raw and normalized content versions, periodically verify unchanged
  files, and expose unsupported formats explicitly.
- Added private JSON-lines exports with provenance and an aggregate dashboard
  coverage panel. Population observations remain independent and commit first.
- Restarted local collection and the dashboard while retaining the existing
  Quick Tunnel and Windows supervisor. The initial live pass successfully saved
  80 details and 8 court reports; histories and exports verified. The remaining
  backlog will be collected by subsequent scheduled passes.

See docs/CASE_DATA.md for field coverage, refresh settings, storage tradeoffs,
initial measured sizes, and export commands. Cloud account setup remains pending.

Final verification: all 95 tests and lint checks pass. Both private export CLI
commands ran successfully. The local dashboard and existing Quick Tunnel return
current aggregate coverage, and the Windows supervisor is enabled with the final
collector and dashboard code running.

## Google Cloud deployment result - 2026-09-22

Deployed both services in `us-central1` under `sc-jail-research-20260922`.
Migrated 5,858 archive files (142,835,436 bytes), verifying size and CRC32C before
enabling collection. The regular 14:00 UTC slot completed successfully for both
population sources. The dashboard, four SVG charts, CSV, source status, and
collector authentication passed live checks; all 111 tests and lint passed.

Stopped the local collector, dashboard, tunnel, and Windows restart task. Kept
the local archive as a cutover backup. A $15 monthly budget alert is configured;
it does not cap spending. See [CLOUD.md](docs/CLOUD.md) for the live URLs,
permissions, migration procedure, and commands for the active archive.

## Reliability release result - 2026-09-23 UTC

Deployed 0.2.0 with recovery from committed observations, resumable repeat
analytics, narrower collector permissions, daily versioned backups, product
freshness alerts, and dashboard caching during storage outages. Cloud Build ran
132 tests and lint before publishing the image. A paused release backup matched
6,444 objects by name, size, and CRC32C, and live collection resumed successfully.
See the [audit](docs/AUDIT.md) and [release record](docs/RELEASE_0_2_0.md) for the
scope, immutable image digest, verification evidence, and remaining limits.

## Further analysis plan - 2026-09-23

The first [population profile](docs/ANALYSIS.md) describes who is held on one day.
The following steps turn the archive into measures of what happens over time. All
analysis reads local archive copies, keeps person-level files under ignored `data/`,
and publishes aggregates only.

1. **Booking panel (now).** Replay committed roster and detail observations into one
   private row per booking: first/last seen, presence spans, listed release date and
   when it appeared, outcome (held, released, disappeared without a release date),
   and dated changes in commitment date, case status, charge grade, bond, detainers,
   and next court date. Mark bookings present at coverage start as left-truncated and
   open bookings as censored. Record missed collection slots, including the recurring
   07:00 UTC roster failures. Rebuild each archived IML population from the panel and
   require an exact match before later steps use it.
2. **Length of stay for new bookings (first readout ~30 days).** Follow bookings first
   seen after coverage began. Estimate time to release with Kaplan-Meier curves by
   charge grade, bond type/amount, and detainer status, and report how many very short
   stays fall between collections.
3. **Money bond and pretrial detention (~4-6 weeks).** Use detail changes to find bond
   reductions, increases, and new bonds; measure time from a change to release and
   waits for people held on low bonds. Keep bond status separate from court outcomes.
4. **Court linkage (~4-8 weeks).** Join pending hearings by booking number and
   calendars/indictments by exact case number, never by name. Measure match rates
   first, then court-date postponements and time from commitment to indictment for
   people without a sentenced case. Dispositions remain unavailable.
5. **Trends and reporting (ongoing).** Rerun the profile weekly from fresh snapshots,
   track composition over time, reconcile IML against XFER, add repeat-booking measures
   after about 90 days of coverage, and keep a short record of source-quality issues.

Order: 1, then 5's weekly run, then 2-4 as data accumulates.

## Booking panel result - 2026-09-23 UTC

Implemented `scripts/build_panel.py`. It replays the September 23 snapshot's 333 roster
observations into 3,584 booking rows with presence spans, release-date history,
permanent-ID history, outcomes, truncation flags, and dated detail-fact changes. Every
archived IML population is reproduced exactly; the build fails on any mismatch.

Validation exposed two source behaviors the first design missed: 54 bookings changed
permanent ID, and one release date was withdrawn and relisted. Both are now kept as
timed histories. The 07:00 UTC roster slot failed on September 20, 21, and 23 while the
roster shrank mid-scan. See [analysis](docs/ANALYSIS.md#booking-panel) for fields and
results. Next: schedule the weekly profile (step 5), then steps 2-4 as data accumulates.

