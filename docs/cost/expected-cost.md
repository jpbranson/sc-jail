---
type: Cost Estimate
title: Expected cost (original estimate)
description: The original population-only monthly cost estimate under free allowances, with pricing rechecked on 2026-09-23; not a forecast for the full workload.
tags: [cost, cloud]
date: 2026-09-23
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T01:54:59Z }
sources:
  - id: cloud-l166
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/docs/CLOUD.md?plain=1#L166-L228
    title: docs/CLOUD.md lines 166-228, before the OKF migration
    last_modified: 2026-09-26T02:01:31Z
  - id: run-pricing
    resource: https://cloud.google.com/run/pricing
    title: Cloud Run pricing
  - id: run-cpu
    resource: https://docs.cloud.google.com/run/docs/configuring/services/cpu
    title: Cloud Run fractional CPU requirements
  - id: scheduler-pricing
    resource: https://cloud.google.com/scheduler/pricing
    title: Scheduler pricing
  - id: storage-pricing
    resource: https://cloud.google.com/storage/pricing
    title: Storage pricing
  - id: free-tier
    resource: https://docs.cloud.google.com/free/docs/free-cloud-features
    title: Free tier allowances
  - id: artifact-registry-pricing
    resource: https://cloud.google.com/artifact-registry/pricing
    title: Artifact Registry pricing
  - id: cloud-build-accounts
    resource: https://docs.cloud.google.com/build/docs/securing-builds/configure-user-specified-service-accounts
    title: Custom Cloud Build accounts
---

The table records the original population-only workload estimate in USD, with
light dashboard traffic and otherwise-unused account free allowances. Its pricing
assumptions were rechecked against the official sources cited in the footnotes on
September 23, 2026. Detail pages, court reports, repeat analytics, backups, and
monitoring add compute, requests, and storage; this baseline is not a forecast for the
full deployed workload or a zero-cost guarantee. The configured $5 alert is a budget
threshold, not a monthly cost estimate; see [measured usage](measured-usage-2026-09-26.md).

| Component | Workload / allowance | Expected initial cost |
| --- | --- | --- |
| Cloud Run collector | 2,976 runs in a 31-day month; at 150 seconds/run and 0.25 CPU: 111,600 vCPU-seconds and 223,200 GiB-seconds | Within request-based free allowances[^run-pricing][^free-tier] |
| Dashboard | Short cached requests, no persistent sessions; scales to zero | Usually within the remaining free allowances |
| Scheduler | One job; three free jobs per billing account | $0[^scheduler-pricing] |
| Storage operations | Roughly 11 writes/run, plus daily normalized checkpoints; fewer than 35,000/month | About $0.15/month after 5,000 free Class A operations, plus any excess reads[^storage-pricing] |
| Stored data | 5 GB-months free in an eligible region; identical source blobs deduplicated | Initially likely $0; grows with retained history[^free-tier] |
| Builds / images | One small image; build inputs/logs deleted after 7 days, untagged images cleaned after 7 days with two recent versions retained | Usually small; image storage above the free allowance is billable[^artifact-registry-pricing] |

The first regular cloud execution on September 22 completed in about two
minutes. One successful run does not establish a monthly average; measure
subsequent durations, retries, and archive growth. At 0.25 CPU, approximately
four minutes per collection would consume the request-based monthly CPU free
allowance before dashboard use or retries.[^run-cpu][^run-pricing]

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
is approximately $0.02/GB-month.[^storage-pricing] File downloads into Cloud Run are
ingress; dashboard traffic and requests to the county consume outbound allowance.

Free allowances are shared across the billing account.[^free-tier] Retries, dashboard
traffic, unrelated workloads, long-term retention, and image size can increase
costs. The deployed project has a
[$5 monthly budget alert](../decisions/2026-09-26-budget-alert-5.md) (September 26, 2026).
Check billing after the first day/week and review run duration and bucket growth.
**Budget alerts do not cap spending.** Pause Scheduler to prevent future scheduled
collection; let any in-flight request finish. Stored data can still incur charges. There
is no uptime guarantee at a strict $0 budget.

[^run-pricing]: Cloud Run pricing
[^run-cpu]: Cloud Run fractional CPU requirements
[^scheduler-pricing]: Scheduler pricing
[^storage-pricing]: Storage pricing
[^free-tier]: Free tier allowances
[^artifact-registry-pricing]: Artifact Registry pricing
