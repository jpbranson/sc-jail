---
type: Reference
title: Configuration
description: Environment variables for the archive location, HTTP identity, IML scan budget, build provenance, and case-data batch, budget, and refresh settings.
resource: ../../src/sc_jail/config.py
tags: [operations, iml-details, xfer-courts]
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T01:54:59Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:06:36Z }
sources:
  - id: readme-l128
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/README.md?plain=1#L128-L143
    title: README.md lines 128-143, before the OKF migration
    last_modified: 2026-09-23T03:04:09Z
  - id: case-data-l145
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/docs/CASE_DATA.md?plain=1#L145-L179
    title: docs/CASE_DATA.md lines 145-179, before the OKF migration
    last_modified: 2026-09-23T05:06:55Z
---

# General

| Variable | Default | Meaning |
| --- | --- | --- |
| `SCJ_DATA_DIR` | `data` | Local archive root |
| `SCJ_BUCKET` | unset | Use a private Google Cloud Storage bucket instead of local disk |
| `SCJ_USER_AGENT` | project research identifier | HTTP identification; optionally add a contact URL |
| `PORT` | `8050` | Server port unless `--port` is provided |
| `SCJ_IML_TIMEOUT_SECONDS` | `420` | IML roster scan budget in seconds (maximum 480) |
| `SCJ_IML_PAGE_WORKERS` | `2` | Concurrent IML roster page requests (1 or 2) |
| `SCJ_BUILD_REVISION` | `development` | Provenance identifier; the deployment supplies a source-content hash at image build time |

Supplemental batch, budget, and refresh variables are listed below. `SCJ_BUCKET` takes
precedence over `SCJ_DATA_DIR`; local relative paths resolve from the working
directory, which the PowerShell launcher sets to the repository root.

# Case data

| Environment variable | Default |
| --- | ---: |
| SCJ_DETAIL_BATCH | 80 pages |
| SCJ_DETAIL_BUDGET | 120 seconds |
| SCJ_DETAIL_REFRESH_HOURS | 24 hours |
| SCJ_DETAIL_REFRESH_AHEAD_HOURS | 4 hours |
| SCJ_COURT_BATCH | 8 files |
| SCJ_COURT_BUDGET | 60 seconds |
| SCJ_COURT_VERIFY_HOURS | 24 hours |

Batch sizes must be integers from 0 through 2,000. Budgets and refresh intervals
must be finite positive numbers. A zero detail batch skips page downloads but can
still publish cached coverage; a zero court batch defers the court pass. Neither
setting disables its freshness alert.

The early-refresh lead must be finite and nonnegative; zero disables it. The
effective lead is capped at one quarter of `SCJ_DETAIL_REFRESH_HOURS`, preserving
at least 75% of short custom refresh intervals. Early refreshes use the existing
batch and time limits and can increase successful page requests (a 20-hour cycle
is about 20% more frequent than a 24-hour cycle). Freshness reporting and alerts
continue to use the full configured interval. Large backlogs or prolonged source
failures can still exceed the headroom and will continue to alert.

The overall collection execution budget takes precedence over these settings.
Population observations commit first; supplementary failures preserve those
results and the last successful case records. Coverage status records partial
failures and overdue passes. `/api/coverage` reports those details; product-specific
freshness endpoints return HTTP 503 when unhealthy. Supplemental errors or
incomplete coverage do not alone change a successful population request into a
failed collector request. Local scheduling and the Cloud Run collector both use
this same path. Increasing batch sizes may increase traffic,
compute use, and storage; the dashboard reports actual progress rather than
assuming the configured daily target was met.

These settings govern [IML record pages](../sources/iml-record-pages.md),
[XFER court reports](../sources/xfer-court-reports.md), and the
[case-data collection](case-data-collection.md) pass.
