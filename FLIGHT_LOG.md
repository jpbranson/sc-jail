# Flight log: next-steps execution

Started 2026-09-26 00:10 UTC (2026-09-25 evening Central). Source of the step list:
the "Next steps" answer given at session start, derived from [PLAN.md](PLAN.md),
[docs/CLOUD.md](docs/CLOUD.md), and [docs/RELEASE_0_2_0.md](docs/RELEASE_0_2_0.md).

**To resume:** read the status board, then the last log entries. Each step records
what was actually verified. "Done" means completed and verified, never "code written".

Status values: `not started`, `in progress`, `done`, `partial` (what remains is
stated), `waiting on data` (earliest date stated), `blocked` (see human review).

## Status board

| # | Step | Status |
|---|---|---|
| 0 | Preflight: gcloud auth, fresh local archive snapshot | done |
| 1a | Weekly job: rsync → validated panel → profile → dated output | done |
| 1b | Week-over-week composition comparison | done |
| 1c | IML-vs-XFER reconciliation | done |
| 1d | Source-quality log | done |
| 1e | Weekly Windows scheduled task (runs late if missed) | done |
| 2 | Length of stay for new bookings (Kaplan-Meier) | waiting on data: code, tests, and a preliminary run done; first readout needs 30 days of collection (on or after 2026-10-19) |
| 3 | Money bond and pretrial detention | waiting on data: code, tests, and a preliminary run done; first readout needs ~4 weeks (on or after 2026-10-17) |
| 4 | Court linkage: match rates, postponements, commitment-to-indictment | partial: match rates done (ready now); court-date and indictment timing waiting on data (4–8 weeks, 2026-10-17 to 11-14) |
| 5 | Repeat-booking measures (~90 days of coverage) | waiting on data: code, tests, and a preliminary run done; readout needs 90 days (on or after 2026-12-18) |
| 6 | Billing and usage review (first-week review due ~Sept 29) | partial: usage measured and priced against the $5 target (weekly re-check added); budget alert lowered to $5 (approved); actual charges and a cost lever if allowances are shared still need the owner (review items 2 and 4) |
| 7 | Restore drill into a separate archive | done |
| 8 | Nightly 07:00 UTC IML alert noise check | done (no change needed) |
| 9 | Remove one-time `SC-Jail-Stop-Collection` Windows task | done |

## Human review queue

1. **What does "Sentenced" mean on a General Sessions case entry?** (found 2026-09-25, step 4)
   Of 1,345 held people counted as "sentenced on some cases, others open", 438 have
   *only* General Sessions (8-digit) entries marked "Sentenced" plus an open Criminal Court
   case. Of 35 bookings matched to a daily indictment list, 32 have the indicted case open,
   but only 1 passes the plan's "no case marked sentenced" test. If IML marks a General
   Sessions case "Sentenced" when it is bound over to the grand jury, the profile's pretrial
   count (1,416 on Sept 25) understates pretrial detention by up to about 440 people.
   Needs a check against court records (a few case numbers on the public Criminal Court
   and General Sessions sites) before changing any published definition. Nothing was
   changed; court linkage already uses the indicted case's own status. Evidence in
   `docs/SOURCE_QUALITY.md`.
2. **Which case applies to the $5 target: $0.52 or $5.38 a month?** (step 6) The projection
   is $0.52/month if this project receives the billing account's free allowances and
   $5.38 if other projects use them first (Cloud Run CPU alone $3.81). The billing account
   has five billing-enabled projects (this one and four others, not named here); I did not
   inspect the others. Check Billing →
   Reports for this project, grouped by SKU with credits shown, or say whether the other
   projects run Cloud Run. No billing export is configured, so this cannot be read by CLI.
3. ~~Approve lowering the budget alert from $15 to $5?~~ **Resolved 2026-09-26:** owner
   approved in chat; budget set to $5 USD with thresholds, project filter, and notifications
   verified unchanged. Before/after configs: `.runtime/budget-before-2026-09-26.json`,
   `.runtime/budget-after-2026-09-26.json`.
4. **If the allowances are shared, how should the project get under $5?** (step 6) Options,
   none applied: (a) move this project to its own billing account, which gets its own free
   allowances (owner action, needs a payment method); (b) test the collector at about 0.17
   vCPU (busy-minute CPU is 49% of 0.25), roughly −$1.20/month, with a risk of longer runs;
   (c) cut failed IML scans (about 11% of collector time) by restarting a shifted scan sooner
   or scanning faster, a code change that needs care with county request volume.

## Log

- 2026-09-26 00:10 UTC: Log created. Pull was a no-op at `04e41fa`; working tree clean.
  Live freshness checks all 200 at 00:05 UTC; IML details 3,308/3,308 fresh.
- 2026-09-26 00:14 UTC: Step 0 done. gcloud CLI (`.runtime/google-cloud-sdk`) is signed in
  as the owner account; no default project, so commands pass `--project`. No Application
  Default Credentials (not needed: analysis reads local copies). Mirrored the archive to
  `data/snapshots/current` (rolling mirror for the weekly job) in 36 s: 10,073 files,
  303,597,871 bytes, exactly equal to `gcloud storage du` of the bucket. The PowerShell
  "NativeCommandError" in `.runtime/snapshot-current-rsync.log` is gcloud progress on
  stderr, not a failure (exit 0). The Sept 23 snapshot is kept unchanged as the baseline.
- 2026-09-26 00:30 UTC: Baseline before code changes: 154 tests pass, ruff clean.
  Extracted the profile report's CSS/bars/table into `src/sc_jail/report_html.py` for reuse;
  verified the regenerated Sept 23 profile (`report.html`, `summary.json`) is byte-identical
  to the committed baseline outputs before and after the refactor.
- 2026-09-26 00:32 UTC: Step 1a done. `src/sc_jail/weekly.py` (runner, tested in
  `tests/test_weekly.py`, 6 tests) and `scripts/weekly_analysis.py` (sync via gcloud →
  staleness check → panel → profile; panel failure skips panel-dependent steps; outputs to
  `.partial-*` then renamed to `<Central date>`, an earlier same-date run is kept as
  `.previous-*`; file lock prevents overlap). Real run into the scratchpad with sync:
  complete in 6m16s (mirror 17 s incremental, panel 354 s with all 591 archived populations
  matching, profile 5 s). Panel: 3,817 bookings, 84 permanent-ID changes (was 54 on Sept 23),
  49 missed roster slots (07:00 UTC: 3). Test outputs are in the session scratchpad only.
- 2026-09-26 00:37 UTC: Step 1b done. `src/sc_jail/trends.py` + `scripts/analysis_trends.py`
  (5 tests). Compares weekly profile summaries plus the Sept 23 baseline; a later roster for
  the same date replaces an earlier one. Real run: Sept 23 vs Sept 25 (people held 3,055 →
  3,027; stale court dates 115 → 0 after the detail backlog cleared). Wired into the weekly
  job and verified in an orchestrated run (all steps ok).
- 2026-09-26 00:37 UTC: Step 1c done. `src/sc_jail/reconcile.py` +
  `scripts/reconcile_sources.py` (4 tests). Each distinct XFER workbook (80, every ~2 h) is
  compared with the nearest IML roster (76 within 20 min). Findings: 3,026 bookings in both;
  XFER consistently lists ~137 long-held bookings IML never shows (all booked >1 week
  earlier, 92 >1 year); ~10 IML-held bookings are missing from XFER; book dates agree for all
  shared bookings, case-number sets for 2,913 of 3,026. Runs in ~90 s; wired into the job.
- 2026-09-26 00:37 UTC: Step 1d done. `docs/SOURCE_QUALITY.md` with 16 dated entries,
  including the reconciliation findings. Claims were checked against the archive (for
  example the dispositions folder is still empty at 00:15 UTC; case letters C/H/lowercase c).
- 2026-09-26 00:37 UTC: Step 1e partial. `scripts/run-weekly-analysis.ps1` (wrapper,
  logs to `.runtime/weekly-analysis.log`) and `scripts/install-weekly-task.ps1`. Registered
  `SC-Jail-Weekly-Analysis`: Wednesdays 09:00 local, interactive user (no stored password),
  StartWhenAvailable, 4 h limit, IgnoreNew; next run 2026-09-30 09:00. Wrapper verified
  against the overlap lock (exit 2, logged). Still to do: trigger the task itself once.
- 2026-09-26 00:37 UTC: Step 2 in progress. Found that 315 of 532 new bookings had no case
  entries on their first record page (charges/bonds appear a median ~7 h later, 90% within
  ~24 h), so groups use the first record page with case entries. Added a `bond_types` fact
  to the panel (`src/sc_jail/panel.py`) to tell "not yet assessed" apart; panel test updated.
- 2026-09-26 00:48 UTC: Steps 2–5 code complete and run on a rebuilt panel (3,817 bookings,
  all 591 populations match). New modules, each with tests: `survival.py` (Kaplan-Meier,
  Greenwood/log-log limits checked against a hand calculation), `stays.py` +
  `scripts/length_of_stay.py`, `bonds.py` + `scripts/bond_analysis.py`, `linkage.py` +
  `scripts/court_linkage.py`, `rebooking.py` + `scripts/rebooking.py`. All four are wired
  into the weekly job and report readiness in `run.json`/`index.html`.
  Review fixes made after the first real run: (a) group by the first record page with case
  entries (charge, detainer; median 6.5 h) and the first with a bond decision (bond; median
  20.5 h) instead of the first page fetched; (b) court-date changes reframed: 1,212 "passed
  date replaced" vs 1 reset seen before the hearing; (c) medians from fewer than 10 events are
  no longer printed; (d) indictment timing uses the indicted case's own status.
  Preliminary results (6 days of collection, not readouts): 526 new bookings, median stay 3
  days; recognizance releases median 1 day; bond reductions (53, median cut 66%) followed by
  release a median 1 day later; 79 held now on money bond alone ≤ $5,000 (matches the
  profile exactly); pending-hearings join 518 of 519 consistent; 482 releases followed, 18
  booked again. Step 4 match rates are final for now; everything else waits for data.
- 2026-09-26 00:58 UTC: Docs updated (ANALYSIS.md weekly run + six products, README,
  PLAN.md progress, DECISIONS.md, SOURCE_QUALITY.md); line endings kept as they were
  (ANALYSIS/README/PLAN/DECISIONS/panel.py CRLF). Full suite: 194 passed (154 + 40 new),
  ruff clean.
- 2026-09-26 00:58 UTC: Step 1e done. Started `SC-Jail-Weekly-Analysis` through Task
  Scheduler: LastResult 0, run 00:50:04–00:57:54 UTC, all 9 steps ok (mirror 16 s, panel
  356 s, reconcile 91 s), stderr empty. First real output: `data/analysis/weekly/2026-09-25/`.
  Next scheduled run 2026-09-30 09:00 local.
- 2026-09-26 00:58 UTC: **New owner constraint (chat): the project must stay under
  $5/month.** Step 6 is now a cost review against that target.
- 2026-09-26 01:20 UTC: Step 6 partial. Measured (read-only): Cloud Monitoring billable
  instance time, requests, storage bytes by type, storage operations by method, collector
  CPU/memory utilization; collector logs (335 run summaries); bucket prefixes; image repo;
  budget config (`--billing-project` needed for the Budget API). Prices from the Cloud
  Billing Catalog API. Result: $0.52/month with free allowances, $5.38 without. Added
  `src/sc_jail/usage.py` (3 tests) and `scripts/usage_report.py`, wired into the weekly job
  as step `usage` (alerts shown in index/run output; `--skip-usage`, `--cost-target`).
  Documented in `docs/CLOUD.md` (Measured usage and cost) and DECISIONS.md. Open: review
  items 2–4 (actual charges, $5 budget alert, cost lever if allowances are shared).
- 2026-09-26 01:25 UTC: Step 8 done, no change needed. Alert policies: freshness alerts fire
  when >1 US checker fails for 15 min (checks every 5 min). Uptime history since 0.2.0
  (Sept 23 02:35 → Sept 26 01:15): population check had 33 short failing stretches
  (first-attempt IML failures until the retry) and met the alert condition once (Sept 23
  07:05–07:20, the 07:00 slot); record-page check alerted twice on Sept 23 (backlog);
  courts and repeat visits never failed. The 07:00 slot failed on only 1 of 3 cloud nights;
  5 roster slots missed since cutover. Updated docs/CLOUD.md and SOURCE_QUALITY.md.
- 2026-09-26 01:26 UTC: Step 9 done. Exported `SC-Jail-Stop-Collection` to
  `.runtime/SC-Jail-Stop-Collection.task.xml` (re-register with
  `Register-ScheduledTask -Xml (Get-Content ... -Raw) -TaskName SC-Jail-Stop-Collection`),
  unregistered it, verified it is gone. Only `SC-Jail-Weekly-Analysis` remains.
- 2026-09-26 01:26 UTC: Step 7 in progress. Backup job enabled, daily 05:10 UTC, excludes
  the lease; last operation SUCCESS Sept 25 05:10 (1,179 objects copied). Inventories: all
  8,839 history objects written before the backup are identical (size + CRC32C); only newer
  objects and 6 later-updated projections differ. Restored the backup to
  `data/restore-drill/2026-09-26` (9,117 files, 265,001,340 bytes = backup). History
  verification on the restored copy: 2,066 observations verified, 0 errors.
- 2026-09-26 01:45 UTC: Step 7 done. On the restored copy only (`SCJ_BUCKET` unset,
  confirmed no `.env`, no ADC): `rebuild_index.py` reproduced the backed-up index history
  exactly (515 IML + 543 XFER points; only `attempts`/`last_attempt` differ, which are
  operational); `update_repeat_visits.py --rebuild` reproduced all 18 public fields and
  3,760 private visit records; panel on the restored copy matched all 515 populations.
  Documented in docs/CLOUD.md ("Restore drill - 2026-09-26"). The restored folder
  (265 MB, person-level data) can be deleted when no longer wanted.
- 2026-09-26 01:55 UTC: Final verification. Second Task Scheduler run (01:44:21–01:52:09
  UTC): all 10 steps ok including `usage` (shows the $5.38 no-allowance alert); earlier
  same-day output kept as `2026-09-25.previous-20260926T015209Z`. Privacy/rendering scan of
  all 9 HTML outputs: no booking or case numbers, source-format dates, roster names (3,280
  checked), None/nan, template leftovers, or tracebacks. Full suite 198 passed, ruff clean.
  Nothing committed (39 changed or new files); memory notes added for the flight log and
  the $5 target.
- 2026-09-26 02:00 UTC: Owner approved lowering the budget alert. Updated "SC Jail monthly
  budget" from $15 to $5 USD with `gcloud billing budgets update --budget-amount=5USD`
  (budget ID in the `.runtime` before/after files); thresholds (50/90/100% actual, 100% forecast), project filter,
  and notifications compared equal before and after. Updated docs/CLOUD.md, README.md, and
  DECISIONS.md. Remaining owner items: 1 (Sentenced meaning), 2 (actual charges), 4 (cost
  lever if allowances are shared).
