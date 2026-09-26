from datetime import date
from zoneinfo import ZoneInfo

from sc_jail.stays import analyze, groups, stay

CHICAGO = ZoneInfo("America/Chicago")
COVERAGE = {"first": "2026-09-19T08:44:00+00:00", "last": "2026-09-26T00:15:00+00:00"}
SNAPSHOT = "2026-09-25"  # Central date of the last roster


def version(commitment="2026-09-21", *, money=True, no_bond=False, grade="Class C felony",
            total=5000.0, detainers=0, at="2026-09-21T15:00:00+00:00",
            status="No case marked sentenced", cases=("C1",), types=("Bond Assessed - Courts",)):
    return {"at": at, "commitment_date": commitment, "status": status, "cases": list(cases),
            "money_bond_only": money, "no_bond_set": no_bond, "grade": grade,
            "bond_total": total, "bond_types": list(types), "detainers": detainers}


def booking(*, first="2026-09-21T15:00:00+00:00", last="2026-09-26T00:15:00+00:00",
            release=None, outcome="held", details=None, truncated=False, listed_at=None,
            history=None, on_latest=True):
    return {"left_truncated": truncated, "first_seen_at": first, "last_seen_at": last,
            "release_date": release, "outcome": outcome,
            "details": [version()] if details is None else details,
            "release_history": history if history is not None else (
                [[listed_at or first, release]] if release else []),
            "release_listed_at": listed_at, "on_latest_roster": on_latest}


def test_released_booking_runs_from_commitment_to_release_date():
    result, reason = stay(booking(release="2026-09-23", outcome="released"),
                          date.fromisoformat(SNAPSHOT), CHICAGO)
    assert reason is None and result == (2, True, "commitment")


def test_held_and_disappeared_bookings_are_censored():
    snapshot = date.fromisoformat(SNAPSHOT)
    assert stay(booking(), snapshot, CHICAGO)[0] == (4, False, "commitment")
    gone = booking(outcome="disappeared", last="2026-09-22T20:00:00+00:00", on_latest=False)
    assert stay(gone, snapshot, CHICAGO)[0] == (1, False, "commitment")
    # A release date after the latest roster date is not yet a release.
    later = booking(release="2026-09-28", outcome="released")
    assert stay(later, snapshot, CHICAGO)[0] == (4, False, "commitment")


def test_old_commitment_date_is_not_a_new_admission():
    old = booking(details=[version("2026-08-01")])
    assert stay(old, date.fromisoformat(SNAPSHOT), CHICAGO) == (
        None, "Commitment date more than a week before first listed")


def test_groups_combine_the_entered_record_and_the_bond_decision():
    entered = version(money=False, total=0.0, types=("Not Assessed",), detainers=1)
    decision = version(money=True, total=800.0)
    assert groups(entered, decision) == {
        "grade": "Felony C–E", "bond": "Money bond alone", "amount": "$1,000 or less",
        "detainer": "Detainer"}
    assert groups(entered, version(money=False, no_bond=True))["bond"] == "No bond set on a case"
    assert groups(entered, version(money=False, types=("Released on own Recognizance",)))["bond"] ==         "Released on recognizance"
    assert groups(entered, None) == {"grade": "Felony C–E", "detainer": "Detainer",
                                     "bond": "No bond decision seen", "amount": None}
    assert groups(None, None)["grade"] == "Record not complete"


def test_groups_wait_for_case_entries_and_for_a_bond_decision():
    empty = version(status="No case entries listed", cases=(), grade="Other or none listed",
                    money=False, types=())
    entered = version(at="2026-09-21T18:00:00+00:00", grade="Class A misdemeanor", money=False,
                      total=0.0, types=("Not Assessed",))
    decided = version(at="2026-09-22T13:00:00+00:00", grade="Class A misdemeanor", total=500.0)
    result = analyze([booking(details=[empty, entered, decided]), booking(details=[empty])],
                     COVERAGE, CHICAGO)
    assert result["groups"]["grade"]["Misdemeanor"]["n"] == 1
    assert result["groups"]["grade"]["Record not complete"]["n"] == 1
    assert result["groups"]["bond"]["Money bond alone"]["n"] == 1
    assert result["groups"]["bond"]["No bond decision seen"]["n"] == 1
    assert list(result["groups"]["amount"]) == ["$1,000 or less"]
    completion = result["record_completion"]
    assert completion["entered"] == {"reached": 1, "not_reached": 1, "median_hours": 3.0,
                                     "ninetieth_percentile_hours": 3.0}
    assert completion["bond_decided"]["median_hours"] == 22.0


def test_analysis_excludes_bookings_present_at_coverage_start_and_counts_short_stays():
    first = "2026-09-22T10:00:00+00:00"
    bookings = [
        booking(truncated=True),
        booking(release="2026-09-23", outcome="released", listed_at="2026-09-23T15:00:00+00:00",
                last="2026-09-24T15:00:00+00:00", on_latest=False),
        # Already released when first listed: the whole stay fell between collections.
        booking(first=first, release="2026-09-22", outcome="released", listed_at=first,
                details=[version("2026-09-22")]),
        booking(details=[]),
        booking(details=[version("2026-08-01")]),
    ]
    result = analyze(bookings, COVERAGE, CHICAGO)
    assert result["cohort"] == 3
    assert result["excluded"] == {"Commitment date more than a week before first listed": 1}
    assert result["origin"] == {"commitment": 2, "first_seen": 1}
    assert result["overall"]["events"] == 2
    assert result["short_stays"]["release_listed_when_first_seen"] == 1
    assert result["short_stays"]["released_same_day"] == 1
    assert result["short_stays"]["listing_after_release_hours"]["median"] == 24.0
    assert result["groups"]["bond"]["No bond decision seen"]["n"] == 1
    assert result["followup_days"] == 6 and not result["readout_ready"]
