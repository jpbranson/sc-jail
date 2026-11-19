---
type: Decision
title: Serve the held index while a dashboard reload waits
description: While one dashboard request reloads the public index, other requests use the index already held, and the dashboard accepts four requests at once, so a slow storage read no longer blocks pages and charts.
tags: [dashboard, monitoring, operations]
decided: 2026-11-19
generated: { by: claude-code/claude-fable-5-2, at: 2026-11-19T01:45:00Z }
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
- The dashboard's Cloud Run concurrency is 4, matching its four server threads. The
  collector stays at 1.[^deploy]
- A Cloud Storage read that takes more than five seconds logs "Slow read of …" with the time
  spent on the metadata request and on the download, for the dashboard and the
  collector.[^storage]

The owner chose this over restarting only, which leaves a repeat to cause the same outage.
It adds no cost: Cloud Run bills instance time, not concurrency.

Known limits:

- The request that performs the reload still waits, so billable time still rises and an
  uptime check that lands on it can still time out.
- The cause of the slow reads is not known. A shorter timeout on dashboard reads, falling
  into the existing stale-and-backoff path, is deferred until the new log shows which call
  waits.
- Four chart requests can now arrive together on 0.25 vCPU. Rendering is still one chart at
  a time, so a chart can wait behind three others.

Related: [monitoring and limits](../operations/monitoring-and-limits.md),
[cloud architecture](../architecture/system.md).

[^monitoring]: Monitoring and limits, the November 18, 2026 dashboard slowdown
[^dashboard]: Dashboard application, state()
[^storage]: Cloud Storage reads, GCSStore.read
[^deploy]: Deployment script, Cloud Run settings per service
