# Google Cloud deployment

## Current deployment

Deployed September 22, 2026:

- Project: `sc-jail-research-20260922` (number `564083380783`).
- Region: `us-central1`.
- Dashboard: https://sc-jail-dashboard-xcucxqzc2q-uc.a.run.app
- Private collector: https://sc-jail-collector-xcucxqzc2q-uc.a.run.app
- Archive: `gs://sc-jail-research-20260922-sc-jail-data`.
- Scheduler: `sc-jail-quarter-hour`, `*/15 * * * *` in UTC.
- Monthly budget: $15, with actual-spend alerts at 50%, 90%, and 100%, and a
  forecast alert at 100%. The budget does not cap spending.

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
observations for that interval. All 111 regression tests and lint checks passed.
The local dashboard port was confirmed closed after cutover.

## Chosen architecture

One private Cloud Run collector, one public read-only Cloud Run dashboard,
one Cloud Scheduler job, and a private regional Cloud Storage archive, all in
`us-central1`. Both services have zero minimum instances, a configured maximum
of one instance per revision, 0.25 vCPU, 512 MiB RAM, request-based billing, and
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

The table records the original population-only estimate using official pricing
checked September 19, 2026, USD, light dashboard traffic, and otherwise-unused
account free allowances. Detail pages and court reports add compute, requests,
and storage; this baseline is not a forecast for the full deployed workload or
a zero-cost guarantee. The configured $15 alert is a budget threshold, not a
monthly cost estimate.

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

The XLS measured 5.33 MB uncompressed / 1.13 MB compressed. If every poll produced
a different XLS, originals alone would add about 3.36 GB per 31-day month;
normalized data and roster pages add more. In the initial observations, the
XLS did not change, so content-addressed storage reused the same blob.
No indefinite free storage claim is made. Additional regional Standard storage
is approximately $0.02/GB-month. File downloads into Cloud Run are ingress;
dashboard traffic and requests to the county consume outbound allowance.

Free allowances are shared across the billing account. Retries, dashboard
traffic, unrelated workloads, long-term retention, and image size can increase
costs. The deployed project has a $15 monthly budget alert. Check billing after
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

`--defer-scheduler` leaves any existing Scheduler job unchanged, so it is intended
for initial setup. Pause an existing job explicitly before a later migration.
`--scheduler-only` configures and invokes the job without rebuilding services.
New service-account propagation failures during bucket permission binding are
retried with bounded backoff. The builder also gets bucket-metadata read access
on the dedicated build bucket, which Cloud Build requires for validation.

The script creates or updates dedicated `sc-jail-*` resources. Run it only in
the intended project. It builds on Cloud Build, so Docker need not run locally.
It disables soft-delete version accumulation on the dedicated buckets, applies
a seven-day lifecycle only to the separate build bucket, and never installs a
retention/deletion rule on the research archive.

Cloud Run's generated HTTPS URL is printed at the end. The initial Scheduler
invocation is asynchronous; verify the first regular quarter-hour execution in
Scheduler logs and `/api/status`. An HTTP 200 alone can mean a completed slot
was skipped or an expired scheduled attempt was ignored. Confirm both sources'
observation slots and successful retrieval times advance. Verify unauthenticated
collector calls are rejected and the dashboard identity has no access to
`private/`. Review Cloud Run/Scheduler logs for failures.

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

The local `data/` directory remains the September 22 cutover backup. To back up
newer cloud observations, copy the cloud archive to a separate private location
during a maintenance window and verify its object inventory and checksums.

## Monitoring and limits

- `/health` checks the web process. `/api/status` checks source freshness.
  The local-compatible `/healthz` alias is retained, but Google's frontend
  returned 404 for that path during deployment; use `/health` for cloud checks.
- After 30 minutes without a successful observation, the dashboard marks that
  source overdue. A scraper exception is displayed immediately.
- XFER's file timestamp is independent of the polling timestamp. A successful
  poll does not imply that the county regenerated its report.
- Local mode retries a failed source once within the slot. Cloud Scheduler
  makes at most two retries; successful sources are not fetched again.
- The collector has bounded source timeouts, a 600-second safe execution
  deadline, and a 660-second lease with a final commit margin.
- A changing roster can fail completeness validation. That missing interval is
  preferable to a false population change; the next attempt starts a fresh session.
- Cloud outages and source outages cannot be backfilled from a live current
  roster. Original observation times are always preserved.
- Soft-delete is disabled to avoid charging for repeated overwritten indexes.
  Keep an independent backup if protection from operator deletion is required.


## Case-data expansion

The same collector request now performs bounded court-report and IML-detail work
after committing both population observations. It uses the existing private
bucket, lease, service, and Scheduler job; no database or new always-on resource
is required. The extra work increases compute, object operations, and storage
beyond the original population-only estimates above. Monitor actual usage before
assuming the expanded workload stays within shared free allowances.

See [CASE_DATA.md](CASE_DATA.md#configuration) for refresh budgets and environment
variables. The overall execution deadline still takes priority, and individual-page coverage builds
across scheduled runs. The cloud deployment uses this same collection path.
