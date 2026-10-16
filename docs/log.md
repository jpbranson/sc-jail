# Knowledge bundle update log

## 2026-10-15
* **Update**: Merged the [October 6 collector update](deployments/2026-10-06.md) record
  written on October 6 into the reconstructed one, confirming the build commit (`dad628b`)
  and adding the build's test results and the court-report re-parse backlog; updated
  [retained images](deployments/retained-images.md) to match.
* **Verification**: Checked the bundle against the code at `b80fab0`, the live Google Cloud
  project (read-only), collector logs, and Monitoring. Corrected the
  [07:00 UTC roster](source-quality/iml-0700-roster-shrinks.md) (missed again October 9, 11, 12,
  and 13), the [pagination-shift](source-quality/iml-pagination-shift.md) rate, the
  [blank permanent ID](source-quality/iml-blank-permanent-id.md) evidence (and removed a booking
  number from it), alert history in [monitoring and limits](operations/monitoring-and-limits.md),
  court-report storage in [archive layout](architecture/archive-layout.md) and
  [case-data storage](architecture/case-data-storage.md),
  [storage growth](architecture/storage-growth.md), the
  [weekly run](analysis/weekly-run.md) (October runs not recorded here),
  [population profile](analysis/population-profile.md) wording, the narrowed
  [XFER scope decision](decisions/2026-09-19-xfer-jail-report-scope.md), and workspace-specific
  paths in [deployment](operations/deploy.md) and [local setup](operations/local-setup.md).
  Analysis numbers from the September 30 run could not be re-derived on this machine.
* **Update**: Recorded the [October 15 deployment](deployments/2026-10-15.md), the first from
  macOS, and reconstructed the unrecorded [October 6 collector update](deployments/2026-10-06.md)
  from Cloud Run, Cloud Build, and audit logs; updated [retained images](deployments/retained-images.md),
  [cloud deployment](operations/cloud-deployment.md), and [deployment](operations/deploy.md).
* **Creation**: Recorded the October 15 IML outage, which ended with the county server
  answering every request with a stack trace and HTTP 200, and the clearer error it now produces:
  the [source-quality issue](source-quality/iml-server-error-page.md) and an update to
  [monitoring and limits](operations/monitoring-and-limits.md).

## 2026-10-06
* **Update**: Recorded the [October 6 collector deployment](deployments/2026-10-06.md) and
  updated [retained images](deployments/retained-images.md) and the
  [cloud deployment](operations/cloud-deployment.md).
* **Creation**: Quarantined unreadable court-report rows after one unescaped quote kept the
  court-report alert open: the [decision](decisions/2026-10-06-quarantine-unreadable-court-rows.md),
  the [source-quality issue](source-quality/xfer-court-unescaped-quote.md), and updates to
  [XFER court reports](sources/xfer-court-reports.md) and [exports](operations/exports.md).
* **Update**: Recorded why freshness alerts recurred from October 2 to 6 in
  [monitoring and limits](operations/monitoring-and-limits.md), and the latest rate of
  [pagination shifts](source-quality/iml-pagination-shift.md).

## 2026-10-05
* **Verification**: Checked every current-state concept against the live Google Cloud
  project (read-only), the code at `61a6e3a`, and the September 30 weekly analysis run; 101
  of 125 concepts now carry a machine-confirmed `verified` entry (the rest are dated records,
  superseded items, and one open question). Fixed claims that were no longer
  true in [weekly run](analysis/weekly-run.md) (missing usage step),
  [booking panel](analysis/booking-panel.md) and
  [07:00 UTC roster](source-quality/iml-0700-roster-shrinks.md) (the slot has not failed since
  September 23), [retained images](deployments/retained-images.md),
  [deployment](operations/deploy.md) (second gcloud install), and
  [maintaining the bundle](maintaining-knowledge.md) (agent verification rule). Added dated
  September 30 readings to the analyses and source-quality issues, alert history to
  [monitoring and limits](operations/monitoring-and-limits.md), and the
  [September 30 cost measurement](cost/measured-usage-2026-09-30.md).
* **Migration**: Converted all project knowledge into this Open Knowledge Format v0.2 bundle.
  The pre-migration files (`README.md`, `PLAN.md`, `DECISIONS.md`, `FLIGHT_LOG.md`, and
  `docs/*.md` as of commit `61a6e3a`) were split into concepts with frontmatter; each
  concept's `sources` cites the exact original lines, with `last_modified` and `author` taken
  from `git blame`. Added [maintaining the knowledge bundle](maintaining-knowledge.md) and
  `scripts/check_knowledge.py`. Earlier entries were reconstructed from the Git history of the
  pre-migration files; all dates are UTC.

## 2026-10-04
* **Update**: Recorded what the IML/XFER gap is and is not: the September 30
  [reconciliation](analysis/source-reconciliation.md), the
  [XFER-only bookings](source-quality/iml-xfer-hidden-bookings.md), and the
  [IML-held bookings missing from XFER](source-quality/iml-xfer-missing-from-xfer.md).
* **Update**: Recorded the October 4 deployments at [16:06](deployments/2026-10-04-1606.md)
  and [16:24 UTC](deployments/2026-10-04-1624.md).
* **Creation**: Accepted IML roster rows with a blank permanent ID: the
  [decision](decisions/2026-10-04-blank-permanent-id.md), the
  [source-quality issue](source-quality/iml-blank-permanent-id.md), and updates to the
  [IML population](measures/iml-population.md), [repeat visits](measures/repeat-visits.md),
  [booking panel](analysis/booking-panel.md), and [re-booking](analysis/rebooking.md).

## 2026-09-28
* **Update**: Recorded the [September 28 deployment](deployments/2026-09-28.md).

## 2026-09-27
* **Update**: Recorded the [September 27 deployment](deployments/2026-09-27.md).
* **Update**: Documented the `/api/freshness` `health` object for the project tracker in
  [monitoring and limits](operations/monitoring-and-limits.md).

## 2026-09-26
* **Update**: Recorded the [September 26 deployment](deployments/2026-09-26.md).
* **Update**: Documented charts loaded at their displayed width and in-place page refresh in
  [monitoring and limits](operations/monitoring-and-limits.md).
* **Creation**: Added the [weekly analysis run](analysis/weekly-run.md), the staged analyses
  ([length of stay](analysis/length-of-stay.md), [money bond](analysis/money-bond.md),
  [court linkage](analysis/court-linkage.md), [re-booking](analysis/rebooking.md),
  [trends](analysis/trends.md), [reconciliation](analysis/source-reconciliation.md)), the
  [source-quality log](source-quality/index.md), the
  [measured usage and cost](cost/measured-usage-2026-09-26.md), the
  [restore drill](operations/restore-drill-2026-09-26.md), and the
  [next-steps run log](history/next-steps-run-2026-09.md).

## 2026-09-23
* **Creation**: Added the [booking panel](analysis/booking-panel.md) and the staged
  [analysis plan](analysis/plan.md).
* **Creation**: Added the [population profile](analysis/population-profile.md).
* **Update**: Documented the early IML detail refresh in
  [IML record pages](sources/iml-record-pages.md), the
  [configuration](architecture/configuration.md), and the
  [detail-refresh fix deployment](deployments/2026-09-23-detail-refresh-fix.md).
* **Update**: Refreshed setup and cloud operations guidance.
* **Creation**: Added the [technical audit](history/2026-09-23-technical-audit.md) and the
  [0.2.0 release record](deployments/2026-09-23-release-0-2-0.md); updated recovery, backup,
  and storage guidance.

## 2026-09-22
* **Initialization**: First commit of the project's README, plan, decision record, and the
  cloud, storage, case-data, and repeat-visit documents, covering work from 2026-09-19 to the
  [cloud cutover](deployments/2026-09-22-cutover.md).
