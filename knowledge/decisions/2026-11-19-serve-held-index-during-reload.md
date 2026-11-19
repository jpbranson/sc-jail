---
type: Decision
title: Serve the held index while a dashboard reload waits
description: While one dashboard request reloads the public index, other requests use the index already held, and the dashboard runs on 1 vCPU and accepts four requests at once, so a slow storage read no longer blocks pages and charts.
tags: [dashboard, monitoring, operations, cost]
decided: 2026-11-19
generated: { by: claude-code/claude-fable-5-2, at: 2026-11-19T02:37:00Z }
sources:
  - id: dashboard
    resource: ../../src/sc_jail/web.py
    title: Dashboard application, state()
  - id: storage
    resource: ../../src/sc_jail/storage.py
    title: Cloud Storage reads, GCSStore.read
  - id: deploy
    resource: ../../scripts/deploy_gcp.py
    title: Deployment script, Cloud Run settings per service
  - id: monitoring
    resource: ../operations/monitoring-and-limits.md
    title: Monitoring and limits, the November 18, 2026 dashboard slowdown
---

On November 18 one dashboard instance's reads of `public/index.json` began taking 21 to 50
seconds without failing. The reload ran inside a request, under a lock, and the dashboard
served one request at a time, so pages and charts queued behind it and failed for about ten
hours while collection stayed healthy.[^monitoring]

Three changes limit the effect of a slow read:

- A request that arrives while another is reloading the index uses the validated index
  already held instead of waiting. A cold instance with no index still waits for the first
  read.[^dashboard]
- The dashboard's Cloud Run concurrency is 4, matching its four server threads, and its CPU
  is 1 vCPU, because Cloud Run rejects concurrency above 1 below 1 vCPU. The collector stays
  at 0.25 vCPU and concurrency 1.[^deploy]
- A Cloud Storage read that takes more than five seconds logs "Slow read of …" with the time
  spent on the metadata request and on the download, for the dashboard and the
  collector.[^storage]

The owner chose this over restarting only, which leaves a repeat to cause the same outage.
The first deployment asked for concurrency 4 on 0.25 vCPU and Cloud Run rejected it (see the
[November 19 deployment](../deployments/2026-11-19.md)). The owner then chose 1 vCPU over
three alternatives: a short timeout on dashboard reads at 0.25 vCPU, which costs nothing but
leaves the page stale until the instance is replaced; a second dashboard instance; and
keeping only the slow-read log.

Cost, estimated at us-central1 list prices and not yet measured: the dashboard was billed
about 1,400 instance-seconds a day from November 15 to 18 (Cloud Monitoring), which is about
10,600 vCPU-seconds a month at 0.25 vCPU and about 42,600 at 1 vCPU. The difference is
about $0.80 a month. It applies in both
[allowance cases](../questions/cost-allowance-case.md), because the collector alone, at
24,600 to 34,200 billable seconds a day from November 12 to 18, now uses more than the
180,000 vCPU-second free allowance. A repeat of the
November 18 slowdown would cost about $0.90 a day at 1 vCPU until the instance is replaced,
against about $0.26 at 0.25 vCPU. The no-allowance projection was already above the
[$5 target](2026-09-26-under-5-dollars.md) before this change.

Known limits:

- The request that performs the reload still waits, so billable time still rises and an
  uptime check that lands on it can still time out.
- The cause of the slow reads is not known. A shorter timeout on dashboard reads, falling
  into the existing stale-and-backoff path, is deferred until the new log shows which call
  waits.
- Rendering is still one chart at a time, so a chart can wait behind others. Six chart
  requests sent together on a new instance finished within 3.0 seconds on November 19.

Related: [monitoring and limits](../operations/monitoring-and-limits.md),
[cloud architecture](../architecture/system.md).

[^monitoring]: Monitoring and limits, the November 18, 2026 dashboard slowdown
[^dashboard]: Dashboard application, state()
[^storage]: Cloud Storage reads, GCSStore.read
[^deploy]: Deployment script, Cloud Run settings per service
