from datetime import date
from zoneinfo import ZoneInfo

from sc_jail import linkage
from sc_jail.linkage import (
    case_statuses,
    court_date_changes,
    indictment_timing,
    latest_report,
    match_rates,
)

CHICAGO = ZoneInfo("America/Chicago")
SNAPSHOT = date(2026, 9, 25)


def version(at, *, cases=("C1234567",), court=None, committed="2026-09-21",
            status="No case marked sentenced"):
    return {"at": at, "commitment_date": committed, "status": status, "cases": list(cases),
            "next_court": court, "money_bond_only": False, "no_bond_set": False,
            "bond_total": 0.0, "bond_types": [], "grade": "Class C felony", "detainers": 0}


def booking(number, details, *, held=True, truncated=False):
    return {"booking_number": number, "details": details, "release_date": None if held else "2026-09-22",
            "outcome": "held" if held else "released", "on_latest_roster": held,
            "left_truncated": truncated}


def court(case="", booking_number="", *, report="r1", modified="2026-09-24T10:00:00+00:00",
          indicted=""):
    return {"report": report, "modified_at": modified, "case": case, "booking": booking_number,
            "indicted": indicted}


def test_latest_report_selects_one_version():
    rows = [court("A", report="old", modified="2026-09-20T10:00:00+00:00"), court("B"), court("C")]
    newest, latest = latest_report(rows)
    assert newest[1] == "r1" and [r["case"] for r in latest] == ["B", "C"]


def test_match_rates_use_exact_booking_and_case_numbers():
    bookings = [booking("10000001", [version("t", cases=("C1234567", "23000001"))]),
                booking("10000002", [version("t", cases=("c7654321",))]),
                booking("10000003", [version("t", cases=("C9999999",))], held=False)]
    courts = {
        "pending_hearings": [court("C1234567", "10000001"), court("C5555555", "10000002"),
                             court("C0000000", ""), court("C2222222", "99999999")],
        "gs_calendar": [court("23000001"), court("23000002")],
        "criminal_calendar": [court("C7654321"), court("C9999999")],
        "indictments": [],
    }
    rates = match_rates(bookings, courts, SNAPSHOT)
    pending = rates["pending_hearings"]
    assert (pending["rows"], pending["rows_with_booking_number"], pending["rows_matching_a_booking"]) == (4, 3, 2)
    assert pending["matched_rows_with_that_case_on_the_booking"] == 1
    assert (pending["held_bookings"], pending["held_bookings_listed"]) == (2, 2)
    assert rates["gs_calendar"]["cases_matching_a_booking"] == 1
    # The released booking's case matches, but it is not held; the lowercase case does not match.
    assert rates["criminal_calendar"]["cases_matching_a_booking"] == 1
    assert rates["criminal_calendar"]["held_bookings_with_a_listed_case"] == 0
    assert rates["lowercase_case_prefixes"] == {"iml_case_numbers": 1, "match_only_if_uppercased": 1}


def test_court_date_changes_separate_resets_from_later_hearings():
    details = [version("2026-09-20T15:00:00+00:00", court="2026-09-25"),
               # Moved later on Sept 22, before the Sept 25 date arrived: a reset.
               version("2026-09-22T15:00:00+00:00", court="2026-10-09"),
               # Seen on Oct 9 or later: the next date after the listed hearing.
               version("2026-10-10T15:00:00+00:00", court="2026-11-01"),
               version("2026-10-11T15:00:00+00:00", court=None)]
    result = court_date_changes([booking("1", details)], CHICAGO)
    assert result["changes"] == {"Hearing date passed; next date set": 1,
                                 "Reset before the hearing date": 1, "Moved earlier": 0,
                                 "First date listed": 0, "No date listed any more": 1}
    assert result["median_days_reset_moved"] == 14
    assert result["median_days_to_next_date"] == 23
    assert result["bookings_by_dates_passed"] == {"1": 1, "2": 0, "3 or more": 0}


def test_indictment_timing_splits_new_and_existing_bookings():
    bookings = [booking("1", [version("t", cases=("C1",), committed="2026-09-20")]),
                booking("2", [version("t", cases=("C2",), committed="2026-06-01")], truncated=True),
                booking("3", [version("t", cases=("C3",), committed="2026-09-22")])]
    courts = {"indictments": [court("C1", indicted="09/24/2026"), court("C1", indicted="09/25/2026"),
                              court("C2", indicted="09/23/2026"), court("C3", indicted="09/01/2026")]}
    statuses = case_statuses([
        {"booking_number": "1", "bonds": [{"Case #": "C1", "Status": "Open"},
                                          {"Case #": "20000001", "Status": "Sentenced"}]},
        {"booking_number": "2", "bonds": [{"Case #": "C2", "Status": "Sentenced"}]}])
    result = indictment_timing(bookings, courts, statuses)
    assert result["indicted_case_status"] == {"Indicted case open": 1,
                                              "Indicted case marked sentenced": 1,
                                              "Record not current": 1}
    assert result["indicted_during_stay_case_open"]["new"]["bookings"] == 1
    assert result["indicted_during_stay_case_open"]["present_at_start"]["bookings"] == 0
    assert result["indicted_during_stay"]["new"]["bookings"] == 1
    assert result["indicted_during_stay"]["new"]["median_days"] == 4  # earliest listing wins
    assert result["indicted_during_stay"]["present_at_start"]["median_days"] == 114
    assert result["indicted_before_booking"] == {"new": 1}
    assert result["matched_with_no_case_sentenced"] == {"new": 2, "present_at_start": 1}


def test_load_courts_keeps_identifiers_and_skips_unsupported_files(monkeypatch):
    items = [
        {"report": {"family": "pending_hearings", "name": "p.xls", "modified_at": "m"},
         "record": {"Case Number": "C1", "Booking Nbr": "10000001", "Def Name": "PRIVATE"}},
        {"report": {"family": "indictments", "name": "i.xls", "modified_at": "m"},
         "record": {"Case Number": "C2", "IndictmentDate": "09/24/2026", "Defendant": "PRIVATE"}},
        {"report": {"family": "gs_calendar", "name": "odd.pdf", "modified_at": "m"}, "record": None},
    ]
    monkeypatch.setattr(linkage, "export_courts", lambda store, all_versions: iter(items))
    rows = linkage.load_courts(object())
    assert rows["pending_hearings"][0]["booking"] == "10000001"
    assert rows["indictments"][0]["indicted"] == "09/24/2026"
    assert "gs_calendar" not in rows
    assert "PRIVATE" not in repr(dict(rows))
