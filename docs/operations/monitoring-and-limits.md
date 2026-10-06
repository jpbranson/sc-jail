---
type: Reference
title: Monitoring and limits
description: Health and freshness endpoints, uptime alerts, the tracker health object, retry behavior, collector time limits, and known alert patterns.
tags: [monitoring, operations]
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-06T20:45:00Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:10:00Z }
sources:
  - id: cloud-l467
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/docs/CLOUD.md?plain=1#L467-L524
    title: docs/CLOUD.md lines 467-524, before the OKF migration
    last_modified: 2026-09-27T21:06:44Z
  - id: courts-parser
    resource: ../../src/sc_jail/courts.py
    title: Court report parser, version 2
---

- `/health` checks the web process. `/api/status` reports source freshness.
  `/api/freshness` returns 503 for failed/overdue population collection or a
  dashboard storage outage. Product checks are available at
  `/api/freshness/iml_details`, `/api/freshness/xfer_courts`, and
  `/api/freshness/repeat_visits`; incomplete supplemental coverage is unhealthy.
  Individual population checks are also available at `/api/freshness/iml` and
  `/api/freshness/xfer`. Repeat analytics is unhealthy if its `through` watermark
  is missing, more than one hour old, or the last refresh reported an error.
  Four five-minute uptime checks alert after sustained failures for 15 minutes.
  A separate log alert watches backup failures. Deployment attaches enabled
  Monitoring notification channels; without one, incidents are console-only.
  The local-compatible `/healthz` alias is retained, but Google's frontend
  returned 404 for that path during deployment; use `/health` for cloud checks.
- `/api/freshness` also carries a `health` object for the project tracker
  (github-project-tracker, DESIGN.md §2), without changing the 200/503 the
  uptime checks use. Each product is a part: "Collecting normally" and
  "Current" read ok; "Coverage incomplete", "Collection failed" and "Delayed"
  warn; "Collection overdue" and "No data" fail. One failed attempt only warns,
  because the tracker ages each `last_success_at` itself (15 minutes expected,
  an hour for repeat visits). The collection is the worse of the two
  population sources, and a storage failure warns.
- After 30 minutes without a successful observation, the dashboard marks that
  source overdue. A scraper exception is displayed immediately.
- XFER's file timestamp is independent of the polling timestamp. A successful
  poll does not imply that the county
  [regenerated its report](../source-quality/xfer-two-hour-regeneration.md).
- Local mode retries population failures once after 60 seconds when the first
  attempt finishes within the slot's first ten minutes. Cloud Scheduler makes at
  most two retries; successful sources are not fetched again. Supplemental or
  repeat-analysis failures alone do not fail the collector request or trigger
  these retries; their freshness checks expose the problem.
- The collector has bounded source timeouts, a 540-second population budget,
  a 600-second request limit, and a 660-second lease with a final commit margin.
- A changing roster can fail completeness validation. That missing interval is
  preferable to a false population change; the next attempt starts a fresh session.
  The 07:00 UTC (2 a.m. Central) IML slot failed this way on September 20, 21,
  and 23 as the roster total fell during every attempt, apparently while released
  records were purged ([source-quality issue](../source-quality/iml-0700-roster-shrinks.md));
  the 07:15 slot succeeded each time. It is not nightly: after the
  cutover it failed only on September 23. From the 0.2.0 release through September 26
  01:15 UTC, five roster slots were missed at scattered times, and the population alert
  (more than one checker failing for 15 minutes) fired once, for the September 23 07:00
  slot. About 25 to 40 times a day an IML scan fails when
  [pagination shifts](../source-quality/iml-pagination-shift.md) and Scheduler retries it, so
  `/api/freshness` returns 503 for about five minutes until the retry succeeds; these blips are
  too short to alert. When every attempt in a slot shifts, the slot is missed and the 503 can
  last long enough to alert. The record-page alert fired twice on
  September 23 during the refresh backlog. No alert change was needed as of September 26.
  From then to October 5, 02:00 UTC, Monitoring recorded seven more population incidents
  (six lasting about ten minutes or less, and one opened at 05:37 UTC on October 4 during the
  [blank permanent ID](../source-quality/iml-blank-permanent-id.md) outage), four record-page
  incidents, one court-report incident, and two repeat-visit incidents. On October 5 that
  population incident and both repeat-visit incidents were still listed as open, although
  every freshness check returned HTTP 200.
- From October 2 to October 6, 20:15 UTC, outside the October 4 outage, ten IML roster slots
  were missed after retries (uptime-check results and collector failure records). Seven were
  pagination shifts on every attempt. The population check met its 15-minute alert condition
  from 21:32 and 22:17 UTC on October 5 and 07:07 UTC on October 6, each a run of shifted
  scans. The other three missed slots (October 6, 19:30 to 20:00 UTC) were a county outage:
  the IML site returned HTTP 404 for every attempt, and the check failed from 19:37 to
  20:17 UTC, a genuine alert. The pagination retry behavior is unchanged.
- Court-report health ignores a few unreadable rows. On October 6 the
  `xfer_courts` check returned 503 from 10:22 UTC because one row of that day's General
  Sessions calendar had an unescaped quote, which made the whole file
  [unsupported](../source-quality/xfer-court-unescaped-quote.md). From court parser
  version 2,[^courts-parser] rows that are not valid CSV or have the wrong number of fields
  are quarantined: left out of the normalized records (the raw file keeps them) and
  counted as `quarantined_rows` in `/api/coverage`, without changing health. A report with
  more quarantined rows than 1% of its data rows (below 100 data rows, any quarantined row)
  stays unsupported, so the check still returns 503 and alerts.
- Cloud outages and source outages cannot be backfilled from a live current
  roster. Original observation times are always preserved.
- A warm dashboard retains the last validated aggregate index during a storage
  outage, marks responses stale, and backs off retries. A cold instance without
  cached data returns 503. Chart output is bounded and cached by index revision,
  range, width bucket, and time bucket. An open page refreshes its text in place every
  60 seconds; each chart is requested once at its displayed width and replaced, after
  it has loaded, only when the index or 5-minute render window changes. Long-range
  change bars aggregate valid observations; gaps are not filled with zeroes.
- Each collection logs a structured `collection_summary` with source status,
  elapsed time, supplemental counts, and repeat-analysis watermark. Observations
  record application/parser versions and a source-content build identifier.

[^courts-parser]: Court report parser, version 2
