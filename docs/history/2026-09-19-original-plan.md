---
type: Plan
title: Original plan
description: Plan written before implementation on September 19, 2026, covering outcome, source investigation, cloud choice and cost, implementation, verification, and progress.
tags: [history, cloud, cost]
date: 2026-09-19
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T01:54:59Z }
sources:
  - id: plan-l1
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/PLAN.md?plain=1#L1-L114
    title: PLAN.md lines 1-114, before the OKF migration
    last_modified: 2026-09-23T03:04:09Z
  - id: run-pricing
    resource: https://cloud.google.com/run/pricing
    title: Cloud Run pricing
  - id: scheduler-pricing
    resource: https://cloud.google.com/scheduler/pricing
    title: Cloud Scheduler pricing
  - id: storage-pricing
    resource: https://cloud.google.com/storage/pricing
    title: Cloud Storage pricing
  - id: free-tier
    resource: https://docs.cloud.google.com/free/docs/free-cloud-features
    title: Google Cloud free tier features
  - id: github-schedule
    resource: https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule
    title: GitHub Actions schedule event
  - id: oracle-free
    resource: https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm
    title: Oracle Cloud Always Free resources
  - id: vpc-pricing
    resource: https://cloud.google.com/vpc/network-pricing
    title: VPC network pricing
  - id: cloudflare-limits
    resource: https://developers.cloudflare.com/workers/platform/limits/
    title: Cloudflare Workers limits
---

Written before implementation: 2026-09-19.

**Current status (2026-09-23 UTC):** Release 0.2.0 is deployed to Google Cloud. The
collector and dashboard run in `sc-jail-research-20260922`; local collection and
its restart task are stopped. See [current operations](../operations/cloud-deployment.md) and
[release verification](../deployments/2026-09-23-release-0-2-0.md). The dated results, now separate
[milestone records](index.md), preserve the
original sequence; statements about pending cloud setup describe September 19,
not current status.

# Outcome

Collect the two sources used by `jpbranson/shelby.county` and
`jpbranson/memphis.xfer` every 15 minutes with Python. Preserve observations and
source files, expose collection health, and show a small aggregate dashboard.
Run locally immediately if cloud account setup requires the owner.

# Source investigation

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

# Cloud choice and cost

Target **Google Cloud Run**, **Cloud Scheduler**, and private **Cloud Storage**
in `us-central1`. Use a private HTTP collector triggered on UTC quarter hours,
plus a separate read-only Python dashboard. Both scale to zero. A small
fractional-CPU collector avoids Cloud Run Jobs' one-minute, one-CPU minimum.[^run-pricing]
Use authenticated scheduling, bounded request duration, one maximum collector
instance, retries, and idempotent observation keys. No always-on VM, managed
database, paid load balancer, or NAT gateway is necessary.

At 96 collections/day, one Scheduler job fits its three-job free allowance.[^scheduler-pricing]
Cloud Run request-based billing and regional Storage free allowances should
cover light use;[^run-pricing][^storage-pricing] object operations and retained data may cost cents. Measure
run duration and compressed data sizes before making a firmer estimate.
Free allowances are shared across a billing account and are not a spending
cap.[^free-tier] Document storage growth, image storage, network use, and budget alerts.

Alternatives considered: GitHub Actions schedules can be delayed or dropped;[^github-schedule]
Oracle free VMs can be reclaimed as idle;[^oracle-free] Google's free VM still incurs an
external IPv4 charge.[^vpc-pricing] Cloudflare's free Worker CPU allowance is too small for
the likely multi-page Python parsing workload.[^cloudflare-limits]

Pricing and limitations checked 2026-09-19.

# Implementation

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

# Verification and handoff

- Test pagination/completeness, date interpretation, duplicate observations,
  failure isolation, changed report detection, atomic persistence, and the
  dashboard's honest empty/stale states with synthetic fixtures.
- Run a real collection and inspect its counts, completeness, timing, and
  stored artifacts; do not present synthetic fixtures as collected data.
- Verify dashboard routes, readable chart output, and deployment configuration.
- Leave local processes running if cloud deployment is blocked. Record exact
  startup/stop commands, the local/remote URLs, and the required cloud setup.
- Keep [`DECISIONS.md`](../decisions/index.md) as a brief plain-English record, adding only decisions
  that affect data quality, cost, operation, or user-visible behavior.

# Progress

- [x] Review original scraper source and current provider documentation.
- [x] Write initial design before implementation.
- [x] Verify live source behavior.
- [x] Implement and test collection/storage.
- [x] Implement and verify dashboard.
- [x] Add cloud deployment and operating instructions.
- [x] Run collection and dashboard locally or in the cloud; record results.
- [x] Deploy to Google Cloud, verify the archive migration, and stop the local
  fallback (2026-09-22).

[^run-pricing]: Cloud Run pricing
[^scheduler-pricing]: Cloud Scheduler pricing
[^storage-pricing]: Cloud Storage pricing
[^free-tier]: Google Cloud free tier features
[^github-schedule]: GitHub Actions schedule event
[^oracle-free]: Oracle Cloud Always Free resources
[^vpc-pricing]: VPC network pricing
[^cloudflare-limits]: Cloudflare Workers limits
