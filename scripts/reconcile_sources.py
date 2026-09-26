"""Reconcile the IML roster with the XFER jail report (JSON and HTML) from a local archive copy.

    python scripts/reconcile_sources.py --data-dir data/snapshots/current --output DIR

Each XFER workbook version is matched to the nearest IML roster observation and the two
booking lists are compared by exact booking number. Counts from 1 to 9 are shown as
"<10" in the HTML report; summary.json is private.
"""

import argparse
import html
import json
from pathlib import Path

from sc_jail.exporters import export_details
from sc_jail.iml import CHICAGO
from sc_jail.profile import suppress
from sc_jail.reconcile import by_day, reconcile
from sc_jail.report_html import document, fmt, notes, pct, table, tiles
from sc_jail.storage import LocalStore

FIELD_TITLES = {
    "book_date": "XFER book date versus IML commitment date",
    "case_numbers": "Case numbers",
    "detainer": "Detainer",
    "next_court": "Earliest next court date",
}


def counted(counter):
    total = sum(counter.values())
    return [[label, suppress(n), pct(n, total) if n >= 10 else "–"]
            for label, n in sorted(counter.items(), key=lambda item: -item[1])]


def render(result):
    latest, agreement = result["latest"], result["latest_field_agreement"]
    shown = [
        ("XFER bookings", latest["xfer_bookings"]),
        ("IML bookings held", latest["iml_held"]),
        ("Listed by both", latest["both"]),
        ("IML-held not in XFER", latest["iml_held_not_in_xfer"]),
        ("XFER not on IML roster", latest["xfer_not_on_roster"]),
    ]
    tile_html = tiles([(label, f"{fmt(suppress(value))}") for label, value in shown])
    day_rows = [[d["day"], d["versions"]] + [fmt(suppress(round(d[f]))) for f in (
        "xfer_bookings", "iml_held", "both", "iml_held_not_in_xfer", "xfer_not_on_roster",
        "xfer_listed_iml_released")] for d in result["by_day"]]
    field_html = "".join(
        f"<h3>{html.escape(FIELD_TITLES[key])}</h3>"
        + table(["Comparison", "Bookings", "Share"], counted(agreement[key]))
        for key in FIELD_TITLES
    )
    unaligned = len(result["unaligned_versions"])
    differences = result["latest_differences"]
    xfer_only, iml_only = differences["xfer_only"], differences["iml_only"]
    difference_html = (
        f"<p>XFER lists {fmt(suppress(latest['xfer_not_on_roster']))} bookings the IML roster does not "
        "show at all. By the committing authority on their workbook rows, how long ago they were "
        "booked, and whether a detainer is marked:</p>"
        + table(["Committing authority", "Bookings", "Share"], counted(xfer_only["committing_authority"]))
        + table(["Time since booking", "Bookings", "Share"], counted(xfer_only["book_date_age"]))
        + table(["Detainer", "Bookings", "Share"], counted(xfer_only["detainer"]))
        + f"<p>IML lists {fmt(suppress(latest['iml_held_not_in_xfer']))} held bookings the workbook "
        "does not include. By the current location on their IML record pages:</p>"
        + table(["Current location", "Bookings", "Share"], counted(iml_only["current_location"]))
    )
    body = f"""{tile_html}
<p>The latest workbook was generated at {html.escape(latest['source_updated_at'][:16])} UTC and is compared
with the IML roster observed at {html.escape(latest['iml_observed_at'][:16])} UTC,
{latest['offset_minutes']:,.1f} minutes apart. Of the IML-held bookings missing from XFER,
{fmt(suppress(latest['iml_held_not_in_xfer_recent']))} were first listed by IML within the two hours
before the workbook, so they may not have reached it yet. Of the XFER bookings not on the IML roster,
{fmt(suppress(latest['xfer_not_on_roster_seen_before']))} had been listed by IML earlier.
XFER also lists {fmt(suppress(latest['xfer_listed_iml_released']))} bookings that IML shows with a past
or current release date.</p>
<h2>By day</h2>
<p>Medians across the workbook versions generated each Central day ({result['aligned_versions']:,} of
{result['xfer_versions']:,} versions had a roster observation within {result['max_align_minutes']}
minutes{'' if not unaligned else f'; {unaligned:,} did not and are left out'}).</p>
{table(["Central date", "Versions", "XFER bookings", "IML held", "Both", "IML held, not in XFER",
        "XFER, not on roster", "XFER, IML released"], day_rows)}
<h2>Bookings only one source lists</h2>
{difference_html}
<h2>Do the shared fields agree?</h2>
<p>For the {fmt(suppress(agreement['bookings_compared']))} bookings both sources list in the latest
comparison, each published field is compared using exact booking and case numbers. IML record pages
are refreshed about daily, so some differences are timing rather than disagreement.</p>
{field_html}
<h2>Method and limits</h2>
{notes([
    "XFER is the Sheriff's jail workbook, published about every two hours with one row per charge. "
    "IML is the public roster searched every 15 minutes. Both are compared by exact booking number.",
    "IML counts a booking as held when its listed release date is blank or after that moment's "
    "Central date, the same rule as the collector's population. IML's roster also lists recently "
    "released bookings, which are not counted as held.",
    "The population chart's IML count is distinct people; these comparisons count bookings.",
    "A workbook's own timestamp is used for alignment, not the time it was downloaded.",
    "Names, dates of birth, and addresses are not read or compared.",
])}"""
    lede = ("Whether the two public sources list the same bookings as held, and whether "
            "the fields they share agree.")
    return document("Source Reconciliation", "IML roster and XFER jail report", lede, body)


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data-dir", type=Path, required=True, help="Local archive copy")
    parser.add_argument("--output", type=Path, required=True, help="Output directory")
    args = parser.parse_args()
    if not (args.data_dir / "private").is_dir():
        parser.error(f"{args.data_dir} does not look like an archive copy")
    store = LocalStore(args.data_dir)
    result = reconcile(store, CHICAGO, list(export_details(store)))
    result["by_day"] = by_day(result["pairs"], CHICAGO)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "summary.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    (args.output / "report.html").write_text(render(result), encoding="utf-8")
    latest = result["latest"]
    print(f"Compared {result['aligned_versions']} of {result['xfer_versions']} XFER versions; latest: "
          f"{latest['xfer_bookings']:,} XFER bookings, {latest['iml_held']:,} IML held, "
          f"{latest['both']:,} in both; wrote {args.output}")


if __name__ == "__main__":
    main()
