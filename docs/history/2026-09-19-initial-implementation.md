---
type: Milestone
title: Initial implementation result
description: First build on September 19, 2026, with both adapters, private archives, scheduler, dashboard, and tests running locally while cloud setup awaited the owner.
tags: [history, local]
date: 2026-09-19
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T01:54:59Z }
sources:
  - id: plan-l116
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/PLAN.md?plain=1#L116-L132
    title: PLAN.md lines 116-132, before the OKF migration
    last_modified: 2026-09-22T16:39:10Z
---

Implemented both source adapters, immutable private archives, atomic local/cloud
storage, a quarter-hour scheduler, the dashboard, tests, a container, and a
repeatable Google Cloud deployment script. The XFER adapter focuses on the
verified jail workbook rather than unrelated county folders.

Both sources have completed multiple live collections. A 09:00 UTC scheduled
run completed with 110 roster pages and 3,003 current people; the report had
3,151 distinct bookings. The dashboard is running at http://127.0.0.1:8050 and
through the [Quick Tunnel](../decisions/2026-09-19-quick-tunnel.md) recorded in README.md. Windows checks for stopped
local processes every minute while the user is signed in.

Cloud setup is ready for the owner to run, but no cloud resources were created:
Google Cloud login, project selection, and billing setup are still needed.
The deployment dry run and Linux dependency resolution pass; actual cloud
execution remains unverified. See [expected cost](../cost/expected-cost.md) and [owner setup](../operations/deploy.md) for cost
estimates and setup.
