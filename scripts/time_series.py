"""Population time series and forecast backtest (JSON and HTML) from a local archive copy.

    python scripts/time_series.py --data-dir data/snapshots/current --output data/analysis/time-series

Reads the aggregate point of every archived population observation, never the person-level
records, so the whole history is used rather than the dashboard's 90-day index. Describes
the weekday and hour-of-day cycles, compares a few simple forecasting rules on past data,
and reports the forecast the dashboard shows. Aggregate counts only.
"""

import argparse
import json
import statistics
from datetime import timedelta
from pathlib import Path

from sc_jail import forecast
from sc_jail.iml import CHICAGO
from sc_jail.report_html import document, notes, table, tiles
from sc_jail.storage import LocalStore, read_json

NAMES = {"iml": "IML roster (people)", "xfer": "In-jail report (bookings)"}
SHOWN = 28
SMOOTHING = 0.3
HORIZONS = range(1, forecast.HORIZON + 1)


def population_points(store, source):
    keys = [k for k in store.keys(f"private/observations/{source}/") if k.endswith(".json.gz")]
    return sorted((read_json(store, key)[0]["point"] for key in keys), key=lambda p: p["slot"])


def latest_day(series, origin, horizon):
    return [(origin + timedelta(days=h), series[origin]["mean"]) for h in range(1, horizon + 1)]


def week_average(series, origin, horizon):
    week = [series[origin - timedelta(days=k)]["mean"] for k in range(7)
            if origin - timedelta(days=k) in series]
    return [(origin + timedelta(days=h), statistics.mean(week)) for h in range(1, horizon + 1)]


def week_average_weekday(series, origin, horizon):
    offsets = forecast.weekday_offsets(series)
    if offsets is None:
        return []
    return [(day, value + offsets[day.weekday()])
            for day, value in week_average(series, origin, horizon)]


def smoothed_weekday(series, origin, horizon):
    """Exponentially smoothed level of the weekday-adjusted series, plus the weekday pattern."""
    offsets = forecast.weekday_offsets(series)
    if offsets is None:
        return []
    level = None
    for day in sorted(series):
        adjusted = series[day]["mean"] - offsets[day.weekday()]
        level = adjusted if level is None else SMOOTHING * adjusted + (1 - SMOOTHING) * level
    targets = [origin + timedelta(days=h) for h in range(1, horizon + 1)]
    return [(day, level + offsets[day.weekday()]) for day in targets]


MODELS = [
    ("Latest day + weekday pattern (the dashboard rule)", forecast.weekday_rule),
    (f"Smoothed level ({SMOOTHING}) + weekday pattern", smoothed_weekday),
    ("Average of last 7 days + weekday pattern", week_average_weekday),
    ("Average of last 7 days", week_average),
    ("Latest day", latest_day),
]


def mean_absolute(errors):
    return round(statistics.mean(abs(e) for e in errors), 1) if errors else None


def analyze(points):
    series = forecast.daily_means(points, CHICAGO)
    summary = forecast.summarize({"sources": {"x": {"history": points}}}, "x", CHICAGO, SHOWN)
    backtests = {}
    for label, model in MODELS:
        errors = forecast.errors_by_horizon(forecast.backtest(series, model))
        backtests[label] = {h: mean_absolute(errors[h]) for h in HORIZONS}
    bands = forecast.errors_by_horizon(forecast.backtest(series))
    days = sorted(series)
    changes = [series[b]["mean"] - series[a]["mean"] for a, b in zip(days, days[1:])
               if (b - a).days == 1]
    return {
        "complete_days": len(series),
        "first_day": days[0].isoformat() if days else None,
        "last_day": days[-1].isoformat() if days else None,
        "daily_change_mean": round(statistics.mean(changes), 1) if changes else None,
        "daily_change_sd": round(statistics.pstdev(changes), 1) if len(changes) > 1 else None,
        "hour_of_day": {h: round(v, 1) for h, v in
                        forecast.hour_of_day(points, CHICAGO, series).items()},
        "backtest_mae": backtests,
        "band": {h: (round(forecast.band(bands[h]), 1) if forecast.band(bands[h]) is not None
                     else None) for h in HORIZONS},
        "forecast": summary,
    }


def show(value, signed=False):
    if value is None:
        return "–"
    return f"{value:+,.1f}" if signed else f"{value:,.1f}"


def source_section(source, r):
    f = r["forecast"]
    parts = [f"<h2>{NAMES[source]}</h2>", tiles([
        ("Complete days", f"{r['complete_days']:,}"),
        ("Typical one-day miss", show(f["typical_miss"])),
        ("Day-to-day change", f"{show(r['daily_change_mean'], True)} ± {show(r['daily_change_sd'])}"),
        ("Weekday swing", f"{max(f['offsets'].values()) - min(f['offsets'].values()):,.0f}"
         if f["offsets"] else "–"),
    ])]
    if not f["available"]:
        return parts + [f"<p>{f['note']}.</p>"]
    parts.append("<h3>Usual weekday difference from the surrounding week</h3>")
    parts.append(table(["Weekday", "Difference"],
                       [[day, show(value, True)] for day, value in f["offsets"].items()]))
    parts.append("<h3>How simple rules would have done (mean miss by days ahead)</h3>")
    parts.append(table(["Rule"] + [f"{h} day{'s' if h > 1 else ''}" for h in HORIZONS] + ["Average"], [
        [label] + [show(mae[h]) for h in HORIZONS]
        + [show(statistics.mean(v for v in mae.values() if v is not None))
           if any(v is not None for v in mae.values()) else "–"]
        for label, mae in r["backtest_mae"].items()
    ]))
    parts.append("<h3>Range that held 80% of the dashboard rule's past misses</h3>")
    parts.append(table(["Days ahead"] + [str(h) for h in HORIZONS],
                       [["±"] + [show(r["band"][h]) for h in HORIZONS]]))
    parts.append(f"<h3>Last {SHOWN} complete days and the week ahead</h3>")
    rows = [[d["date"], f"{d['actual']:,}", f"{d['observations']}",
             f"{d['forecast']:,}" if d["forecast"] is not None else "–",
             f"{d['miss']:+,}" if d["miss"] is not None else "–"] for d in f["days"]]
    rows += [[d["date"], "–", "–", f"{d['forecast']:,}",
              f"{d['low']:,} to {d['high']:,}" if d["low"] is not None else "–"] for d in f["ahead"]]
    parts.append(table(["Central date", "Daily average", "Observations",
                        "Forecast made the day before", "Miss, or range ahead"], rows))
    parts.append("<h3>Hour of day (difference from the daily average)</h3>")
    parts.append(table(["Hour (Central)", "Difference"],
                       [[f"{h:02d}:00", show(v, True)] for h, v in r["hour_of_day"].items()]))
    return parts


def render(results):
    body = [part for source, r in results.items() for part in source_section(source, r)]
    body.append("<h2>Method and limits</h2>")
    body.append(notes([
        "A day's value is the average of its quarter-hour counts in Memphis time. Only complete days "
        "count: strictly between the first and last observed dates, with at least 24 of 96 observations.",
        "The weekday difference is the average gap between a day and the mean of the seven days "
        "centered on it, over every fully observed window. The dashboard rule takes the latest "
        "complete day, removes its weekday difference, and adds the target day's.",
        "Each rule is scored on past data using only the days up to each forecast origin, so the "
        "misses are what the rule would actually have made. A miss is forecast minus actual.",
        "No rule has a trend term; all of them lag a sustained rise or fall. Collection began "
        "September 19, 2026, so the weekday pattern rests on a few weeks of data.",
    ]))
    first = min(r["first_day"] for r in results.values() if r["first_day"])
    last = max(r["last_day"] for r in results.values() if r["last_day"])
    lede = (f"Daily averages from {first} to {last}, with the weekly cycle and a backtest of "
            "simple forecast rules.")
    return document("Population Time Series", "Population time series and forecast", lede,
                    "".join(body))


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data-dir", type=Path, required=True, help="Local archive copy")
    parser.add_argument("--output", type=Path, required=True, help="Output directory")
    args = parser.parse_args()
    if not (args.data_dir / "private").is_dir():
        parser.error(f"{args.data_dir} does not look like an archive copy")
    store = LocalStore(args.data_dir)
    results = {source: analyze(population_points(store, source)) for source in NAMES}
    if not any(r["complete_days"] for r in results.values()):
        parser.error("The archive has no complete day of population observations")
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "summary.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    (args.output / "report.html").write_text(render(results), encoding="utf-8")
    days = ", ".join(f"{s} {r['complete_days']} days" for s, r in results.items())
    print(f"Analyzed {days}; wrote {args.output}")


if __name__ == "__main__":
    main()
