---
type: Decision
title: Show a weekday-adjusted latest-day forecast on the dashboard
description: The dashboard forecasts both sources' daily average with the latest complete day shifted by the weekday pattern, computed from the public index at request time, with its past misses shown alongside.
tags: [dashboard, forecast, analysis]
decided: 2026-11-02
generated: { by: claude-code/claude-fable-5-1, at: 2026-11-02T02:05:00Z }
sources:
  - id: time-series
    resource: ../analysis/time-series.md
    title: Population time series analysis, findings through October 27, 2026
---

Add a "Population forecast" panel to the public dashboard for both the IML and XFER
population series, using one rule: the latest complete day's average, with that weekday's
usual difference removed and the target weekday's added. Show the forecast the rule made one
day earlier next to each actual day, and a seven-day forecast with the range that held 80%
of the rule's past misses. Compute it in the dashboard from the public 90-day index at
request time; nothing is stored, collected, or added to the cloud services.

The owner chose this over a smoothed-level variant and over fitted models because it is
explainable in one sentence, has no tuning constant, and had the smallest misses one to three
days ahead in the backtest (14 people one day ahead, against 18 for repeating the latest day
and 22 for the smoothed variant). A week ahead the plain latest day misses less (37 against
44), which is accepted: the panel's own band makes that uncertainty visible.[^time-series]
No forecasting library is added; the rule is standard-library Python.

Related: [population forecast](../measures/population-forecast.md),
[population time series](../analysis/time-series.md),
[no new infrastructure](2026-09-23-no-new-infrastructure.md).

[^time-series]: Population time series analysis, findings through October 27, 2026
