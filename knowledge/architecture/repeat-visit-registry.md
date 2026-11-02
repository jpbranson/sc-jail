---
type: Pipeline
title: Repeat-visit registry
description: The collector incrementally replays committed IML and detail observations into a private registry and publishes aggregate repeat-visit results.
resource: ../../src/sc_jail/repeats.py
tags: [repeat-visits, storage, privacy]
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T01:54:59Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:06:36Z }
sources:
  - id: repeat-visits-l33
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/docs/REPEAT_VISITS.md?plain=1#L33-L81
    title: docs/REPEAT_VISITS.md lines 33-81, before the OKF migration
    last_modified: 2026-09-23T03:04:09Z
---

Computes the [repeat visits and time between visits](../measures/repeat-visits.md) measure.

# Updating

After population and detail collection, the collector incrementally consumes new
committed IML and IML-detail observations. The initial run backfills all archived
observations, including those older than the 90-day population-chart window.
Changes and checkpoints are reconstructed with the archive's checksum validation;
unchanged states are verified against the previous processed checksum.

The compact registry at `private/analytics/repeat-visits.json.gz` retains only
booking identifiers, permanent IDs, first-seen timestamps, and the dates needed
for the calculation. Person-level data stays private. The public index and
`/api/repeat-visits` expose aggregate counts, date coverage, and histogram bins.
A failed calculation preserves the last completed public result and displays
a delayed-refresh notice.

Long calculations save a private staging registry at
`private/analytics/repeat-visits-progress.json.gz` every 20 observations and
before their time budget expires. Each calculation captures fixed source targets;
later arrivals wait for the next calculation. Subsequent runs resume that work,
while the published registry and public summary remain at their last complete
watermark. A calculation-version change requires `--rebuild`. Administrative rebuilds
renew their storage lease while progressing; a lost lease prevents publication.

`/api/freshness/repeat_visits` returns HTTP 503 when the public result has no
`through` watermark, is more than one hour behind, has a refresh error, or the
dashboard cannot refresh its storage cache. The collector's population result
can still be successful while this calculation is delayed.

# Commands

Commands below use `SCJ_BUCKET` when set, otherwise the local `SCJ_DATA_DIR`
(default `data/`). The local archive stopped updating at cloud cutover; use the
[cloud archive setup](../operations/active-cloud-archive.md) to update the
active dashboard. Normal scheduled collection already refreshes these summaries.

Recalculate from the selected archive without contacting county sources:

```powershell
.\.venv\Scripts\python.exe scripts\update_repeat_visits.py
```

After repairing historical source data, rebuild the registry:

```powershell
.\.venv\Scripts\python.exe scripts\update_repeat_visits.py --rebuild
```

Both commands acquire the collector lease. For cloud maintenance, pause the
Scheduler job and let active collection finish before running them, then resume
the job after verification. An active collection leaves the archive and existing
summaries unchanged. Original observations are never modified by this calculation.
