---
type: Playbook
title: Owner setup and deployment
description: How to deploy or update sc-jail with scripts/deploy_gcp.py, including dry runs, deferred Scheduler activation, image rollback, and post-deploy checks.
resource: ../../scripts/deploy_gcp.py
tags: [cloud, deployment, operations]
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:12:00Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:10:00Z }
sources:
  - id: cloud-l271
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/docs/CLOUD.md?plain=1#L271-L353
    title: docs/CLOUD.md lines 271-353, before the OKF migration
    last_modified: 2026-09-23T03:04:09Z
---

For a new environment, Google Cloud sign-in and an existing billing account are
required. The code does not create a billing account. This workspace has a
portable CLI at `.runtime/google-cloud-sdk/bin/gcloud.cmd`. From the repository
root, add it to the current PowerShell process's PATH:

```powershell
$env:PATH = (Join-Path (Get-Location) '.runtime\google-cloud-sdk\bin') + [IO.Path]::PathSeparator + $env:PATH
```

As of October 5, 2026, this machine also has a newer Google Cloud CLI (installed with winget
on October 4) at `%LOCALAPPDATA%\Google\Cloud SDK\google-cloud-sdk\bin`, which may not be on
PATH; prepend either `bin` directory the same way before running `scripts/deploy_gcp.py`.

The examples use the project's installed virtual environment. On a new machine,
first follow [local dependency setup](local-setup.md), stopping before
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
   Follow the [migration steps](migrate-local-history.md), then activate collection with
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
The images currently available for rollback are listed in
[retained images and rollback](../deployments/retained-images.md).

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
