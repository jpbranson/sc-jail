"""Money bond and pretrial detention (JSON and HTML), from a validated booking panel.

    python scripts/bond_analysis.py --panel data/analysis/panel --output DIR

Finds bond changes in dated record-page versions, measures time from each change to
release, and describes how long people with low money bonds wait. The panel must come
from scripts/build_panel.py with no population mismatches. Counts from 1 to 9 are shown
as "<10" in the HTML report; summary.json is private.
"""

import argparse
import json
from pathlib import Path

from sc_jail.bonds import EVENT_ORDER, LOW_BONDS, analyze
from sc_jail.iml import CHICAGO
from sc_jail.profile import suppress
from sc_jail.report_html import days_text, document, fmt, notes, notice, share_text, table, tiles


def load_panel(folder):
    summary = json.loads((folder / "summary.json").read_text(encoding="utf-8"))
    if summary.get("population_mismatches"):
        raise SystemExit(f"{folder} failed its population check; refusing to analyze it")
    with (folder / "bookings.jsonl").open(encoding="utf-8") as stream:
        return summary, [json.loads(line) for line in stream]


def km_cells(result):
    """Median and share released within 1, 3, and 7 days, from a survival summary."""
    if result is None or result["n"] < 10:
        return ["–"] * 4

    def released(day):
        held = result["at"][day]["still_held"]
        return "–" if held is None else share_text(1 - held)

    return [days_text(result["median"]), released("1"), released("3"), released("7")]


def render(result):
    preliminary = "" if result["readout_ready"] else notice(
        f"<strong>Preliminary.</strong> Collection began {result['coverage_start'][:10]}, so bond "
        f"changes have at most {result['followup_days']} days of follow-up. The first readout needs about "
        f"{result['readout_days']} days (four to six weeks of collection).")
    changes = result["changes"]
    change_rows = []
    for kind in EVENT_ORDER:
        entry = changes[kind]
        followed = entry["time_to_release"]
        change_rows.append([kind, suppress(entry["bookings"]), suppress(entry["seen_after_release"]),
                            suppress(followed["events"]) if followed else 0] + km_cells(followed))
    stock_rows = []
    for limit in LOW_BONDS:
        entry = result["low_bond_held_now"][str(limit)]
        people = entry["people"]
        small = people < 10
        stock_rows.append([f"${limit:,} or less", suppress(people),
                           "–" if small or entry["median_days_held"] is None
                           else f"{entry['median_days_held']:,} days",
                           "–" if small else suppress(entry["held_over_30_days"]),
                           "–" if small else suppress(entry["held_over_90_days"])])
    flow_rows = []
    for limit in LOW_BONDS:
        entry = result["low_bond_new_bookings"][str(limit)]
        flow_rows.append([f"${limit:,} or less", suppress(entry["n"]) if entry else 0,
                          suppress(entry["events"]) if entry else 0] + km_cells(entry))
    held_5000 = result["low_bond_held_now"]["5000"]["people"]
    reduction = result["median_reduction_share"]
    tile_html = tiles([
        ("Bookings with a bond change", f"{result['bookings_with_changes']:,}"),
        ("Bond totals reduced", f"{fmt(suppress(changes['Bond total reduced']['bookings']))}"),
        ("New court-assessed bonds", f"{fmt(suppress(changes['New court-assessed bond']['bookings']))}"),
        ("Held now on money bond alone of $5,000 or less", f"{fmt(suppress(held_5000))}"),
    ])
    body = f"""{preliminary}{tile_html}
<h2>Bond changes and what followed</h2>
<p>Each booking's first change of each kind, found by comparing its record pages over time.
{'A reduction cut the total by a median of ' + share_text(reduction) + '.' if reduction is not None else ''}
Changes seen only after the listed release date are counted but not followed.</p>
<div class="panel">{table(["Change", "Bookings", "Seen after release", "Released since",
                           "Median time to release", "Released within 1 day", "Within 3 days",
                           "Within 7 days"], change_rows)}</div>
<h2>People held now on low money bonds</h2>
<p>People on the latest roster whose record shows only open cases with a court-assessed money
bond, no detainer, and no violation charge, at or below each amount. Nothing else in their record
explains why they are held. Time held runs from the commitment date. The rows are cumulative.</p>
<div class="panel">{table(["Total bond", "People", "Median time held so far", "Held over 30 days",
                           "Held over 90 days"], stock_rows)}</div>
<h2>New bookings with low money bonds</h2>
<p>Bookings that began during collection whose first complete record showed a money bond alone at
or below each amount, followed from the day the bond was seen until release.</p>
<div class="panel">{table(["Total bond", "Bookings", "Released", "Median wait", "Released within 1 day",
                           "Within 3 days", "Within 7 days"], flow_rows)}</div>
<h2>Method and limits</h2>
{notes([
    "Bond changes compare consecutive versions of a booking's record page that list case entries. "
    "Record pages refresh about daily, so a change is dated when it was seen, up to about a day after "
    "it was made.",
    "A new court-assessed bond is the first appearance of that bond type (for example after a bond "
    "was not assessed or not set). Reductions and increases compare the Sheriff's listed grand total. "
    "Recognizance entered is the first appearance of release on recognizance.",
    "Time to release runs in whole days from the date a change was seen to the listed release date, "
    "with Kaplan-Meier estimates; people still held are censored at the latest roster.",
    "Bond status is not a court outcome. No disposition is inferred from a paid, sentenced, or "
    "recognizance status; the county's dispositions folder is empty.",
    "Money bond alone uses the population profile's definition, and amounts are the listed grand total.",
])}"""
    lede = ("How money bonds change while people are held, and how long people with low bonds wait, "
            "from the Sheriff's record pages.")
    return document("Money Bond", "Money bond and pretrial detention", lede, body)


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
    counts = {kind: entry["bookings"] for kind, entry in result["changes"].items()}
    print(f"Bond changes by kind: {counts}; held now on money bond alone <= $5,000: "
          f"{result['low_bond_held_now']['5000']['people']}; "
          f"readout {'ready' if result['readout_ready'] else 'not ready'}; wrote {args.output}")


if __name__ == "__main__":
    main()
