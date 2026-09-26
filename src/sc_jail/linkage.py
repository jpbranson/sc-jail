"""Court reports linked to jail bookings by exact identifiers only.

Pending-hearing rows carry a booking number; calendars and indictments carry case
numbers, which IML record pages list for each charge. Joins compare exact strings and
never use names. Calendars also list people who are not in jail, so only a minority of
calendar cases are expected to match. Dispositions are not published, so no case outcome
is inferred here.
"""

from collections import Counter, defaultdict
from datetime import date

from .bonds import held_at_snapshot, latest_complete
from .exporters import export_courts
from .profile import parse_date
from .stays import local_date

READOUT_DAYS = 28
PRETRIAL = "No case marked sentenced"


def load_courts(store):
    """Identifier fields from every archived court-report row, by report family."""
    rows = defaultdict(list)
    for item in export_courts(store, all_versions=True):
        record = item.get("record")
        if record is None:  # an unsupported file appears only as an inventory row
            continue
        rows[item["report"]["family"]].append({
            "report": item["report"]["name"],
            "modified_at": item["report"]["modified_at"],
            "case": record.get("Case Number") or "",
            "booking": record.get("Booking Nbr") or "",
            "indicted": record.get("IndictmentDate") or "",
        })
    return rows


def latest_report(rows):
    """Rows of the most recently modified report version in one family."""
    if not rows:
        return None, []
    newest = max((r["modified_at"], r["report"]) for r in rows)
    return newest, [r for r in rows if (r["modified_at"], r["report"]) == newest]


def booking_cases(booking):
    return {case for version in booking["details"] for case in version["cases"]}


def match_rates(bookings, courts, snapshot_date):
    by_number = {b["booking_number"]: b for b in bookings}
    held = {b["booking_number"] for b in bookings if held_at_snapshot(b, snapshot_date)}
    case_bookings = defaultdict(set)
    for booking in bookings:
        for case in booking_cases(booking):
            case_bookings[case].add(booking["booking_number"])
    newest, pending = latest_report(courts.get("pending_hearings", []))
    with_booking = [r for r in pending if r["booking"]]
    matched = [r for r in with_booking if r["booking"] in by_number]
    result = {"pending_hearings": {
        "report_modified_at": newest[0] if newest else None,
        "rows": len(pending),
        "rows_with_booking_number": len(with_booking),
        "rows_matching_a_booking": len(matched),
        "matched_rows_with_that_case_on_the_booking": sum(
            r["case"] in booking_cases(by_number[r["booking"]]) for r in matched),
        "held_bookings": len(held),
        "held_bookings_listed": len({r["booking"] for r in pending} & held),
    }}
    court_cases = set()
    for family in ("criminal_calendar", "gs_calendar", "indictments"):
        rows = courts.get(family, [])
        cases = {r["case"] for r in rows if r["case"]}
        court_cases |= cases
        matched_cases = cases & case_bookings.keys()
        listed_held = {b for case in matched_cases for b in case_bookings[case]} & held
        result[family] = {
            "report_versions": len({(r["modified_at"], r["report"]) for r in rows}),
            "rows": len(rows),
            "distinct_cases": len(cases),
            "cases_matching_a_booking": len(matched_cases),
            "held_bookings_with_a_listed_case": len(listed_held),
        }
    court_cases |= {r["case"] for r in pending if r["case"]}
    lowercase = [c for c in case_bookings if c[:1].islower()]
    result["lowercase_case_prefixes"] = {
        "iml_case_numbers": len(lowercase),
        "match_only_if_uppercased": sum(c not in court_cases and c.upper() in court_cases
                                        for c in lowercase),
    }
    return result


RESET = "Reset before the hearing date"
PASSED = "Hearing date passed; next date set"
CHANGE_KINDS = [PASSED, RESET, "Moved earlier", "First date listed", "No date listed any more"]


def court_date_changes(bookings, zone):
    """Classify changes in each booking's earliest listed court date between record versions.

    Record pages refresh about daily, so most continuances granted in court appear as a
    passed date followed by a new one; only changes seen while the old date was still in
    the future can be called resets before the hearing.
    """
    kinds, moved, next_after, passed_per_booking = Counter(), [], [], Counter()
    for booking in bookings:
        passed, previous = 0, None
        for version in booking["details"]:
            if previous is not None and version["next_court"] != previous["next_court"]:
                old, new = previous["next_court"], version["next_court"]
                seen = local_date(version["at"], zone)
                if old and new:
                    before, after = date.fromisoformat(old), date.fromisoformat(new)
                    if after > before and before > seen:
                        kinds[RESET] += 1
                        moved.append((after - before).days)
                    elif after > before:
                        kinds[PASSED] += 1
                        next_after.append((after - before).days)
                        passed += 1
                    else:
                        kinds["Moved earlier"] += 1
                elif new:
                    kinds["First date listed"] += 1
                else:
                    kinds["No date listed any more"] += 1
            previous = version
        if passed:
            passed_per_booking[min(passed, 3)] += 1
    moved.sort()
    next_after.sort()
    return {
        "changes": {kind: kinds[kind] for kind in CHANGE_KINDS},
        "median_days_reset_moved": moved[len(moved) // 2] if moved else None,
        "median_days_to_next_date": next_after[len(next_after) // 2] if next_after else None,
        "bookings_by_dates_passed": {"1": passed_per_booking[1], "2": passed_per_booking[2],
                                     "3 or more": passed_per_booking[3]},
    }


def indicted_case_status(statuses):
    """Summarize the Sheriff's bond-entry status for the indicted case(s) of one booking."""
    if not statuses:
        return "Record not current"
    if "Open" in statuses or "No Bond" in statuses:
        return "Indicted case open"
    if statuses == {"Sentenced"}:
        return "Indicted case marked sentenced"
    return "Other or blank status"


def indictment_timing(bookings, courts, case_status=None):
    """Days from commitment to the earliest indictment listing one of the booking's cases.

    ``case_status`` maps booking number to {case number: set of bond-entry statuses} from
    the latest record pages; it separates pretrial indicted cases from others.
    """
    case_status = case_status or {}
    indicted = {}
    for row in courts.get("indictments", []):
        day = parse_date(row["indicted"])
        if row["case"] and day:
            indicted[row["case"]] = min(day, indicted.get(row["case"], day))
    groups = {"new": [], "present_at_start": []}
    open_groups = {"new": [], "present_at_start": []}
    before_booking, pretrial, indicted_status = Counter(), Counter(), Counter()
    for booking in bookings:
        cases = booking_cases(booking) & indicted.keys()
        commitment = next((v["commitment_date"] for v in booking["details"] if v["commitment_date"]),
                          None)
        if not cases or not commitment:
            continue
        days = (min(indicted[c] for c in cases) - date.fromisoformat(commitment)).days
        group = "present_at_start" if booking["left_truncated"] else "new"
        version = latest_complete(booking)
        if version is not None and version["status"] == PRETRIAL:
            pretrial[group] += 1
        statuses = set().union(*(case_status.get(booking["booking_number"], {}).get(c, set())
                                 for c in cases))
        status = indicted_case_status(statuses)
        indicted_status[status] += 1
        if days < 0:
            before_booking[group] += 1  # indicted first, then booked (for example on a capias)
        else:
            groups[group].append(days)
            if status == "Indicted case open":
                open_groups[group].append(days)

    def describe(days):
        ordered = sorted(days)
        if not ordered:
            return {"bookings": 0, "median_days": None, "quartile_1": None, "quartile_3": None}
        return {"bookings": len(ordered), "median_days": ordered[len(ordered) // 2],
                "quartile_1": ordered[len(ordered) // 4], "quartile_3": ordered[3 * len(ordered) // 4]}

    return {
        "indicted_cases_listed": len(indicted),
        "indicted_during_stay": {group: describe(days) for group, days in groups.items()},
        "indicted_during_stay_case_open": {group: describe(days)
                                           for group, days in open_groups.items()},
        "indicted_case_status": dict(indicted_status),
        "indicted_before_booking": dict(before_booking),
        # The plan's pretrial test; compare with indicted_case_status, which is per case.
        "matched_with_no_case_sentenced": dict(pretrial),
    }


def case_statuses(details):
    """{booking: {case: statuses}} from current record pages (for example export_details)."""
    statuses = defaultdict(dict)
    for record in details:
        for bond in record["bonds"]:
            if bond["Case #"]:
                statuses[record["booking_number"]].setdefault(bond["Case #"], set()).add(bond["Status"])
    return statuses


def analyze(bookings, courts, coverage, zone, case_status=None):
    snapshot_date = local_date(coverage["last"], zone)
    followup = (snapshot_date - local_date(coverage["first"], zone)).days
    return {
        "coverage_start": coverage["first"],
        "snapshot": coverage["last"],
        "followup_days": followup,
        "readout_days": READOUT_DAYS,
        "readout_ready": followup >= READOUT_DAYS,
        "match_rates": match_rates(bookings, courts, snapshot_date),
        "court_dates": court_date_changes(bookings, zone),
        "indictments": indictment_timing(bookings, courts, case_status),
    }
