"""Link court reports to jail bookings by exact booking and case numbers (JSON and HTML).

    python scripts/court_linkage.py --data-dir data/snapshots/current --panel data/analysis/panel --output DIR

Reads every archived court-report version from the local archive copy and the validated
booking panel. Never joins by name. Counts from 1 to 9 are shown as "<10" in the HTML
report; summary.json is private.
"""

import argparse
import json
from pathlib import Path

from sc_jail.exporters import export_details
from sc_jail.iml import CHICAGO
from sc_jail.linkage import CHANGE_KINDS, PASSED, RESET, analyze, case_statuses, load_courts
from sc_jail.profile import suppress
from sc_jail.report_html import document, fmt, notes, notice, pct, table, tiles
from sc_jail.storage import LocalStore

FAMILY_TITLES = {
    "criminal_calendar": "Criminal Court calendars",
    "gs_calendar": "General Sessions calendars",
    "indictments": "Daily indictment lists",
}


def load_panel(folder):
    summary = json.loads((folder / "summary.json").read_text(encoding="utf-8"))
    if summary.get("population_mismatches"):
        raise SystemExit(f"{folder} failed its population check; refusing to analyze it")
    with (folder / "bookings.jsonl").open(encoding="utf-8") as stream:
        return summary, [json.loads(line) for line in stream]


def share(part, whole):
    return pct(part, whole) if part >= 10 and whole else "–"


def render(result):
    rates, dates, indictments = result["match_rates"], result["court_dates"], result["indictments"]
    pending = rates["pending_hearings"]
    preliminary = "" if result["readout_ready"] else notice(
        "<strong>Match rates are ready; the rest is preliminary.</strong> Court-date resets and time to "
        f"indictment need about {result['readout_days']} days of collection (four to eight weeks); "
        f"collection began {result['coverage_start'][:10]}, {result['followup_days']} days before the "
        "latest roster.")
    tile_html = tiles([
        ("Held bookings in the latest pending-hearings report",
         share(pending["held_bookings_listed"], pending["held_bookings"])),
        ("Pending-hearing rows matching a jail booking",
         share(pending["rows_matching_a_booking"], pending["rows_with_booking_number"])),
        ("Held bookings with a case on a Criminal Court calendar",
         share(rates["criminal_calendar"]["held_bookings_with_a_listed_case"], pending["held_bookings"])),
        ("Court dates passed with a new date set", fmt(suppress(dates["changes"][PASSED]))),
    ])
    pending_rows = [
        ["Rows in the latest report", fmt(pending["rows"]), ""],
        ["Rows with a booking number", fmt(suppress(pending["rows_with_booking_number"])),
         share(pending["rows_with_booking_number"], pending["rows"])],
        ["Rows whose booking number IML listed during collection",
         fmt(suppress(pending["rows_matching_a_booking"])),
         share(pending["rows_matching_a_booking"], pending["rows_with_booking_number"])],
        ["Matched rows whose case number is on that booking's record",
         fmt(suppress(pending["matched_rows_with_that_case_on_the_booking"])),
         share(pending["matched_rows_with_that_case_on_the_booking"], pending["rows_matching_a_booking"])],
        ["Bookings held at the latest roster that the report lists",
         fmt(suppress(pending["held_bookings_listed"])),
         share(pending["held_bookings_listed"], pending["held_bookings"])],
    ]
    family_rows = []
    for family, title in FAMILY_TITLES.items():
        entry = rates[family]
        family_rows.append([title, entry["report_versions"], fmt(suppress(entry["distinct_cases"])),
                            fmt(suppress(entry["cases_matching_a_booking"])),
                            share(entry["cases_matching_a_booking"], entry["distinct_cases"]),
                            fmt(suppress(entry["held_bookings_with_a_listed_case"])),
                            share(entry["held_bookings_with_a_listed_case"], pending["held_bookings"])])
    change_rows = [[kind, fmt(suppress(dates["changes"][kind]))] for kind in CHANGE_KINDS]
    passed_rows = [[f"{label} date{'s' if label != '1' else ''} passed", fmt(suppress(count))]
                   for label, count in dates["bookings_by_dates_passed"].items()]
    to_next = dates["median_days_to_next_date"]
    to_next_text = (f"When a listed date passed and the booking stayed on the roster, the next date was "
                    f"set a median of {to_next:,} days later."
                    if to_next is not None and dates["changes"][PASSED] >= 10 else "")
    moved = dates["median_days_reset_moved"]
    reset_text = (f"Resets seen before the hearing date moved it a median of {moved:,} days."
                  if moved is not None and dates["changes"][RESET] >= 10 else
                  "Too few resets were seen before the hearing date to describe them.")
    timing_rows = []
    for group, label in (("new", "Booked during collection"),
                         ("present_at_start", "Already held when collection began")):
        for key, subset in (("indicted_during_stay", "all"),
                            ("indicted_during_stay_case_open", "indicted case open")):
            entry = indictments[key][group]
            small = entry["bookings"] < 10
            timing_rows.append([f"{label} ({subset})", fmt(suppress(entry["bookings"])),
                                "–" if small else f"{entry['median_days']:,} days",
                                "–" if small else f"{entry['quartile_1']:,}–{entry['quartile_3']:,} days"])
    status_rows = [[label, fmt(suppress(count))]
                   for label, count in sorted(indictments["indicted_case_status"].items(),
                                              key=lambda item: -item[1])]
    no_sentenced = sum(indictments["matched_with_no_case_sentenced"].values())
    before = sum(indictments["indicted_before_booking"].values())
    lower = rates["lowercase_case_prefixes"]
    body = f"""{preliminary}{tile_html}
<h2>Pending hearings, by booking number</h2>
<p>The pending-hearings report modified {pending['report_modified_at'][:16] if pending['report_modified_at'] else '–'}
UTC, compared with the booking panel and the latest roster ({pending['held_bookings']:,} bookings held).</p>
<div class="panel">{table(["Measure", "Count", "Share"], pending_rows)}</div>
<h2>Calendars and indictments, by case number</h2>
<p>Every archived version of each report, compared with the case numbers on IML record pages.
Calendars include people who are not in jail, so most calendar cases are not expected to match.</p>
<div class="panel">{table(["Report", "Versions", "Distinct cases", "Cases on a jail record", "Share",
                           "Held bookings with a listed case", "Share of held"], family_rows)}</div>
<p>{fmt(suppress(lower['iml_case_numbers']))} IML case numbers begin with a lowercase letter;
{fmt(suppress(lower['match_only_if_uppercased']))} of them would match a court report only if the letter were
uppercased. Matches here use exact strings.</p>
<h2>Changes in the next court date</h2>
<p>Changes in each booking's earliest listed court date between versions of its record page. Record
pages refresh about daily, so a continuance granted in court usually appears as a passed date followed
by a new one; the record does not say whether the hearing was held, continued, or reset. {to_next_text}
{reset_text}</p>
<div class="panel">{table(["Change", "Changes"], change_rows)}</div>
<div class="panel">{table(["Bookings whose listed court date passed while held", "Bookings"],
                          passed_rows)}</div>
<h2>Time from commitment to indictment</h2>
<p>Bookings with a case number that appears on a daily indictment list collected since
{result['coverage_start'][:10]}. Indictments before collection began are not observed, so people
already held when collection began are shown separately and over-represent long waits.</p>
<div class="panel">{table(["Group", "Bookings indicted during the stay", "Median time from commitment",
                           "Middle half"], timing_rows)}</div>
<p>Status of the indicted case on the latest record page. The plan's test (no case marked sentenced
on the whole record) matches {fmt(suppress(no_sentenced))} of these bookings, because most also have
General Sessions entries marked sentenced; the indicted case itself is usually open. See the
source-quality log. {fmt(suppress(before))} bookings were indicted before their commitment date.</p>
<div class="panel">{table(["Indicted case", "Bookings"], status_rows)}</div>
<h2>Method and limits</h2>
{notes([
    "Joins use exact booking numbers (pending hearings) and exact case numbers (calendars and "
    "indictments). Names are never used, and no fuzzy matching is attempted.",
    "A reset before the hearing date means the earliest court date moved later while that date was still "
    "in the future when the change was seen. A passed date with a new date set means the listed date "
    "arrived and a later one replaced it while the booking stayed listed.",
    "The county publishes no dispositions, so outcomes are not measured, and bond status is not "
    "treated as an outcome.",
    "Case status comes from the Sheriff's bond entries on the latest complete record page.",
])}"""
    lede = ("How the county's criminal court reports connect to people in jail, using exact booking "
            "and case numbers.")
    return document("Court Linkage", "Court reports and jail bookings", lede, body)


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data-dir", type=Path, required=True, help="Local archive copy")
    parser.add_argument("--panel", type=Path, required=True, help="Folder from build_panel.py")
    parser.add_argument("--output", type=Path, required=True, help="Output directory")
    args = parser.parse_args()
    if not (args.data_dir / "private").is_dir():
        parser.error(f"{args.data_dir} does not look like an archive copy")
    summary, bookings = load_panel(args.panel)
    store = LocalStore(args.data_dir)
    courts = load_courts(store)
    result = analyze(bookings, courts, summary["coverage"], CHICAGO,
                     case_statuses(export_details(store)))
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "summary.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    (args.output / "report.html").write_text(render(result), encoding="utf-8")
    pending = result["match_rates"]["pending_hearings"]
    print(f"Pending hearings list {pending['held_bookings_listed']:,} of {pending['held_bookings']:,} "
          f"held bookings; readout {'ready' if result['readout_ready'] else 'not ready'}; "
          f"wrote {args.output}")


if __name__ == "__main__":
    main()
