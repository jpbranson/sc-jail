---
type: Project Overview
title: Shelby County jail
description: Two Python source collectors, case detail archives, and a small Flask dashboard that measure the Shelby County jail population from two county sources.
tags: [population, iml, xfer, dashboard]
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T01:54:59Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:06:36Z }
sources:
  - id: readme-l1
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/README.md?plain=1#L1-L31
    title: README.md lines 1-31, before the OKF migration
    last_modified: 2026-10-04T16:36:20Z
  - id: readme-l257
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/README.md?plain=1#L257-L260
    title: README.md lines 257-260, before the OKF migration
    last_modified: 2026-09-22T16:39:10Z
---

Two Python source collectors, case detail archives, and a small Flask dashboard.
[Cloud collections](operations/cloud-deployment.md) run on UTC quarter hours; the local
scheduler also attempts a collection when started. The two county sources are measured
separately:

- **IML:** distinct permanent IDs with a blank release date or one after today's
  Memphis date. The complete result set includes recently released records,
  which remain in the private archive but are excluded from the current count.
  A booking listed before IML assigns its permanent ID is archived but counts no one.
  See [IML population](measures/iml-population.md) and the [IML roster](sources/iml-roster.md).
- **XFER:** distinct booking numbers in `/SCSO-InJail/SCSO-InJail.xls`. A person
  can have several charge rows and potentially several bookings.
  See [XFER bookings](measures/xfer-bookings.md) and the
  [XFER jail workbook](sources/xfer-jail-workbook.md).

IML individual pages and the relevant XFER criminal court reports are collected
in bounded batches after the population runs. Detail pages target a daily
refresh; court folders are checked each interval and unchanged files are verified
daily. See [case data](architecture/case-data-collection.md),
[private exports](operations/exports.md), and [refresh settings](architecture/configuration.md).
The dashboard shows actual detail coverage and report backlog. It also charts
[repeat visits and time between visits](measures/repeat-visits.md) using distinct
bookings linked by IML permanent ID across the full archive.
A private [population profile](analysis/population-profile.md) and
[booking panel](analysis/booking-panel.md) summarize time held,
case status, charges, bonds, and court dates, and follow each booking over time, from
a local archive copy. A [weekly analysis run](analysis/weekly-run.md)
rebuilds them with [trends](analysis/trends.md), an
[IML/XFER reconciliation](analysis/source-reconciliation.md), and
[length-of-stay](analysis/length-of-stay.md), [money-bond](analysis/money-bond.md),
[court-linkage](analysis/court-linkage.md), and [re-booking](analysis/rebooking.md) analyses.
Source behaviors that affect these measures are kept in the
[source-quality log](source-quality/index.md).

The dashboard uses Shiny-like controls, Inter text, and minimal SVG charts.
All interface and chart text is at least 16 CSS px (12 pt). The public surface
contains aggregates; names, dates of birth, and source records stay in private
storage.

# Original references

[jpbranson/shelby.county](https://github.com/jpbranson/shelby.county) and
[jpbranson/memphis.xfer](https://github.com/jpbranson/memphis.xfer).
See the [original plan](history/2026-09-19-original-plan.md) and the
[decisions](decisions/index.md).
