---
type: Cost Measurement
title: Measured usage and cost, 2026-09-26
description: Measured use after the 0.2.0 release projects $0.52 a month if this project gets the billing account's free allowances and $5.38 if it does not.
tags: [cost, cloud, monitoring]
date: 2026-09-26
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:15:07Z }
sources:
  - id: cloud-l230
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/docs/CLOUD.md?plain=1#L230-L269
    title: docs/CLOUD.md lines 230-269, before the OKF migration
    last_modified: 2026-09-26T02:01:31Z
    author: claude-code/claude-opus-5-5
---

The [owner's target](../decisions/2026-09-26-under-5-dollars.md) is **under $5 a month**
for this project. Measured use since the 0.2.0 release (median of full days, September 23
to 25, UTC), projected to an average month at us-central1 list prices from the Cloud
Billing Catalog (checked September 26):

| Item | Measured | Per month | Free allowance | Cost if this project gets the allowance | Cost if it does not |
| --- | --- | --- | --- | ---: | ---: |
| Collector | 20,385 billable s/day, 114 requests/day, 0.25 vCPU, 512 MiB | 158,800 vCPU-s; 317,600 GiB-s (both services) | 180,000 vCPU-s; 360,000 GiB-s | $0.00 (88% used) | $4.61 |
| Dashboard | 483 billable s/day, 3,551 requests/day (almost all uptime checks) | 111,500 requests | 2 million requests | $0.00 | $0.04 |
| Storage | 1.09 GiB billable: live 535 MB (archive + backup), soft-deleted 628 MB, noncurrent 6 MB | 1.09 GiB, growing 2.55 GiB/month | 5 GiB | $0.00 | $0.02 |
| Storage operations | 2,400 writes, 615 lists, 2,845 reads, 4,670 metadata reads a day | 94,900 Class A; 235,700 Class B | 5,000 A; 50,000 B | $0.52 | $0.57 |
| Container images | 0.38 GiB | 0.38 GiB | 0.5 GiB | $0.00 | $0.04 |
| Scheduler | 1 job | 1 job | 3 jobs | $0.00 | $0.10 |
| **Total** | | | | **$0.52** | **$5.38** |

Free allowances belong to the billing account, which has five billing-enabled projects.
If another project uses Cloud Run's allowance, this project's Cloud Run use is billed and
the total passes the $5 target. Only the billing console (Billing, Reports, grouped by
project and SKU, showing free-tier credits) can confirm which case applies; no billing
export is configured. This is an [open question](../questions/cost-allowance-case.md).

Other measurements behind the projection:

- Collector runs take a median 182 s (90th percentile 252 s, maximum 405 s). About 18
  runs a day fail because IML [pagination shifts](../source-quality/iml-pagination-shift.md)
  while the roster changes mid-scan (53 of 55 IML failures), and Scheduler retries them;
  failed scans and retries are about 11% of collector time. Busy-minute CPU use (95th
  percentile) is 49% of the 0.25 vCPU; memory reaches 47% of 512 MiB at the 99th
  percentile, so memory should not be reduced.
- Archive growth is about 44 MB a day: IML roster pages 27 MB, XFER workbooks 14 MB,
  record pages and manifests 3 MB. The backup doubles it. Soft-deleted copies of
  overwritten projections (7-day recovery) add about 0.6 GB at steady state. Storage
  passes 5 GiB in about 1.5 months and would cost about $0.53 a month a year from now.
- The weekly mirror downloads about 1.4 GB a month, within the 100 GiB free monthly
  Cloud Storage download allowance.

The [weekly analysis run](../analysis/weekly-run.md) now includes
[`scripts/usage_report.py`](../../scripts/usage_report.py), which repeats these
measurements, projects both cases against the target (`--cost-target`, default $5), and
shows an alert on the run's index page when either case is at risk. It reads Monitoring
metrics, service sizes, and bucket totals only; it changes nothing. The next recorded
measurement is [September 30, 2026](measured-usage-2026-09-30.md).
