---
type: Metric
title: Population forecast
description: The dashboard's seven-day forecast of each source's daily average population is the latest complete day's level shifted by the usual weekday difference, shown against what actually happened.
resource: ../../src/sc_jail/forecast.py
tags: [population, dashboard, forecast, iml, xfer]
generated: { by: claude-code/claude-fable-5-1, at: 2026-11-02T02:05:00Z }
sources:
  - id: forecast-module
    resource: ../../src/sc_jail/forecast.py
    title: Forecast rule, daily averages, and backtest
---

# Definition

For each source ([IML people](iml-population.md) and [XFER bookings](xfer-bookings.md)), the
dashboard's "Population forecast" panel shows:[^forecast-module]

- **Daily average:** the mean of the day's quarter-hour counts in Memphis time, for complete
  days only (strictly between the first and last observed dates, at least 24 of 96 slots).
- **Forecast made the day before:** for each past day, what the rule predicted from the
  previous complete day; blank after a missing day. The values table lists the signed miss
  (forecast minus actual) and the average one-day miss over the days scored.
- **The week ahead:** seven daily forecasts from the latest complete day, each with the range
  that held 80% of the rule's past misses at that distance ahead.

The rule: `forecast = latest day's average − its weekday difference + the target weekday's
difference`, where each weekday's difference is its average gap from the surrounding week
over the dashboard's 90-day history. It has no trend term. Until about two weeks of complete
days exist (every weekday with a fully observed surrounding week) the panel says the forecast
is not yet available.

The forecast is computed by the dashboard from the public 90-day index at request time, not
stored or collected ([decision](../decisions/2026-11-02-dashboard-forecast.md)). Its
method, backtest, and findings are in the [population time series](../analysis/time-series.md)
analysis, which the weekly run repeats on the full archive.

[^forecast-module]: Forecast rule, daily averages, and backtest
