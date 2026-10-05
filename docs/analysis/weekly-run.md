---
type: Pipeline
title: Weekly analysis run
description: Local weekly job that refreshes the archive mirror and rebuilds every analysis product into a dated folder, run by the SC-Jail-Weekly-Analysis task.
resource: ../../scripts/weekly_analysis.py
tags: [analysis, local, operations]
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:10:00Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:10:00Z }
sources:
  - id: analysis-l139
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/docs/ANALYSIS.md?plain=1#L139-L175
    title: docs/ANALYSIS.md lines 139-175, before the OKF migration
    last_modified: 2026-09-26T02:01:31Z
    author: claude-code/claude-opus-5-5
---

`scripts/weekly_analysis.py` refreshes a local mirror of the cloud archive and rebuilds
every product into `data/analysis/weekly/<Central date>/`, with `index.html` (status and
links), `run.json` (per-step status, timing, and readout readiness), and `logs/`.

```powershell
$env:PATH = "$PWD\.runtime\google-cloud-sdk\bin;$env:PATH"
.\.venv\Scripts\python.exe scripts\weekly_analysis.py
```

- The mirror is `data/snapshots/current`. `gcloud storage rsync` downloads only new or
  changed objects (seconds after the first copy), using the normal `gcloud auth login`
  sign-in. The run fails if the newest roster slot is more than three hours old.
- Steps run in separate processes: mirror, [booking panel](booking-panel.md),
  [profile](population-profile.md), [trends](trends.md), [reconciliation](source-reconciliation.md),
  [length of stay](length-of-stay.md), [money bond](money-bond.md), [court linkage](court-linkage.md),
  [re-booking](rebooking.md), and a monthly cost projection
  ([`scripts/usage_report.py`](../../scripts/usage_report.py); `--skip-usage` leaves it out and
  `--cost-target` sets the target, default $5). If the panel
  fails its population check, the steps that use it are skipped and the run is marked
  incomplete; the others still run.
- Work goes to a `.partial-*` folder and is renamed at the end. A second run on the same
  date keeps the earlier folder as `<date>.previous-<time>`; nothing is deleted.
  A file lock prevents overlapping runs.
- `--skip-sync` rebuilds from the mirror as it is, and `--output-root` writes elsewhere.

The `SC-Jail-Weekly-Analysis` Windows task
([decision](../decisions/2026-09-26-weekly-local-analysis.md)) runs this on Wednesdays at 09:00 through
`scripts/run-weekly-analysis.ps1`, which adds the bundled gcloud CLI to `PATH` and
appends one line per run to `.runtime/weekly-analysis.log` (full output in
`weekly-analysis.out.log` and `.err.log`). The task runs only while the owner is signed
in, stores no password, and starts at the next opportunity if a run was missed. Install
or update it with `scripts\install-weekly-task.ps1`; remove it with
`Unregister-ScheduledTask SC-Jail-Weekly-Analysis`. If a run fails with an rsync error,
run `gcloud auth login` again.

Readouts: each analysis records whether it has enough collection time for its first
readout (`readout_ready` in its `summary.json`). Before then its report is marked
preliminary. Collection began on September 19, 2026, so readouts become available on or
after October 17 (bond, court timing), October 19 (length of stay), and December 18
(re-booking). Reconciliation and court match rates are usable now.

Latest weekly run (September 30, 2026): all ten steps were ok in about 14 minutes (the panel
took 647 seconds), with no readout ready yet; the task's next run is October 7.
