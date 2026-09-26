# Google Cloud deployment

## Current deployment

Initially deployed September 22, 2026; updated to 0.2.0 on September 23 UTC.
The live service configuration, Scheduler, backup settings, and public endpoints
were rechecked on September 23. See the [0.2.0 release record](RELEASE_0_2_0.md)
for the deployed image digest and release validation.

The collector received an early-detail-refresh fix at 04:55 UTC on September 23.
It now serves revision `sc-jail-collector-00005-ddm`, built from
`source-3b79f7a94a05796d4e7f`, with image digest
`sha256:cab94e326b8ca956088a552e329c20f242f44e96d738f3ca859ce805062edb5b`.
Cloud Build `b053b757-05fd-4e79-8894-c835ebc66c75` passed all 138 tests and lint
on Linux/Python 3.13; Windows checks also passed. Only the collector image changed;
the dashboard still uses the 0.2.0 release image. Details now queue at 20 hours
with oldest-first rotation, while the freshness limit remains 24 hours. See
[case-data settings](CASE_DATA.md#configuration) for the configurable lead and
its request-volume tradeoff. The previous collector image is retained in the
0.2.0 release record for rollback.

The first scheduled pass on that revision (05:00 UTC) refreshed 80 details with
zero page failures, finishing the detail stage at 05:03:47 UTC. It retained all
3,249 available records; 3,169 were fresh and 80 still overdue as the existing
daily-expiry wave continued. The oldest check advanced from 03:56 to 04:47 UTC
on September 22. The freshness endpoint correctly remained HTTP 503. This
verifies the deployed collection path, not full backlog recovery; the new lead
needs scheduled passes to work through pages collected under the old rotation.

- Project: `sc-jail-research-20260922` (number `564083380783`).
- Region: `us-central1`.
- Dashboard: https://sc-jail-dashboard-xcucxqzc2q-uc.a.run.app
- Private collector: https://sc-jail-collector-xcucxqzc2q-uc.a.run.app
- Archive: `gs://sc-jail-research-20260922-sc-jail-data`.
- Daily backup: `gs://sc-jail-research-20260922-sc-jail-backup`, at 05:10 UTC.
- Scheduler: `sc-jail-quarter-hour`, `*/15 * * * *` in UTC.
- Monitoring: four freshness uptime checks and a backup-error alert, with an
  enabled email notification channel.
- Monthly budget: $5 since September 26, 2026 (was $15), matching the owner's target of
  under $5 a month, with actual-spend alerts at 50%, 90%, and 100%, and a forecast alert
  at 100%. The budget does not cap spending.

All 5,858 local archive files (142,835,436 bytes) passed size and CRC32C
verification before scheduling was enabled. The local processes and restart
task were stopped; the unchanged local archive is a backup. Migration receipts,
deployment logs, the final image digest, and service URLs are in `.runtime/`.

The deployment uses dedicated collector, dashboard, scheduler, and builder
service accounts. The dashboard reads only `public/` objects, the archive
enforces public-access prevention, and unauthenticated collector calls return
403. The public `/health`, charts, API routes, and CSV export were checked live.

The regular 14:00 UTC (9:00 a.m. Central) execution on September 22 completed
with HTTP 200 at 14:02:08 UTC. Both population sources recorded successful
observations for that interval. All 111 regression tests and lint checks passed
at the initial cutover; the 0.2.0 suite has 132 passing tests. The local dashboard
port was confirmed closed after cutover.

## Chosen architecture

One private Cloud Run collector, one public read-only Cloud Run dashboard,
one Cloud Scheduler job, a private regional Cloud Storage archive, and a separate
daily Storage Transfer Service backup to another private bucket in `us-central1`.
Cloud Monitoring checks freshness and backup failures. Both Cloud Run services
have zero minimum instances, a configured maximum of one instance per revision,
0.25 vCPU, 512 MiB RAM, request-based billing, and
first-generation execution. The collector lease also prevents overlapping
collection across revisions.
The collector runs synchronously inside an authenticated request; it does not
depend on background threads surviving after a request ends.

Scheduler calls `POST /collect` every 15 minutes using its own service account
and an OIDC token with the service URL as audience. Only that identity gets
`roles/run.invoker` on the collector. The dashboard cannot run collection and
its identity can read only the archive's `public/` objects. The collector gets
object access to its dedicated archive bucket. A separate builder account can
write only its build bucket and Artifact Registry repository.

A conditional Cloud Storage lease prevents overlapping collectors; generation
preconditions protect updates. Source observations are immutable and recoverable
after a partially completed write. Retries skip sources already completed in a
slot. A Scheduler retry that arrives after its original 15-minute slot is
discarded instead of pretending to collect historical data.

Normalized records use daily full checkpoints and embedded change logs.
The mutable working state avoids replaying cloud objects during normal
collection. Raw source archives remain intact. See [storage details](STORAGE.md).

The bucket holds durable state; container filesystems are temporary. There is no
database server, VM, load balancer, NAT gateway, or paid domain.

## Expected cost

The table records the original population-only workload estimate in USD, with
light dashboard traffic and otherwise-unused account free allowances. Its pricing
assumptions were rechecked against the official sources below on September 23,
2026. Detail pages, court reports, repeat analytics, backups, and monitoring add
compute, requests, and storage; this baseline is not a forecast for the full
deployed workload or a zero-cost guarantee. The configured $5 alert is a budget
threshold, not a monthly cost estimate; see measured usage below.

| Component | Workload / allowance | Expected initial cost |
| --- | --- | --- |
| Cloud Run collector | 2,976 runs in a 31-day month; at 150 seconds/run and 0.25 CPU: 111,600 vCPU-seconds and 223,200 GiB-seconds | Within request-based free allowances |
| Dashboard | Short cached requests, no persistent sessions; scales to zero | Usually within the remaining free allowances |
| Scheduler | One job; three free jobs per billing account | $0 |
| Storage operations | Roughly 11 writes/run, plus daily normalized checkpoints; fewer than 35,000/month | About $0.15/month after 5,000 free Class A operations, plus any excess reads |
| Stored data | 5 GB-months free in an eligible region; identical source blobs deduplicated | Initially likely $0; grows with retained history |
| Builds / images | One small image; build inputs/logs deleted after 7 days, untagged images cleaned after 7 days with two recent versions retained | Usually small; image storage above the free allowance is billable |

The first regular cloud execution on September 22 completed in about two
minutes. One successful run does not establish a monthly average; measure
subsequent durations, retries, and archive growth. At 0.25 CPU, approximately
four minutes per collection would consume the request-based monthly CPU free
allowance before dashboard use or retries.

The 0.2.0 recovery and monitoring features add costs beyond that table:

- Daily backups add another retained copy, noncurrent backup versions, and
  listing/copy requests. Soft-deleted objects also incur storage charges during
  their recovery window. See [Storage pricing](https://cloud.google.com/storage/pricing)
  and [Storage Transfer pricing](https://cloud.google.com/storage-transfer/pricing).
- Each region's execution of an uptime check counts separately. Four checks at
  five-minute intervals produce 35,712 executions per region in a 31-day month.
  Monitoring includes one million executions per billing account per month, then
  charges $0.30 per 1,000. These requests also use the dashboard's Cloud Run
  resources, even when nobody opens the page. See
  [Monitoring pricing](https://cloud.google.com/products/observability/pricing).

The XLS measured 5.33 MB uncompressed / 1.13 MB compressed. If every poll produced
a different XLS, originals alone would add about 3.36 GB per 31-day month;
normalized data and roster pages add more. In the initial observations, the
XLS did not change, so content-addressed storage reused the same blob.
No indefinite free storage claim is made. Additional regional Standard storage
is approximately $0.02/GB-month. File downloads into Cloud Run are ingress;
dashboard traffic and requests to the county consume outbound allowance.

Free allowances are shared across the billing account. Retries, dashboard
traffic, unrelated workloads, long-term retention, and image size can increase
costs. The deployed project has a $5 monthly budget alert (September 26, 2026). Check billing after
the first day/week and review run duration and bucket growth. **Budget alerts do
not cap spending.** Pause Scheduler to prevent future scheduled collection;
let any in-flight request finish. Stored data can still incur charges. There
is no uptime guarantee at a strict $0 budget.

Pricing and configuration sources:

- [Cloud Run pricing](https://cloud.google.com/run/pricing)
- [Cloud Run fractional CPU requirements](https://docs.cloud.google.com/run/docs/configuring/services/cpu)
- [Scheduler pricing](https://cloud.google.com/scheduler/pricing)
- [Storage pricing](https://cloud.google.com/storage/pricing)
- [Free tier allowances](https://docs.cloud.google.com/free/docs/free-cloud-features)
- [Artifact Registry pricing](https://cloud.google.com/artifact-registry/pricing)
- [Custom Cloud Build accounts](https://docs.cloud.google.com/build/docs/securing-builds/configure-user-specified-service-accounts)

## Measured usage and cost - 2026-09-26

The owner's target is **under $5 a month** for this project. Measured use since the 0.2.0
release (median of full days, September 23 to 25, UTC), projected to an average month at
us-central1 list prices from the Cloud Billing Catalog (checked September 26):

| Item | Measured | Per month | Free allowance | Cost if this project gets the allowance | Cost if it does not |
| --- | --- | --- | --- | ---: | ---: |
| Collector | 20,385 billable s/day, 114 requests/day, 0.25 vCPU, 512 MiB | 158,800 vCPU-s; 317,600 GiB-s (both services) | 180,000 vCPU-s; 360,000 GiB-s | $0.00 (88% used) | $4.61 |
| Dashboard | 483 billable s/day, 3,551 requests/day (almost all uptime checks) | 111,500 requests | 2 million requests | $0.00 | $0.04 |
| Storage | 1.09 GiB billable: live 535 MB (archive + backup), soft-deleted 628 MB, noncurrent 6 MB | 1.09 GiB, growing 2.55 GiB/month | 5 GiB | $0.00 | $0.02 |
| Storage operations | 2,400 writes, 615 lists, 2,845 reads, 4,670 metadata reads a day | 94,900 Class A; 235,700 Class B | 5,000 A; 50,000 B | $0.52 | $0.57 |
| Container images | 0.38 GiB | 0.38 GiB | 0.5 GiB | $0.00 | $0.04 |
| Scheduler | 1 job | 1 job | 3 jobs | $0.00 | $0.10 |
| **Total** | | | | **$0.52** | **$5.38** |

Free allowances belong to the billing account, which has five billing-enabled projects.
If another project uses Cloud Run's allowance, this project's Cloud Run use is billed and
the total passes the $5 target. Only the billing console (Billing, Reports, grouped by
project and SKU, showing free-tier credits) can confirm which case applies; no billing
export is configured.

Other measurements behind the projection:

- Collector runs take a median 182 s (90th percentile 252 s, maximum 405 s). About 18
  runs a day fail because IML pagination shifts while the roster changes mid-scan (53 of
  55 IML failures), and Scheduler retries them; failed scans and retries are about 11% of
  collector time. Busy-minute CPU use (95th percentile) is 49% of the 0.25 vCPU; memory
  reaches 47% of 512 MiB at the 99th percentile, so memory should not be reduced.
- Archive growth is about 44 MB a day: IML roster pages 27 MB, XFER workbooks 14 MB,
  record pages and manifests 3 MB. The backup doubles it. Soft-deleted copies of
  overwritten projections (7-day recovery) add about 0.6 GB at steady state. Storage
  passes 5 GiB in about 1.5 months and would cost about $0.53 a month a year from now.
- The weekly mirror downloads about 1.4 GB a month, within the 100 GiB free monthly
  Cloud Storage download allowance.

The weekly analysis run now includes `scripts/usage_report.py`, which repeats these
measurements, projects both cases against the target (`--cost-target`, default $5), and
shows an alert on the run's index page when either case is at risk. It reads Monitoring
metrics, service sizes, and bucket totals only; it changes nothing.

## Owner setup and deployment

For a new environment, Google Cloud sign-in and an existing billing account are
required. The code does not create a billing account. This workspace has a
portable CLI at `.runtime/google-cloud-sdk/bin/gcloud.cmd`. From the repository
root, add it to the current PowerShell process's PATH:

```powershell
$env:PATH = (Join-Path (Get-Location) '.runtime\google-cloud-sdk\bin') + [IO.Path]::PathSeparator + $env:PATH
```

The examples use the project's installed virtual environment. On a new machine,
first follow [local dependency setup](../README.md#local-setup), stopping before
the local launcher commands. On Linux/macOS, substitute your environment's
`python` executable. The live project is already created and linked to billing;
use its ID for updates rather than creating another project.

1. Create/select a Google Cloud project and link billing. Install Google Cloud
   CLI and sign in with `gcloud auth login`. The deploying user needs permission
   to enable services, create the dedicated resources/service accounts, grant
   their IAM roles, and act as those accounts. A project owner can do the initial
   setup; routine collection does not use the owner's identity.
2. Review all commands without changing any cloud resources:
   `.\.venv\Scripts\python.exe scripts\deploy_gcp.py --project YOUR_PROJECT_ID --dry-run`.
3. For a new deployment with local history, prepare the services without starting
   collection:
   `.\.venv\Scripts\python.exe scripts\deploy_gcp.py --project YOUR_PROJECT_ID --defer-scheduler`.
   Follow the migration steps below, then activate collection with
   `.\.venv\Scripts\python.exe scripts\deploy_gcp.py --project YOUR_PROJECT_ID --scheduler-only`.
   An ordinary deployment or update uses
   `.\.venv\Scripts\python.exe scripts\deploy_gcp.py --project YOUR_PROJECT_ID`.

For example, preview an update to the deployed project with:

```powershell
.\.venv\Scripts\python.exe scripts\deploy_gcp.py --project sc-jail-research-20260922 --dry-run
```

Remove `--dry-run` to build and deploy the update. The script does not create
billing budgets; configure one separately for any new project.
Pass `--notification-email ADDRESS` to create an operational email channel.
Subsequent deployments reuse enabled channels without requiring the address again.
For a short maintenance cutover or rollback, `--image` accepts an already tested
immutable digest from this project's `sc-jail/app` repository and skips rebuilding.
Build and verify the image before pausing collection; retain its digest with the
release record. Mutable tags are rejected by this option. During a paused
cutover, combine `--image` with `--defer-scheduler` so deployment does not request
an immediate collection. Resume the existing job explicitly after verification.

`--defer-scheduler` leaves any existing Scheduler job unchanged. It supports
initial setup or a cutover whose existing job has already been paused explicitly.
`--scheduler-only` configures and requests an immediate run without rebuilding
services; it does not explicitly resume a paused job. Ordinary deployment also
configures and requests a run unless `--defer-scheduler` is supplied.
New service-account propagation failures during bucket permission binding are
retried with bounded backoff. The builder also gets bucket-metadata read access
on the dedicated build bucket, which Cloud Build requires for validation.

The script creates or updates dedicated `sc-jail-*` resources. Run it only in
the intended project. It builds on Cloud Build, so Docker need not run locally.
It enables seven-day soft deletion on the archive, creates a separate daily
backup with versioning, and limits the collector's overwrite/delete access to
mutable projections and its lease. Build objects alone have seven-day cleanup.
No deletion lifecycle is installed on the research archive. Existing collection
tuning variables are preserved when `SCJ_BUCKET` is updated on Cloud Run.
Cloud Build runs regression tests and lint before publishing the image.

Cloud Run's generated HTTPS URL is printed at the end. The initial Scheduler
invocation is asynchronous; verify the first regular quarter-hour execution in
Scheduler logs and `/api/status`. An HTTP 200 alone can mean a completed slot
was skipped or an expired scheduled attempt was ignored. Confirm both sources'
observation slots and successful retrieval times advance. Verify unauthenticated
collector calls are rejected and the dashboard identity has no access to
`private/`. Review Cloud Run/Scheduler logs for failures.
An immediate manual Scheduler run can replay an expired scheduled timestamp and
be correctly skipped. Wait for the next regular quarter hour, or use an
authenticated `POST /collect` without a Scheduler timestamp to verify a current
collection; do not bypass the collector's stale-replay check.

The Linux container and staged deployment were verified on September 22, 2026.
The service setup and scheduler activation are separate so archive migration
can finish before collection starts. Regression checks cover that separation
and retries for newly created service accounts.

## Move existing local history

This cutover is complete for the deployed project. Do not copy the frozen local
backup over its newer cloud archive. For another migration, use a maintenance
window so no collector modifies the data during copy:

1. For initial setup, use `--defer-scheduler` so no cloud job exists yet. For an
   existing deployment, pause the job:
   `gcloud scheduler jobs pause sc-jail-quarter-hour --location us-central1 --project YOUR_PROJECT_ID`.
2. Wait for any cloud collection to finish; pausing Scheduler does not cancel
   an active request. Let the local collection finish, then stop local processes
   using `scripts/stop-local.ps1` and confirm the restart task is disabled.
3. If the cloud bucket already contains research observations, back it up and
   reconcile overlapping slots first. Do not overwrite a newer cloud index with
   an older local copy.
4. For an empty destination archive, copy:
   `gcloud storage rsync data/private gs://YOUR_PROJECT_ID-sc-jail-data/private --recursive --checksums-only --exclude='.*\.tmp$'`
   and
   `gcloud storage rsync data/public gs://YOUR_PROJECT_ID-sc-jail-data/public --recursive --checksums-only --exclude='.*\.tmp$'`.
   Compare source/destination object inventories, sizes, and CRC32C checksums
   before activation. Exclude transient files; retain all research backups.
5. For initial setup, create and invoke the job:
   `.\.venv\Scripts\python.exe scripts\deploy_gcp.py --project YOUR_PROJECT_ID --scheduler-only`.
   For an existing paused job, resume it:
   `gcloud scheduler jobs resume sc-jail-quarter-hour --location us-central1 --project YOUR_PROJECT_ID`.
6. Confirm both sources update in the next slot. Keep the local files as a backup.

## Work with the active cloud archive

From the repository root, use the CLI PATH setup above and authenticate the
local Python client with Application Default Credentials. `gcloud auth login`
for deployment does not itself configure these credentials. The account needs
access to the private archive; the dashboard service account intentionally lacks
that access.

```powershell
gcloud auth application-default login
$env:SCJ_BUCKET = 'sc-jail-research-20260922-sc-jail-data'
.\.venv\Scripts\python.exe scripts\export_archive.py --output data\exports\history.csv
```

The same `SCJ_BUCKET` selection applies to case exports, reconstruction, repairs,
and analytics updates. Export commands read the cloud archive and write their
output locally. Maintenance commands can modify the selected archive; pause
scheduling and let active collection finish before using them. Resume after
verification:

```powershell
gcloud scheduler jobs pause sc-jail-quarter-hour --location us-central1 --project sc-jail-research-20260922
# Wait for active collection to finish, perform maintenance, and verify results.
gcloud scheduler jobs resume sc-jail-quarter-hour --location us-central1 --project sc-jail-research-20260922
```

For subsequent commands that should use the local archive, clear the selection:

```powershell
Remove-Item Env:SCJ_BUCKET -ErrorAction SilentlyContinue
```

The local `data/` directory remains the September 22 cutover backup. It must not
be used to overwrite newer cloud observations.

## Backup and restoration

The deployment configures Storage Transfer Service to copy the archive into
`gs://YOUR_PROJECT_ID-sc-jail-backup` daily at 05:10 UTC. Changed objects are copied;
objects missing from the source are retained in the backup. The transient
collector lease is excluded. The collector and dashboard have no backup access.
The backup has versioning and seven-day soft deletion. Its lifecycle removes only
noncurrent versions older than 30 days with at least two newer versions. Live
backup objects have no deletion lifecycle. This adds storage and request costs;
it is a same-project recovery copy, not protection from a compromised project owner.

Failed copy/find operations are logged and monitored. Check the transfer job's
last successful operation as well as the failure alert: a disabled job cannot
emit copy failures. Scheduled copies can overlap collection and do not form an
atomic snapshot. Immutable manifests are commit records; rebuild projections
after a restore. For a release checkpoint or restore drill, pause Scheduler,
wait for active collection to finish, run the transfer job, and compare both
inventories by object name, size, and CRC32C (excluding the lease).

After accidental deletion, first inspect the archive's soft-deleted generations
and the backup's live/noncurrent versions. Restore into a **separate private
bucket or local directory**, not over the active archive. Never restore the lease.
Use `scripts/migrate_history.py --verify-only` to check reconstruction, then
`scripts/rebuild_index.py` and `scripts/update_repeat_visits.py --rebuild` to
recreate projections. Compare counts and latest slots before switching the
collector/dashboard `SCJ_BUCKET` and resuming Scheduler. Keep the original
archive and recovery copy until validation is complete.

### Restore drill - 2026-09-26

A rehearsal restored the backup into a separate local folder
(`data/restore-drill/2026-09-26`) with the live archive and collector untouched:

1. The backup job was enabled and its latest daily copy (September 25, 05:10 UTC)
   succeeded. Inventories by name, size, and CRC32C showed all 8,839 history objects
   written before that copy identical in the backup; the only differences were newer
   objects and six projections updated later. The lease is excluded by design.
2. `gcloud storage rsync` restored 9,117 objects (265,001,340 bytes), matching the backup
   inventory exactly (inventory SHA-256 `e27dab979d64b5e1817e48a5e0da0d2d1fc686574f1963e21d7c048ce5e0989f`).
3. With `SCJ_BUCKET` unset and `SCJ_DATA_DIR` pointing at the restored folder:
   `migrate_history.py --verify-only` verified 2,066 observations (11 minutes);
   `rebuild_index.py` rebuilt 515 IML and 543 XFER points, identical to the backed-up
   public index except the operational `attempts` and `last_attempt` fields (11 minutes);
   `update_repeat_visits.py --rebuild` reproduced all 18 public repeat-visit fields and all
   3,760 private visit records (5 minutes). A booking panel built from the restored copy
   matched all 515 archived IML populations.

A full restore and rebuild took about 35 minutes on a desktop. The drill does not
exercise restoring soft-deleted archive generations or noncurrent backup versions.

## Monitoring and limits

- `/health` checks the web process. `/api/status` reports source freshness.
  `/api/freshness` returns 503 for failed/overdue population collection or a
  dashboard storage outage. Product checks are available at
  `/api/freshness/iml_details`, `/api/freshness/xfer_courts`, and
  `/api/freshness/repeat_visits`; incomplete supplemental coverage is unhealthy.
  Individual population checks are also available at `/api/freshness/iml` and
  `/api/freshness/xfer`. Repeat analytics is unhealthy if its `through` watermark
  is missing, more than one hour old, or the last refresh reported an error.
  Four five-minute uptime checks alert after sustained failures for 15 minutes.
  A separate log alert watches backup failures. Deployment attaches enabled
  Monitoring notification channels; without one, incidents are console-only.
  The local-compatible `/healthz` alias is retained, but Google's frontend
  returned 404 for that path during deployment; use `/health` for cloud checks.
- After 30 minutes without a successful observation, the dashboard marks that
  source overdue. A scraper exception is displayed immediately.
- XFER's file timestamp is independent of the polling timestamp. A successful
  poll does not imply that the county regenerated its report.
- Local mode retries population failures once after 60 seconds when the first
  attempt finishes within the slot's first ten minutes. Cloud Scheduler makes at
  most two retries; successful sources are not fetched again. Supplemental or
  repeat-analysis failures alone do not fail the collector request or trigger
  these retries; their freshness checks expose the problem.
- The collector has bounded source timeouts, a 540-second population budget,
  a 600-second request limit, and a 660-second lease with a final commit margin.
- A changing roster can fail completeness validation. That missing interval is
  preferable to a false population change; the next attempt starts a fresh session.
  The 07:00 UTC (2 a.m. Central) IML slot failed this way on September 20, 21,
  and 23 as the roster total fell during every attempt, apparently while released
  records were purged; the 07:15 slot succeeded each time. It is not nightly: after the
  cutover it failed only on September 23. From the 0.2.0 release through September 26
  01:15 UTC, five roster slots were missed at scattered times, and the population alert
  (more than one checker failing for 15 minutes) fired once, for the September 23 07:00
  slot. About 11 times a day an IML scan fails when pagination shifts and Scheduler
  retries it, so `/api/freshness` returns 503 for about five minutes until the retry
  succeeds; these blips are too short to alert. The record-page alert fired twice on
  September 23 during the refresh backlog. No alert change was needed as of September 26.
- Cloud outages and source outages cannot be backfilled from a live current
  roster. Original observation times are always preserved.
- A warm dashboard retains the last validated aggregate index during a storage
  outage, marks responses stale, and backs off retries. A cold instance without
  cached data returns 503. Chart output is bounded and cached by index revision,
  range, width bucket, and time bucket. Long-range change bars aggregate valid
  observations; gaps are not filled with zeroes.
- Each collection logs a structured `collection_summary` with source status,
  elapsed time, supplemental counts, and repeat-analysis watermark. Observations
  record application/parser versions and a source-content build identifier.


## Case-data expansion

The same collector request performs bounded court-report and IML-detail work
after attempting both population sources and committing each successful result.
A population-source failure does not by itself block supplemental work; IML
details require a complete roster no more than two hours old, and all work must
fit the remaining execution budget. Case collection uses the existing private
bucket, lease, service, and Scheduler job; no database or new always-on resource
is required. The extra work increases compute, object operations, and storage
beyond the original population-only estimates above. Monitor actual usage before
assuming the expanded workload stays within shared free allowances.

See [CASE_DATA.md](CASE_DATA.md#configuration) for refresh budgets and environment
variables. The overall execution deadline still takes priority, and individual-page coverage builds
across scheduled runs. The cloud deployment uses this same collection path.
