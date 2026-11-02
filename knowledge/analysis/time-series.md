---
type: Analysis
title: Population time series
description: Daily average population by Central day, its weekday and hour-of-day cycles, and a backtest of simple forecast rules, including the one the dashboard shows.
resource: ../../scripts/time_series.py
tags: [analysis, population, iml, xfer, forecast]
generated: { by: claude-code/claude-fable-5-1, at: 2026-11-02T02:05:00Z }
sources:
  - id: forecast-module
    resource: ../../src/sc_jail/forecast.py
    title: Forecast rule, daily averages, and backtest
  - id: run-2026-10-27
    resource: ../../scripts/time_series.py
    title: Run of scripts/time_series.py on the local mirror through 2026-10-28 13:45 UTC (38 complete days, September 20 to October 27)
---

`scripts/time_series.py` turns every archived population observation into one value per
complete Central day, describes the weekly and daily cycles, and scores simple forecasting
rules on past data. It reads only the aggregate `point` of each observation manifest, so it
uses the whole archive rather than the dashboard's 90-day index and touches no person-level
record. It writes `summary.json` and `report.html` into each [weekly run](weekly-run.md)
(`time-series/`). The rule it recommends is what the dashboard publishes as the
[population forecast](../measures/population-forecast.md)
([decision](../decisions/2026-11-02-dashboard-forecast.md)).

# Definitions

- **Daily average:** the mean of a day's quarter-hour counts in Memphis time. Only complete
  days count: strictly between the first and last observed dates, with at least 24 of the 96
  slots observed. Today is never complete.[^forecast-module]
- **Weekday difference:** for every day whose centered seven-day window is fully observed,
  the day's value minus the window's mean; averaged by weekday. The pattern exists once each
  weekday has one window, about two weeks in.
- **Dashboard rule ("latest day + weekday pattern"):** take the latest complete day, remove
  its weekday difference, add the target day's. No trend term.
- **Backtest:** each rule forecasts from every past day using only the days up to it, so the
  misses are the ones it would really have made. A miss is forecast minus actual. The
  dashboard's shaded range is the miss that 80% of past misses stayed within, per days ahead.

# Findings, September 20 to October 27, 2026 (38 complete days)[^run-2026-10-27]

- **A clear weekly cycle, the same in both sources.** Weekday difference from the
  surrounding week, IML people: Monday +30, Tuesday +31, Wednesday 0, Thursday −8,
  Friday −19, Saturday −22, Sunday 0. XFER bookings: +28, +33, +1, −6, −18, −23, −3. The
  population builds over the weekend and Monday and is worked down from Wednesday to Saturday.
- **No usable trend.** The daily average moved +0.6 (IML) and +0.2 (XFER) a day on average,
  with a day-to-day standard deviation of 22 in both. Drift and straight-line fits lost to
  simply repeating the latest day at every horizon.
- **The hour-of-day cycle is small.** IML runs about +7 at 1 a.m. Central and +5 from 4 to
  6 p.m., and about −4 from 5 a.m. to 1 p.m.; the overnight high and the drop after 2 a.m.
  match the [07:00 UTC purge of released records](../source-quality/iml-0700-roster-shrinks.md).
  XFER runs +5 from 5 to 8 p.m. and −4 around 7 to 8 a.m. Averaging a day removes this.
- **Backtest, mean miss in people (IML; XFER within 1):**

  | Rule | 1 day | 2 | 3 | 4 | 5 | 6 | 7 | Average |
  | --- | --- | --- | --- | --- | --- | --- | --- | --- |
  | Latest day + weekday pattern (dashboard) | 13.9 | 20.5 | 27.9 | 33.7 | 39.1 | 43.2 | 44.3 | 31.8 |
  | Smoothed level (0.3) + weekday pattern | 21.7 | 27.8 | 31.7 | 34.5 | 35.4 | 38.5 | 38.5 | 32.6 |
  | Latest day | 17.8 | 30.8 | 36.2 | 38.0 | 36.2 | 35.5 | 37.5 | 33.1 |
  | Average of last 7 days | 26.6 | 30.1 | 33.0 | 35.4 | 37.0 | 38.6 | 40.6 | 34.5 |
  | Average of last 7 days + weekday pattern | 28.4 | 32.8 | 35.6 | 38.1 | 38.4 | 39.9 | 39.7 | 36.1 |

  The dashboard rule is clearly best one to three days ahead and best on average. From five
  days ahead the plain latest day and the smoothed rule miss less, because a week out the
  level matters more than the weekday shift. The range holding 80% of the dashboard rule's
  past misses widens from ±26 (one day) to ±63 (seven days).
- The one-day-ahead misses were largest on days with thin collection (October 4, 52
  observations, −39; October 16, 31 observations, −44) and around the early-October rise
  and fall.

# Limits

Six weeks of data support a weekday pattern but not seasonality, holidays, or a trend;
the rule will lag any sustained rise or fall. Thin days (outages) are kept when they reach 24
observations and can distort both the average and the next day's forecast. Re-run the
backtest as the archive grows and change the dashboard rule only if another simple rule
beats it on the one-to-three-day misses people actually read.

[^forecast-module]: Forecast rule, daily averages, and backtest
[^run-2026-10-27]: Run of scripts/time_series.py on the local mirror through 2026-10-28 13:45 UTC
