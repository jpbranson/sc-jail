"""Kaplan-Meier estimates for right-censored durations in whole days.

At a tied time, events are counted before censorings (the usual convention), so a
booking censored on day t is still at risk for releases on day t. Confidence limits use
Greenwood's variance on the log(-log) scale, which keeps them inside 0 and 1. Estimates
are undefined after the longest observed duration, so lookups there return None.
"""

import math

Z95 = 1.959963984540054


def kaplan_meier(observations):
    """Rows for each distinct duration: at risk, events, censored, survival, 95% limits.

    ``observations`` is an iterable of (duration, event) with duration >= 0.
    """
    data = sorted((duration, bool(event)) for duration, event in observations)
    if any(duration < 0 for duration, _ in data):
        raise ValueError("Durations must be nonnegative")
    rows, survival, greenwood, at_risk, index = [], 1.0, 0.0, len(data), 0
    while index < len(data):
        time = data[index][0]
        events = censored = 0
        while index < len(data) and data[index][0] == time:
            events += data[index][1]
            censored += not data[index][1]
            index += 1
        if events:
            survival *= 1 - events / at_risk
            greenwood = (greenwood + events / (at_risk * (at_risk - events))
                         if at_risk > events else math.inf)
        lower = upper = None
        if 0 < survival < 1 and math.isfinite(greenwood):
            spread = Z95 * math.sqrt(greenwood) / abs(math.log(survival))
            lower, upper = survival ** math.exp(spread), survival ** math.exp(-spread)
        rows.append({"time": time, "at_risk": at_risk, "events": events, "censored": censored,
                     "survival": survival, "lower": lower, "upper": upper})
        at_risk -= events + censored
    return rows


def _row_at(rows, time):
    if not rows or time > rows[-1]["time"]:
        return None
    current = None
    for row in rows:
        if row["time"] > time:
            break
        current = row
    return current


def survival_at(rows, time):
    """Estimated share still without the event after ``time`` days; None beyond follow-up."""
    if not rows or time > rows[-1]["time"]:
        return None
    row = _row_at(rows, time)
    return 1.0 if row is None else row["survival"]


def limits_at(rows, time):
    row = _row_at(rows, time)
    return (None, None) if row is None else (row["lower"], row["upper"])


def at_risk_at(rows, time):
    """Number still followed and without the event at the start of day ``time``."""
    if not rows:
        return 0
    return sum(r["events"] + r["censored"] for r in rows if r["time"] >= time)


def quantile(rows, share):
    """First duration at which the event share reaches ``share`` (0.5 is the median)."""
    for row in rows:
        if row["survival"] <= 1 - share + 1e-12:
            return row["time"]
    return None


def curve(rows):
    """(time, survival) steps for plotting."""
    return [(row["time"], row["survival"]) for row in rows if row["events"]]


def summarize(observations, days=(1, 2, 3, 7, 14, 30)):
    """Counts, median, and survival with limits at fixed days for one group."""
    observations = list(observations)
    rows = kaplan_meier(observations)
    return {
        "n": len(observations),
        "events": sum(1 for _, event in observations if event),
        "censored": sum(1 for _, event in observations if not event),
        "longest_followup": rows[-1]["time"] if rows else None,
        "median": quantile(rows, 0.5),
        "quartile_1": quantile(rows, 0.25),
        "quartile_3": quantile(rows, 0.75),
        "at": {str(day): {"still_held": survival_at(rows, day),
                          "lower": limits_at(rows, day)[0] if survival_at(rows, day) is not None else None,
                          "upper": limits_at(rows, day)[1] if survival_at(rows, day) is not None else None,
                          "at_risk": at_risk_at(rows, day + 1)}
               for day in days},
        "curve": curve(rows),
    }
