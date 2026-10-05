---
type: Metric
title: Arrivals and departures
description: Arrivals and departures are IDs appearing or disappearing between adjacent successful slots no more than 20 minutes apart; gaps stay blank.
tags: [population, dashboard, data-quality]
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T01:54:59Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:06:36Z }
sources:
  - id: readme-l192
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/README.md?plain=1#L192-L195
    title: README.md lines 192-195, before the OKF migration
    last_modified: 2026-09-22T16:39:10Z
---

# Definition

Arrivals/departures mean IDs appearing/disappearing between adjacent successful
slots no more than 20 minutes apart. The first observation and comparisons over
gaps have blank changes. They are not independently confirmed jail events.
Release dates have no time-of-day precision.

Collection gaps are recorded in the [normalized history](../architecture/normalized-history.md);
before the cloud cutover, [local collection missed roughly one slot in five](../source-quality/iml-local-missed-slots.md).
