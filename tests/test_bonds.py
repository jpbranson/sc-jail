from datetime import date
from zoneinfo import ZoneInfo

from sc_jail.bonds import analyze, bond_events, classify, release_after

CHICAGO = ZoneInfo("America/Chicago")
COVERAGE = {"first": "2026-09-19T08:44:00+00:00", "last": "2026-09-26T00:15:00+00:00"}
ASSESSED = "Bond Assessed - Courts"


def version(at, total, *, types=(ASSESSED,), money=True, committed="2026-09-21",
            status="No case marked sentenced", cases=("C1",)):
    return {"at": at, "commitment_date": committed, "status": status, "cases": list(cases),
            "money_bond_only": money, "no_bond_set": False, "grade": "Class C felony",
            "bond_total": total, "bond_types": list(types), "detainers": 0}


def booking(details, *, release=None, outcome="held", truncated=False, on_latest=True,
            first="2026-09-21T15:00:00+00:00"):
    return {"details": details, "release_date": release, "outcome": outcome,
            "left_truncated": truncated, "on_latest_roster": on_latest,
            "first_seen_at": first, "last_seen_at": COVERAGE["last"]}


def test_classify_bond_changes():
    base = version("t0", 5000.0)
    assert classify(version("t0", 0.0, types=("Not Assessed",)), base) == "New court-assessed bond"
    assert classify(base, version("t1", 2500.0)) == "Bond total reduced"
    assert classify(base, version("t1", 7500.0)) == "Bond total increased"
    assert classify(base, version("t1", 0.0, types=(ASSESSED, "Released on own Recognizance"))) == \
        "Recognizance entered"
    assert classify(base, version("t1", 0.0)) == "Bond total cleared"
    assert classify(base, version("t1", 5000.0)) is None


def test_events_skip_incomplete_pages_and_keep_the_first_of_each_kind():
    empty = version("2026-09-21T15:00:00+00:00", None, types=(), money=False,
                    status="No case entries listed", cases=())
    details = [empty,
               version("2026-09-21T16:00:00+00:00", 0.0, types=("Not Assessed",), money=False),
               version("2026-09-22T16:00:00+00:00", 10000.0),
               version("2026-09-23T16:00:00+00:00", 5000.0),
               version("2026-09-24T16:00:00+00:00", 2000.0)]
    assert [(kind, at[:10]) for kind, at, _, _ in bond_events(booking(details))] == [
        ("New court-assessed bond", "2026-09-22"), ("Bond total reduced", "2026-09-23")]


def test_release_seen_before_a_change_is_not_followed():
    released = booking([], release="2026-09-22", outcome="released")
    snapshot = date(2026, 9, 25)
    assert release_after(released, date(2026, 9, 23), snapshot, CHICAGO) is None
    assert release_after(released, date(2026, 9, 22), snapshot, CHICAGO) == (0, True)
    assert release_after(booking([]), date(2026, 9, 23), snapshot, CHICAGO) == (2, False)


def test_analysis_counts_changes_low_bond_stock_and_new_bookings():
    reduced = booking([version("2026-09-21T16:00:00+00:00", 10000.0),
                       version("2026-09-22T16:00:00+00:00", 4000.0)],
                      release="2026-09-23", outcome="released", on_latest=False)
    # Held since August on a $900 money bond alone; present when collection began.
    waiting = booking([version("2026-09-19T12:00:00+00:00", 900.0, committed="2026-08-26")],
                      truncated=True, first=COVERAGE["first"])
    new_low = booking([version("2026-09-21T16:00:00+00:00", 1000.0)])
    result = analyze([reduced, waiting, new_low], COVERAGE, CHICAGO)
    change = result["changes"]["Bond total reduced"]
    assert change["bookings"] == 1 and change["time_to_release"]["events"] == 1
    assert result["median_reduction_share"] == 0.6
    assert result["low_bond_held_now"]["1000"]["people"] == 2
    assert result["low_bond_held_now"]["1000"]["median_days_held"] == 30  # sorted [4, 30]
    assert result["low_bond_held_now"]["1000"]["held_over_30_days"] == 0
    flow = result["low_bond_new_bookings"]
    assert flow["1000"]["n"] == 1 and flow["5000"]["n"] == 1  # reduced started above $5,000
    assert flow["10000"]["n"] == 2
    assert result["followup_days"] == 6 and not result["readout_ready"]
