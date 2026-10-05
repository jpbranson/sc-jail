---
type: Cost Measurement
title: Measured usage and cost, 2026-09-30
description: The September 30 weekly cost check projects $0.51 a month with the billing account's free allowances and $5.44 without, still above the $5 target.
tags: [cost, cloud, monitoring]
date: 2026-09-30
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:10:00Z }
sources:
  - id: usage-report
    resource: ../../data/analysis/weekly/2026-09-30/usage/summary.json
    title: Weekly usage report, September 30, 2026 (local, Git-ignored run output)
  - id: collector-logs
    resource: Cloud Logging collection_summary entries of sc-jail-collector, 2026-09-25 to 2026-10-05
    title: Collector run summaries
---

The [weekly analysis run](../analysis/weekly-run.md) of September 30 repeated the
[September 26 measurement](measured-usage-2026-09-26.md) with
[`scripts/usage_report.py`](../../scripts/usage_report.py): daily medians over full days from
September 23 to 29 (UTC), projected to an average month at us-central1 list prices, against
the [owner's target](../decisions/2026-09-26-under-5-dollars.md) of under $5 a month.[^usage-report]

| Item | Measured | Per month | Free allowance | Cost if this project gets the allowance | Cost if it does not |
| --- | --- | --- | --- | ---: | ---: |
| Collector | 20,538 billable s/day, 119 requests/day, 0.25 vCPU, 512 MiB | 160,300 vCPU-s; 320,500 GiB-s (both services) | 180,000 vCPU-s; 360,000 GiB-s | $0.00 (89% used) | $4.65 |
| Dashboard | 522 billable s/day, 3,558 requests/day | 111,900 requests | 2 million requests | $0.00 | $0.04 |
| Storage | 2.79 GiB billable: live 893 MB (archive + backup), soft-deleted 2,090 MB, noncurrent 15 MB | 2.79 GiB, growing 2.54 GiB/month | 5 GiB | $0.00 | $0.06 |
| Storage operations | 2,289 writes, 642 lists, 2,998 reads, 4,713 metadata reads a day | 90,800 Class A; 241,100 Class B | 5,000 A; 50,000 B | $0.51 | $0.55 |
| Container images | 0.45 GiB | 0.45 GiB | 0.5 GiB | $0.00 | $0.05 |
| Scheduler | 1 job | 1 job | 3 jobs | $0.00 | $0.10 |
| **Total** | | | | **$0.51** | **$5.44** |

Compared with September 26:

- The no-allowance case rose from $5.38 to $5.44 and stays above the target; Cloud Run CPU
  is still most of it. Which case applies is still an
  [open question](../questions/cost-allowance-case.md).
- Soft-deleted storage grew from 628 MB to 2,090 MB, about three and a half times the roughly
  0.6 GB the September 26 measurement expected at steady state, and is now about 70% of
  billable storage. At 2.54 GiB a month of growth, storage passes the 5 GiB free allowance in about
  0.9 months (about 1.5 months on September 26) and would cost about $0.57 a month a year
  from now.
- Container images reached 0.45 GiB, 90% of the 0.5 GiB free allowance.

Collector logs for September 25 to 29 show runs taking a median 175 s (90th percentile
237 s, maximum 408 s), against 182 s, 252 s, and 405 s on September 26. From September 26
to October 4 05:00 UTC, 205 IML attempts failed (about 25 a day), almost all
[pagination shifts](../source-quality/iml-pagination-shift.md).[^collector-logs]

[^usage-report]: Weekly usage report, September 30, 2026
[^collector-logs]: Collector run summaries
