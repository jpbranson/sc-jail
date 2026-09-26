"""Re-booking after release (JSON and HTML), from a validated booking panel.

    python scripts/rebooking.py --panel data/analysis/panel --output DIR

Follows each release listed during collection until the same permanent person ID is
booked again or the latest roster. The plan's readout needs about 90 days of collection.
Counts from 1 to 9 are shown as "<10" in the HTML report; summary.json is private.
"""

import argparse
import json
from pathlib import Path

from sc_jail.iml import CHICAGO
from sc_jail.profile import suppress
from sc_jail.rebooking import DAYS, analyze
from sc_jail.report_html import days_text, document, fmt, notes, notice, share_text, table, tiles


def load_panel(folder):
    summary = json.loads((folder / "summary.json").read_text(encoding="utf-8"))
    if summary.get("population_mismatches"):
        raise SystemExit(f"{folder} failed its population check; refusing to analyze it")
    with (folder / "bookings.jsonl").open(encoding="utf-8") as stream:
        return summary, [json.loads(line) for line in stream]


def render(result):
    followed = result["rebooking"]
    preliminary = "" if result["readout_ready"] else notice(
        f"<strong>Preliminary.</strong> Collection began {result['coverage_start'][:10]}; releases have at "
        f"most {result['followup_days']} days of follow-up. The plan's readout needs about "
        f"{result['readout_days']} days of collection, and shares at 30, 60, or 90 days appear only once "
        "releases have been followed that long.")
    rows = []
    for day in DAYS:
        point = followed["at"][str(day)] if followed else None
        held = point["still_held"] if point else None
        rows.append([f"Within {day} days", "–" if held is None else share_text(1 - held),
                     "–" if held is None or point["lower"] is None else
                     f"{share_text(1 - point['upper'])}–{share_text(1 - point['lower'])}",
                     "–" if held is None else fmt(point["at_risk"])])
    tile_html = tiles([
        ("Releases followed", f"{followed['n']:,}" if followed else "0"),
        ("Booked again so far", fmt(suppress(followed["events"])) if followed else "0"),
        ("Median time to re-booking", days_text(followed["median"]) if followed else "–"),
        ("Booked again within 7 days",
         share_text(1 - followed["at"]["7"]["still_held"])
         if followed and followed["at"]["7"]["still_held"] is not None else "–"),
    ])
    body = f"""{preliminary}{tile_html}
<h2>Share booked again, by days since release</h2>
<div class="panel">{table(["Period", "Booked again", "95% interval", "Releases still followed"], rows)}</div>
<h2>Method and limits</h2>
{notes([
    f"Each release listed from {result['coverage_start'][:10]} through the latest roster starts a clock "
    f"({result['releases_during_collection']:,} releases). The event is the first later booking with the "
    "same IML permanent person ID, dated by the day the roster first listed it.",
    f"{fmt(suppress(result['excluded_reassigned_ids']))} releases were left out because the person's "
    "permanent ID was reassigned between bookings, so their bookings cannot be linked safely.",
    "Kaplan-Meier estimates; releases not followed by a new booking are censored at the latest roster. "
    f"{fmt(suppress(result['same_day']))} new bookings were first listed on the release day itself; some "
    "may be administrative (a new booking number rather than a new arrest).",
    "Only bookings into this jail during collection are seen. Arrests elsewhere, citations without "
    "booking, and anything during collection outages that never reached the roster are not counted. "
    "This is not a recidivism rate and says nothing about guilt.",
])}"""
    lede = "How soon people released from the jail are booked into it again, from the Sheriff's roster."
    return document("Re-booking", "Re-booking after release", lede, body)


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
    followed = result["rebooking"]
    print(f"Followed {followed['n'] if followed else 0:,} releases "
          f"({followed['events'] if followed else 0:,} booked again); "
          f"readout {'ready' if result['readout_ready'] else 'not ready'}; wrote {args.output}")


if __name__ == "__main__":
    main()
