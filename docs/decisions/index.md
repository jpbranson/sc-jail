# 2026-10-04

* [Accept IML roster rows with a blank permanent ID](2026-10-04-blank-permanent-id.md) - A roster row with a blank permanent ID is archived and counted as a booking but counts no one until IML assigns an ID.

# 2026-09-26

* [Run the weekly analysis as a local Windows task](2026-09-26-weekly-local-analysis.md) - The weekly analysis runs as a local Windows task under the owner's sign-in from a gcloud-synced mirror, keeping person-level analysis off the cloud services.
* [Group new bookings by the filled-in record page](2026-09-26-filled-in-record-page.md) - New bookings are grouped by the record page after it fills in, not the first page fetched, which usually predates charges and bonds.
* [Keep the "no case marked sentenced" definition for now](2026-09-26-keep-sentenced-definition.md) - The profile keeps its "no case marked sentenced" definition until the meaning of "Sentenced" on General Sessions entries is checked.
* [Keep the project under $5 a month](2026-09-26-under-5-dollars.md) - The owner requires this project to cost under $5 a month, tracked by a weekly projection with and without the billing account's free allowances.
* [Lower the budget alert to $5](2026-09-26-budget-alert-5.md) - The budget alert drops from $15 to $5 with the same actual-spend and forecast thresholds; it alerts but does not cap spending.

# 2026-09-23

* [Treat immutable observations as the commit journal](2026-09-23-observations-as-journal.md) - Immutable observations are the commit journal, and checkpoints and indexes are repairable projections reconciled across slot boundaries.
* [Add no database, queue, or framework for this workload](2026-09-23-no-new-infrastructure.md) - Keep Cloud Run, Storage, and the four source adapters, adding no database, queue, or frameworks for this single-writer workload.
* [Narrow collector access and add an independent backup](2026-09-23-narrow-collector-access.md) - The collector can create and read history but overwrite only projections, backed by seven-day recovery and a separately permissioned, versioned daily backup.
* [Stage repeat analysis and keep dashboard data through outages](2026-09-23-staged-repeat-analysis.md) - Repeat-analysis progress is staged privately and only complete results are published; the dashboard keeps validated data through storage outages.
* [Pin and test builds before publishing images](2026-09-23-pinned-tested-builds.md) - Pin build tools and the container base, test in Cloud Build before publishing an image, preserve deployment tuning, and record parser and build provenance.
* [Run analysis on local archive copies and publish aggregates only](2026-09-23-local-aggregate-analysis.md) - Analysis reads local archive copies under the ignored data/ directory, never the live bucket, and publishes only aggregates with counts below ten suppressed.
* [Base time-based analysis on a validated booking panel](2026-09-23-validated-booking-panel.md) - Time-based analysis uses a booking panel that must reproduce every archived IML population, keeping ID and release-date changes as timed histories.

# 2026-09-22

* [Deploy in a dedicated project and stop local collection](2026-09-22-dedicated-project.md) - Deploy in the dedicated sc-jail-research-20260922 project in us-central1, hand quarter-hour collection to Cloud Scheduler, and keep local history as a backup.
* [Separate service deployment from Scheduler activation](2026-09-22-deferred-scheduler.md) - Deploy services before activating Scheduler so existing history can be copied and checksum-verified before cloud collection begins.
* [Use separate least-privilege service identities](2026-09-22-separate-identities.md) - The collector, dashboard, scheduler, and builder each get their own identity, with dashboard storage limited to public/ and an authenticated collector.
* [Use /health for cloud process checks](2026-09-22-health-endpoint.md) - Cloud process checks use /health, keeping /healthz only as a local alias because Google's frontend returned 404 for it.

# 2026-09-19

* [Target Cloud Run, Scheduler, and private Cloud Storage](2026-09-19-cloud-run-scheduler-storage.md) - Run on scale-to-zero Cloud Run with Cloud Scheduler and private Cloud Storage, which fits near-zero cost better than an always-on server.
* [Keep the two sources independent](2026-09-19-independent-sources.md) - One population source failing must not erase the other source's observations or the last successful population.
* [Use a Python Flask dashboard with minimal charts](2026-09-19-flask-dashboard.md) - A Flask dashboard with Shiny-like styling and minimal charts serves short HTTP requests, avoiding the cost of persistent dashboard sessions.
* [Keep person-level source files private](2026-09-19-private-person-level-files.md) - Person-level source files stay private; the dashboard exposes only aggregates and collection health.
* [Scope XFER to the jail report](2026-09-19-xfer-jail-report-scope.md) - Collect the XFER jail report rather than the unrelated county court, health, and purchasing folders the old project downloaded.
* [Count distinct XFER bookings separately from IML people](2026-09-19-xfer-distinct-bookings.md) - The XFER report has several charge rows per booking, so it is shown as distinct bookings, separate from IML's distinct permanent IDs.
* [Enable the legacy TLS option only for county sessions](2026-09-19-legacy-tls-option.md) - Both county servers need a legacy TLS handshake option, enabled only in their HTTP sessions with certificate and hostname checks kept.
* [Fetch the jail spreadsheet every interval](2026-09-19-fetch-workbook-each-interval.md) - Download the jail spreadsheet each interval and deduplicate by content hash, because filename and file size cannot reliably detect changes.
* [Retain private observations indefinitely](2026-09-19-indefinite-retention.md) - Keep private observations indefinitely but only 90 days in the dashboard index, preserving research history while keeping queries small.
* [Separate the collector and dashboard services](2026-09-19-collector-and-dashboard-services.md) - Cloud deployment uses one authenticated HTTP collection service and a separate aggregate-only dashboard, both with zero minimum instances.
* [Store daily checkpoints and quarter-hour change logs](2026-09-19-checkpoints-and-change-logs.md) - Normalized history is stored as daily checkpoints plus quarter-hour record and ID changes, checksum-verified, with a cached current state to keep cloud reads small.
* [Keep raw source archives unchanged](2026-09-19-keep-raw-archives.md) - Raw source archives and downloads stay unchanged, and original manifests and blobs are kept as private backups when history is migrated.
* [Remove repeated XFER headings and repair history](2026-09-19-remove-xfer-repeated-headings.md) - Remove repeated spreadsheet headings from XFER records and repair historical counts and change logs, keeping original reports and repair backups.
* [Collect IML detail pages in bounded batches](2026-09-19-iml-detail-batches.md) - IML detail pages are collected in bounded batches after the population runs, aiming for a daily refresh with visible coverage and per-record check times.
* [Expand XFER to criminal court reports](2026-09-19-xfer-court-reports.md) - Collect criminal calendars, indictments, pending hearings, and the dispositions folder, downloading changed reports and verifying the others daily.
* [Keep detail HTML on meaningful change and every court file version](2026-09-19-detail-html-versions.md) - Keep IML detail HTML only when meaningful fields change and skip images; keep each court file version compressed with structured rows and provenance.
* [Export individual records privately as JSON lines](2026-09-19-private-jsonl-exports.md) - Individual records stay private and are exported as JSON lines; the dashboard adds only aggregate coverage, freshness, and collection health.

# Superseded

* [Configure a $15 monthly budget alert](2026-09-22-budget-15.md) - A $15 monthly budget alerts at 50%, 90%, and 100% of actual spend and 100% of forecast; it notifies but does not cap spending.
* [Start the local fallback while cloud setup waits](2026-09-19-local-fallback.md) - With no Google Cloud login or project configured locally, start the local fallback and supply a repeatable cloud deployment script.
* [Run local collection on UTC quarter hours under a Windows check](2026-09-19-local-quarter-hour-schedule.md) - Local collection starts on UTC quarter hours, retries a failed source within the slot, and is supervised by a one-minute Windows check.
* [Use a Cloudflare Quick Tunnel for temporary remote viewing](2026-09-19-quick-tunnel.md) - A Cloudflare Quick Tunnel provides temporary remote viewing; its URL is temporary and the computer must stay awake and connected.
