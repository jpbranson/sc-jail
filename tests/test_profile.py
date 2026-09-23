from datetime import date
from zoneinfo import ZoneInfo

from sc_jail.profile import (
    legal_status,
    money_band,
    money_bond_only,
    most_serious,
    movement,
    profile,
    suppress,
)

TODAY = date(2026, 9, 23)


def bond(case="TEST-C1", status="Open", kind="Bond Assessed - Courts", amount="5000.00"):
    return {"Case #": case, "Status": status, "Bond Type": kind, "Amount": amount,
            "Total": amount, "Additional": "", "Percent": "", "Post Date": "", "Posted By": ""}


def charge(grade="FC", description="SYNTHETIC OFFENSE"):
    return {"Case #": "TEST-C1", "Grade": grade, "Description": description, "Code": "0",
            "Degree": "", "Offense Date": "01/01/2026"}


def detail(booking, *, committed="09/01/2026", born="01/01/1990", sex="M", bonds=None,
           charges=None, detainers=(), hearing="09/30/2026 09:00", total="5000.00"):
    return {
        "booking_number": booking,
        "permanent_id": "TEST-P-" + booking,
        "physical": {"DOB": born, "Sex": sex},
        "inmate": {"Race": "Synthetic", "Ethnicity": ""},
        "incarceration": {"Commitment Date": committed, "Current Location": "JMS"},
        "charges": [charge()] if charges is None else charges,
        "bonds": [bond()] if bonds is None else bonds,
        "bond_totals": {"Grand Total": total},
        "hearings": [{"Next Court Date": hearing}] if hearing else [],
        "detainers": list(detainers),
    }


def roster(*bookings, released=()):
    return [{"booking_number": b, "release_date": "2026-09-22" if b in released else ""}
            for b in bookings]


def test_profile_counts_only_people_without_release_dates():
    details = [detail("B1"), detail("B2"), detail("B3")]
    result = profile(details, roster("B1", "B2", "B3", "B4", released={"B3"}), TODAY)
    assert result["people"] == 2
    assert result["roster_current"] == 3
    assert result["missing_details"] == 1


def test_time_held_uses_commitment_date_and_rejects_future_dates():
    details = [detail("B1", committed="09/22/2026"), detail("B2", committed="09/23/2025"),
               detail("B3", committed="10/01/2026"), detail("B4", committed="")]
    result = profile(details, roster("B1", "B2", "B3", "B4"), TODAY)
    held = {row["label"]: row["count"] for row in result["held"]}
    assert held["Under 1 week"] == 1
    assert held["6–12 months"] == 1
    assert result["flags"]["commitment_missing_or_future"] == 2
    assert result["held_median_days"] == (1 + 365) / 2


def test_age_is_computed_on_the_snapshot_date():
    details = [detail("B1", born="09/24/2008"), detail("B2", born="09/23/2008")]
    ages = {r["label"]: r["count"] for r in profile(details, roster("B1", "B2"), TODAY)["age"]}
    assert ages["Under 18"] == 1
    assert ages["18–24"] == 1


def test_legal_status_distinguishes_partly_sentenced_people():
    assert legal_status([]) == "No case entries listed"
    assert legal_status([bond(status="Sentenced")]) == "Sentenced on every listed case"
    assert legal_status([bond(status="Sentenced"), bond(status="Open")]) == (
        "Sentenced on some cases, others open")
    assert legal_status([bond(status="Open"), bond(status="")]) == "No case marked sentenced"


def test_most_serious_grade_prefers_felonies_over_violations():
    assert most_serious([charge("MA"), charge("FE"), charge("IE")]) == "Class E felony"
    assert most_serious([charge("FA"), charge("FM")]) == "First-degree murder (FM)"
    assert most_serious([charge("IE")]) == "Probation, parole, or diversion violation only"
    assert most_serious([]) == "Other or none listed"


def test_money_bond_only_excludes_other_reasons_to_be_held():
    assert money_bond_only(detail("B1")) == 5000
    assert money_bond_only(detail("B1", detainers=[{"Issued By": "Synthetic"}])) is None
    assert money_bond_only(detail("B1", charges=[charge("IE")])) is None
    assert money_bond_only(detail("B1", bonds=[bond(), bond(status="Sentenced")])) is None
    assert money_bond_only(detail("B1", bonds=[bond(kind="No Bond Set")])) is None
    assert money_bond_only(detail("B1", bonds=[])) is None
    assert money_bond_only(detail("B1", total="0.0")) is None


def test_money_bands_have_inclusive_upper_bounds():
    assert money_band(1000) == "$1,000 or less"
    assert money_band(1000.01) == "$1,001–$5,000"
    assert money_band(250_001) == "More than $250,000"


def test_next_court_date_uses_the_earliest_listed_date():
    details = [detail("B1", hearing="09/22/2026 09:00"), detail("B2", hearing="09/23/2026 13:00"),
               detail("B3", hearing=None), detail("B4", hearing="12/31/2026 09:00")]
    court = {r["label"]: r["count"] for r in profile(details, roster("B1", "B2", "B3", "B4"),
                                                      TODAY)["court"]}
    assert court == {"Listed date before today": 1, "Today": 1, "1–7 days": 0, "8–30 days": 0,
                     "31–90 days": 0, "More than 90 days": 1, "No date listed": 1}


def test_movement_excludes_initial_backlog_and_partial_days():
    start = "2026-09-19T08:44:00+00:00"
    visit = {"commitment_date": None, "person_ids": ["P"], "release_date": None}
    registry = {
        "coverage_start": start,
        "through": "2026-09-22T06:00:00+00:00",
        "visits": {
            "OLD": {**visit, "first_seen_at": start, "release_date": "2026-09-20"},
            "NEW1": {**visit, "first_seen_at": "2026-09-20T15:00:00+00:00"},
            # 04:00 UTC on September 21 is still September 20 in Memphis.
            "NEW2": {**visit, "first_seen_at": "2026-09-21T04:00:00+00:00"},
            "NEW3": {**visit, "first_seen_at": "2026-09-21T15:00:00+00:00",
                     "release_date": "2026-09-21"},
            "EARLY": {**visit, "first_seen_at": "2026-09-19T12:00:00+00:00",
                      "release_date": "2026-09-19"},
        },
    }
    days = movement(registry, ZoneInfo("America/Chicago"))
    assert days == [
        {"day": "2026-09-20", "first_seen": 2, "released": 1},
        {"day": "2026-09-21", "first_seen": 1, "released": 1},
    ]


def test_small_counts_are_suppressed():
    assert suppress(0) == 0
    assert suppress(9) == "<10"
    assert suppress(10) == 10
