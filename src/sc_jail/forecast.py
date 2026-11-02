"""A simple population forecast: the latest complete day's level plus the usual weekday difference.

The dashboard history shows a clear weekly cycle (Monday and Tuesday high, Friday and
Saturday low) and no reliable trend, so the forecast takes the most recent complete day,
removes that weekday's usual difference from its week, and adds the target weekday's.
Everything here works on daily average counts, so no person-level data is involved.
"""

import statistics
from collections import defaultdict
from datetime import datetime, timedelta

MIN_OBSERVATIONS = 24  # a quarter of a day's 96 slots; fewer and the day's average is not trusted
HORIZON = 7
BAND_SHARE = 0.8
MIN_ERRORS = 5
WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
NOT_YET = "Forecast needs two weeks of complete days"


def daily_means(points, zone):
    """Average population per complete local day: strictly between the first and last
    observed dates, with at least MIN_OBSERVATIONS observations. Today is never complete."""
    by_day = defaultdict(list)
    for point in points:
        day = datetime.fromisoformat(point["observed_at"]).astimezone(zone).date()
        by_day[day].append(point["population"])
    if len(by_day) < 3:
        return {}
    first, last = min(by_day), max(by_day)
    return {
        day: {"mean": statistics.mean(values), "observations": len(values)}
        for day, values in sorted(by_day.items())
        if first < day < last and len(values) >= MIN_OBSERVATIONS
    }


def weekday_offsets(series):
    """How much each weekday usually differs from the average of its surrounding week.

    Uses every day whose seven-day window centered on it is fully observed. Returns None
    until each weekday has at least one such window (about two weeks of data).
    """
    deviations = defaultdict(list)
    for day, entry in series.items():
        window = [day + timedelta(days=k) for k in range(-3, 4)]
        if all(d in series for d in window):
            week = statistics.mean(series[d]["mean"] for d in window)
            deviations[day.weekday()].append(entry["mean"] - week)
    if len(deviations) < 7:
        return None
    return {weekday: statistics.mean(values) for weekday, values in deviations.items()}


def weekday_rule(series, origin, horizon=HORIZON):
    """Forecast the days after ``origin`` from its level and the weekday pattern known so far."""
    offsets = weekday_offsets(series)
    if offsets is None or origin not in series:
        return []
    level = series[origin]["mean"] - offsets[origin.weekday()]
    targets = [origin + timedelta(days=h) for h in range(1, horizon + 1)]
    return [(target, level + offsets[target.weekday()]) for target in targets]


def backtest(series, model=weekday_rule, horizon=HORIZON):
    """Forecast from every past day using only the days up to it, paired with what happened."""
    records = []
    days = sorted(series)
    for index, origin in enumerate(days):
        known = {day: series[day] for day in days[: index + 1]}
        for target, value in model(known, origin, horizon):
            if target in series:
                records.append({"origin": origin, "target": target, "ahead": (target - origin).days,
                                "forecast": value, "actual": series[target]["mean"]})
    return records


def errors_by_horizon(records, horizon=HORIZON):
    """Signed misses (forecast minus actual) grouped by days ahead."""
    errors = {h: [] for h in range(1, horizon + 1)}
    for record in records:
        errors[record["ahead"]].append(record["forecast"] - record["actual"])
    return errors


def band(errors):
    """The miss that BAND_SHARE of past misses stayed within, or None with too few of them."""
    if len(errors) < MIN_ERRORS:
        return None
    misses = sorted(abs(error) for error in errors)
    return misses[int(BAND_SHARE * (len(misses) - 1))]


def hour_of_day(points, zone, series):
    """Average difference between an observation and its day's average, by local hour."""
    deviations = defaultdict(list)
    for point in points:
        moment = datetime.fromisoformat(point["observed_at"]).astimezone(zone)
        if moment.date() in series:
            deviations[moment.hour].append(point["population"] - series[moment.date()]["mean"])
    return {hour: statistics.mean(values) for hour, values in sorted(deviations.items())}


def summarize(index, source, zone, shown_days=28):
    """Everything the chart, the page table, and the weekly report show for one source."""
    points = index.get("sources", {}).get(source, {}).get("history", [])
    series = daily_means(points, zone)
    offsets = weekday_offsets(series)
    summary = {"source": source, "available": False, "note": None, "offsets": None,
               "origin": None, "days": [], "ahead": [], "typical_miss": None, "errors": 0}
    if offsets is None:
        summary["note"] = NOT_YET
        return summary
    records = backtest(series)
    errors = errors_by_horizon(records)
    day_before = {r["target"]: r["forecast"] for r in records if r["ahead"] == 1}
    days = sorted(series)
    origin = days[-1]
    summary.update(
        available=True,
        offsets={WEEKDAYS[weekday]: round(offsets[weekday], 1) for weekday in range(7)},
        origin=origin.isoformat(),
        days=[{
            "date": day.isoformat(),
            "actual": round(series[day]["mean"]),
            "observations": series[day]["observations"],
            "forecast": round(day_before[day]) if day in day_before else None,
            "miss": round(day_before[day] - series[day]["mean"]) if day in day_before else None,
        } for day in days[-shown_days:]],
        ahead=[{
            "date": target.isoformat(),
            "forecast": round(value),
            "low": round(value - spread) if spread is not None else None,
            "high": round(value + spread) if spread is not None else None,
        } for (target, value), spread in zip(weekday_rule(series, origin),
                                            (band(errors[h]) for h in range(1, HORIZON + 1)))],
        typical_miss=round(statistics.mean(abs(e) for e in errors[1]), 1) if errors[1] else None,
        errors=len(errors[1]),
    )
    return summary
