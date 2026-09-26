"""Length of stay for new bookings (Kaplan-Meier), from a validated booking panel.

    python scripts/length_of_stay.py --panel data/analysis/panel --output DIR

The panel must come from scripts/build_panel.py with no population mismatches. Writes a
private summary.json and an aggregate report.html (groups under 10 bookings suppressed).
"""

import argparse
import json
import sys
from pathlib import Path

from sc_jail.iml import CHICAGO
from sc_jail.profile import suppress
from sc_jail.report_html import (
    days_text,
    document,
    fmt,
    notes,
    notice,
    share_text,
    step_chart,
    table,
    tiles,
)
from sc_jail.stays import AMOUNT_BANDS, BOND_ORDER, DETAINER_ORDER, GRADE_ORDER, analyze

DAYS = ("1", "2", "3", "7", "14", "30")
GROUP_TITLES = {
    "grade": ("Most serious charge when the record was complete", GRADE_ORDER),
    "bond": ("Bond situation when first decided", BOND_ORDER),
    "amount": ("Money bond alone when first decided, by amount",
               [label for _, label in AMOUNT_BANDS]),
    "detainer": ("Detainer when the record was complete", DETAINER_ORDER),
}


def load_panel(folder):
    summary = json.loads((folder / "summary.json").read_text(encoding="utf-8"))
    if summary.get("population_mismatches"):
        sys.exit(f"{folder} failed its population check; refusing to analyze it")
    with (folder / "bookings.jsonl").open(encoding="utf-8") as stream:
        bookings = [json.loads(line) for line in stream]
    return summary, bookings


def held_cell(group, day):
    point = group["at"][day]
    if point["still_held"] is None:
        return "–"
    return share_text(point["still_held"])


def interval(point):
    if point["still_held"] is None:
        return "–"
    if point["lower"] is None:
        return share_text(point["still_held"])
    return f"{share_text(point['still_held'])} ({share_text(point['lower'])}–{share_text(point['upper'])})"


def group_rows(groups, order):
    rows = []
    for label in order:
        group = groups.get(label)
        if not group:
            continue
        if group["n"] < 10:
            rows.append([label, suppress(group["n"]), "–", "–", "–", "–", "–"])
            continue
        rows.append([label, group["n"], group["events"], days_text(group["median"])]
                    + [held_cell(group, day) for day in ("1", "3", "7")])
    return rows


def completion_note(completion):
    entered, decided = completion["entered"], completion["bond_decided"]

    def when(stage):
        if stage["median_hours"] is None:
            return "not yet"
        return (f"a median of {stage['median_hours']:,.0f} hours after first listing "
                f"(90% within {stage['ninetieth_percentile_hours']:,.0f} hours)")

    return ("Groups come from the record page once it fills in. Charges and bond entries appeared "
            f"{when(entered)}; charge grade and detainer use that page, and {entered['not_reached']:,} "
            "records had none by the latest roster. A bond decision (any bond type other than "
            f"“Not Assessed”) appeared {when(decided)}; bond groups use that page, and "
            f"{decided['not_reached']:,} bookings had no decision yet. Record pages keep being fetched "
            "while a released booking is still listed. Later bond changes are in the bond analysis.")


def render(result):
    overall = result["overall"]
    horizon = min(overall["longest_followup"] or 1, 30)
    preliminary = "" if result["readout_ready"] else notice(
        f"<strong>Preliminary.</strong> Collection began {result['coverage_start'][:10]}, so the longest "
        f"possible follow-up is {result['followup_days']} days. The first readout needs about "
        f"{result['readout_days']} days; until then, estimates past the first few days rest on few "
        "bookings and the median may not be reached.")
    tile_html = tiles([
        ("New bookings followed", f"{result['cohort']:,}"),
        ("Released so far", f"{overall['events']:,}"),
        ("Median length of stay", days_text(overall["median"])),
        ("Still held after 3 days", share_text(overall["at"]["3"]["still_held"])),
    ])
    overall_rows = [[f"{day} day{'s' if day != '1' else ''}", interval(overall["at"][day]),
                     fmt(overall["at"][day]["at_risk"]) if overall["at"][day]["still_held"] is not None
                     else "–"] for day in DAYS]
    sections = "".join(
        f"<h2>{title}</h2><div class=\"panel\">"
        + table(["Group", "Bookings", "Released", "Median stay", "Held after 1 day",
                 "After 3 days", "After 7 days"], group_rows(result["groups"][key], order))
        + "</div>"
        for key, (title, order) in GROUP_TITLES.items()
    )
    short = result["short_stays"]
    listing = short["listing_after_release_hours"]
    listing_text = (f"Released bookings stayed on the roster a median of {listing['median']:,.0f} hours "
                    f"after their release date appeared (shortest {listing['shortest']:,.1f} hours, "
                    f"{listing['bookings']:,} bookings), so a stay that ends between two 15-minute "
                    "collections is still seen, with its release date."
                    if listing else "No released booking has left the roster yet.")
    excluded = "; ".join(f"{fmt(suppress(n))} {reason.lower()}" for reason, n in result["excluded"].items())
    body = f"""{preliminary}{tile_html}
<h2>Share still held, by days since commitment</h2>
<div class="panel">{step_chart([("All new bookings", overall["curve"])], horizon=horizon)}</div>
<div class="panel">{table(["After", "Still held (95% interval)", "Bookings still followed"], overall_rows)}</div>
{sections}
<h2>Very short stays</h2>
<p>{fmt(suppress(short['release_listed_when_first_seen']))} bookings already had a release date the first time
the roster listed them: their whole stay fell between two collections. {fmt(suppress(short['released_same_day']))}
were released on their commitment date. {listing_text}</p>
<h2>Method and limits</h2>
{notes([
    "Cohort: bookings first listed after the first archived roster (collection began "
    f"{result['coverage_start'][:16]} UTC), so each stay's start is observed. "
    + (f"Excluded: {excluded}." if excluded else "None were excluded."),
    "Time runs from the IML commitment date to the listed release date, in whole days; "
    "a same-day release is 0 days. Bookings still held are censored at the latest roster "
    f"({result['snapshot'][:16]} UTC); a booking that left the roster without a release date is "
    "censored when last seen.",
    "Kaplan-Meier estimates with 95% intervals (Greenwood variance, log-log scale). An estimate is "
    "shown only up to the longest observed follow-up.",
    completion_note(result["record_completion"]),
    "This follows bookings, not people, and describes stays that began during collection. A "
    "held-population snapshot over-represents long stays; this does not.",
])}"""
    lede = ("How long bookings that began during collection stayed in jail, from the Sheriff's roster "
            "and record pages.")
    return document("Length of Stay", "Length of stay for new bookings", lede, body)


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--panel", type=Path, required=True, help="Folder from build_panel.py")
    parser.add_argument("--output", type=Path, required=True, help="Output directory")
    args = parser.parse_args()
    summary, bookings = load_panel(args.panel)
    result = analyze(bookings, summary["coverage"], CHICAGO)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "summary.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    (args.output / "report.html").write_text(render(result), encoding="utf-8")
    overall = result["overall"]
    print(f"Followed {result['cohort']:,} new bookings ({overall['events']:,} released) over "
          f"{result['followup_days']} days; median stay {days_text(overall['median'])}; "
          f"readout {'ready' if result['readout_ready'] else 'not ready'}; wrote {args.output}")


if __name__ == "__main__":
    main()
