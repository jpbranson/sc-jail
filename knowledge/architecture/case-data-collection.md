---
type: Pipeline
title: Case-data collection
description: After the population sources commit, the same collector request spends bounded time on court reports and then IML record pages, with no extra service.
tags: [iml-details, xfer-courts, cloud]
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T01:54:59Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:06:36Z }
sources:
  - id: case-data-l1
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/docs/CASE_DATA.md?plain=1#L1-L8
    title: docs/CASE_DATA.md lines 1-8, before the OKF migration
    last_modified: 2026-09-23T03:04:09Z
  - id: cloud-l527
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/docs/CLOUD.md?plain=1#L527-L541
    title: docs/CLOUD.md lines 527-541, before the OKF migration
    last_modified: 2026-09-23T03:04:09Z
---

# Order and budget

Population collection runs every 15 minutes. After attempting both population
sources and committing each successful result, the same process spends bounded
time on [court reports](../sources/xfer-court-reports.md) and then
[IML individual pages](../sources/iml-record-pages.md). A population failure does
not by itself block this work: details can use the last complete roster for up
to two hours, subject to the remaining budget. Case collection adds no separate
cloud service, database, or Scheduler job.

# In the cloud deployment

The same collector request performs bounded court-report and IML-detail work
after attempting both population sources and committing each successful result.
A population-source failure does not by itself block supplemental work; IML
details require a complete roster no more than two hours old, and all work must
fit the remaining execution budget. Case collection uses the existing private
bucket, lease, service, and Scheduler job; no database or new always-on resource
is required. The extra work increases compute, object operations, and storage
beyond the original population-only estimates in [expected cost](../cost/expected-cost.md).
Monitor actual usage before assuming the expanded workload stays within shared free
allowances.

See [configuration](configuration.md) for refresh budgets and environment
variables. The overall execution deadline still takes priority, and individual-page coverage builds
across scheduled runs. The cloud deployment uses this same collection path.

Storage of the collected versions is described in [case-data storage](case-data-storage.md).
