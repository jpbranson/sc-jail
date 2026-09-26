"""Compare saved population profiles week over week (JSON and HTML).

    python scripts/analysis_trends.py --weekly-root data/analysis/weekly \
        --baseline data/analysis/baseline/summary.json --output data/analysis/trends

Reads <weekly-root>/<YYYY-MM-DD>/profile/summary.json from completed weekly runs, plus
--current and --baseline summaries when given. Only aggregate summaries are read.
"""

import argparse
import html
import json
from pathlib import Path

from sc_jail.profile import suppress
from sc_jail.report_html import document, notes, table
from sc_jail.trends import compare, load
from sc_jail.weekly import dated_runs

SHOWN = 8


def show(value, kind):
    if value is None:
        return "–"
    if kind == "count":
        return f"{suppress(value):,}" if isinstance(suppress(value), int) else suppress(value)
    if kind == "share":
        return f"{value:.1%}"
    if kind == "days":
        return f"{value:,.0f}"
    if kind == "money":
        return f"${value:,.0f}"
    return f"{value:,.1f}"


def show_change(before, after, delta, kind):
    if delta is None:
        return "–"
    if kind == "count" and any(isinstance(suppress(v), str) for v in (before, after)):
        return "–"
    if kind == "share":
        return f"{delta * 100:+.1f} pts"
    if kind == "money":
        return f"{'+' if delta >= 0 else '−'}${abs(delta):,.0f}"
    if kind in ("days", "count"):
        return f"{delta:+,.0f}"
    return f"{delta:+,.1f}"


def render(result):
    points = result["points"][-SHOWN:]
    headers = ["Measure"] + [p["as_of"] for p in points] + ["Change"]
    rows = []
    for metric in result["metrics"]:
        key, kind = metric["key"], metric["kind"]
        values = [p["metrics"].get(key) for p in points]
        before = values[-2] if len(values) >= 2 else None
        change = show_change(before, values[-1], result["change_since_previous"].get(key), kind)
        rows.append([metric["label"]] + [show(v, kind) for v in values] + [change])
    first, last = result["points"][0]["as_of"], result["points"][-1]["as_of"]
    observed = ", ".join(f"{p['as_of']} at {html.escape(str(p['roster_observed_at']))} UTC"
                         for p in points)
    body = table(headers, rows) + "<h2>Method and limits</h2>" + notes([
        "Each column is the people listed as held on that roster date, using the population "
        "profile's definitions. A held population over-represents long stays; it is not a "
        "measure of everyone booked in a week.",
        f"Rosters used: {observed}. Rosters from different times of day can differ because "
        "releases and bookings are processed unevenly through the day.",
        "Daily rates average booking numbers first seen and listed release dates over the "
        "complete Central days in the week before each roster date; early runs have fewer days.",
        "Change compares the two most recent columns. Shares change in percentage points. "
        "Changes involving a count from 1 to 9 are not shown.",
        "Charge grades, bond types, and statuses are published by the Sheriff and can lag court "
        "records. Collection began September 19, 2026, so early weeks describe a short period.",
    ])
    lede = (f"{len(result['points'])} roster dates from {first} to {last}. "
            "Aggregate counts from the weekly population profiles.")
    return document("Composition Trends", "Held population, week over week", lede, body)


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--weekly-root", type=Path, required=True)
    parser.add_argument("--current", type=Path, help="Profile summary from an unfinished run")
    parser.add_argument("--baseline", type=Path, help="An earlier profile summary to include")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    paths = [run / "profile" / "summary.json" for run in dated_runs(args.weekly_root)]
    paths = [p for p in paths if p.exists()]
    paths += [p for p in (args.baseline, args.current) if p and p.exists()]
    if not paths:
        parser.error("No profile summaries found")
    result = compare(load(paths))
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "summary.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    (args.output / "report.html").write_text(render(result), encoding="utf-8")
    dates = [p["as_of"] for p in result["points"]]
    print(f"Compared {len(dates)} profile dates ({', '.join(dates)}); wrote {args.output}")


if __name__ == "__main__":
    main()
