from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

from sc_jail.history import cached_state, canonical_state, make_history, observation_key
from sc_jail.panel import build_panel, check_populations, missing_slots, value_at
from sc_jail.storage import LocalStore, read_json, write_json

CHICAGO = ZoneInfo("America/Chicago")
# 15:00 UTC on September 20 is 10:00 a.m. in Memphis.
NOW = datetime(2026, 9, 20, 15, tzinfo=timezone.utc)


def roster(booking, person, release=""):
    return {"booking_number": booking, "permanent_id": person, "release_date": release,
            "name": "PRIVATE SYNTHETIC NAME", "date_of_birth": "01/01/1990", "result_id": "X"}


def detail(booking, *, bond="5000.00", court="09/30/2026 09:00"):
    return {
        "booking_number": booking,
        "permanent_id": "P-" + booking,
        "incarceration": {"Commitment Date": "09/01/2026"},
        "charges": [{"Case #": "TEST-C1", "Grade": "FC", "Description": "SYNTHETIC"}],
        "bonds": [{"Case #": "TEST-C1", "Status": "Open", "Bond Type": "Bond Assessed - Courts",
                   "Amount": bond}],
        "bond_totals": {"Grand Total": bond},
        "hearings": [{"Next Court Date": court}],
        "detainers": [],
    }


def population(rows, moment):
    today = moment.astimezone(CHICAGO).date().isoformat()
    return len({r["permanent_id"] for r in rows
                if not r["release_date"] or r["release_date"] > today})


def observe(store, source, rows, moment, *, archived=None):
    checkpoint_key = f"private/checkpoints/{source}.json.gz"
    previous, version = read_json(store, checkpoint_key, {})
    ids = sorted({row["booking_number"] for row in rows})
    state = canonical_state(rows, ids, ids)
    key = observation_key(source, moment)
    point = {"slot": moment.isoformat(), "observed_at": moment.isoformat()}
    if source == "iml":
        point["population"] = population(rows, moment) if archived is None else archived
    manifest = {"schema": 2, "source": source, "point": point,
                "history": make_history(store, source, moment, state, previous)}
    write_json(store, key, manifest, create_only=True)
    write_json(store, checkpoint_key, cached_state(key, manifest, state, []), expected=version)


def at(minutes):
    return NOW + timedelta(minutes=minutes)


def test_panel_tracks_spans_releases_and_outcomes(tmp_path):
    store = LocalStore(tmp_path)
    observe(store, "iml", [roster("B1", "P1"), roster("B2", "P2")], at(0))
    observe(store, "iml", [roster("B1", "P1"), roster("B2", "P2", "2026-09-20"),
                           roster("B3", "P3")], at(15))
    # A missed slot (at 30) does not split a span; absence from a complete roster does.
    observe(store, "iml", [roster("B2", "P2", "2026-09-20"), roster("B3", "P3")], at(45))
    observe(store, "iml", [roster("B1", "P1"), roster("B3", "P3")], at(60))
    bookings, observations = build_panel(store, CHICAGO)
    b1, b2, b3 = bookings["B1"], bookings["B2"], bookings["B3"]
    assert b1["spans"] == [[at(0).isoformat(), at(15).isoformat()],
                           [at(60).isoformat(), at(60).isoformat()]]
    assert b1["reappearances"] == 1 and b1["outcome"] == "held" and b1["left_truncated"]
    assert b2["outcome"] == "released"
    assert b2["release_history"] == [[at(15).isoformat(), "2026-09-20"]]
    assert b3["outcome"] == "held" and not b3["left_truncated"]
    assert check_populations(bookings, observations, CHICAGO) == []
    assert missing_slots(observations) == [at(30).isoformat()]


def test_booking_that_leaves_without_a_release_date_is_disappeared(tmp_path):
    store = LocalStore(tmp_path)
    observe(store, "iml", [roster("B1", "P1"), roster("B2", "P2")], at(0))
    observe(store, "iml", [roster("B2", "P2")], at(15))
    bookings, _ = build_panel(store, CHICAGO)
    assert bookings["B1"]["outcome"] == "disappeared"


def test_withdrawn_release_and_reassigned_person_match_archived_populations(tmp_path):
    store = LocalStore(tmp_path)
    observe(store, "iml", [roster("B1", "P1"), roster("B2", "P2")], at(0))
    observe(store, "iml", [roster("B1", "P1", "2026-09-20"), roster("B2", "P2")], at(15))
    observe(store, "iml", [roster("B1", "P1"), roster("B2", "P1")], at(30))
    bookings, observations = build_panel(store, CHICAGO)
    assert bookings["B1"]["release_history"] == [[at(15).isoformat(), "2026-09-20"],
                                                  [at(30).isoformat(), None]]
    assert bookings["B2"]["permanent_ids"] == ["P1", "P2"]
    assert value_at(bookings["B2"]["permanent_id_history"], at(20).isoformat()) == "P2"
    # Counting every ID a booking ever had would report 2 people at 30 instead of 1.
    assert [p["population"] for p in observations] == [2, 1, 1]
    assert check_populations(bookings, observations, CHICAGO) == []


def test_population_mismatch_is_reported(tmp_path):
    store = LocalStore(tmp_path)
    observe(store, "iml", [roster("B1", "P1")], at(0), archived=2)
    bookings, observations = build_panel(store, CHICAGO)
    assert check_populations(bookings, observations, CHICAGO) == [
        {"observed_at": at(0).isoformat(), "archived": 2, "panel": 1}]


def test_detail_versions_record_only_changed_facts(tmp_path):
    store = LocalStore(tmp_path)
    observe(store, "iml", [roster("B1", "P1")], at(0))
    observe(store, "iml_details", [detail("B1")], at(0))
    observe(store, "iml_details", [detail("B1")], at(15))
    # A later check with a lowered bond and a new court date is one new version.
    observe(store, "iml_details", [detail("B1", bond="2500.00", court="10/15/2026 09:00")], at(30))
    observe(store, "iml_details", [detail("B1", bond="2500.00", court="10/15/2026 09:00"),
                                   detail("UNLISTED")], at(45))
    bookings, _ = build_panel(store, CHICAGO)
    versions = bookings["B1"]["details"]
    assert [(v["at"], v["bond_total"], v["next_court"]) for v in versions] == [
        (at(0).isoformat(), 5000.0, "2026-09-30"),
        (at(30).isoformat(), 2500.0, "2026-10-15"),
    ]
    assert versions[0]["money_bond_only"] and versions[0]["status"] == "No case marked sentenced"
    assert versions[0]["bond_types"] == ["Bond Assessed - Courts"]
    assert "UNLISTED" not in bookings


def test_empty_archive_is_an_error(tmp_path):
    with pytest.raises(RuntimeError):
        build_panel(LocalStore(tmp_path), CHICAGO)
