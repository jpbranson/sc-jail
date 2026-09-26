from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sc_jail.history import cached_state, canonical_state, make_history, observation_key
from sc_jail.reconcile import (
    align,
    by_day,
    case_relation,
    field_agreement,
    reconcile,
    xfer_versions,
)
from sc_jail.storage import LocalStore, read_json, write_json

CHICAGO = ZoneInfo("America/Chicago")
NOW = datetime(2026, 9, 20, 15, tzinfo=timezone.utc)  # 10:00 a.m. in Memphis


def at(minutes):
    return NOW + timedelta(minutes=minutes)


def roster(booking, release=""):
    return {"booking_number": booking, "permanent_id": "P" + booking, "release_date": release,
            "name": "PRIVATE SYNTHETIC NAME", "date_of_birth": "01/01/1990", "result_id": "X"}


def workbook(booking, *, case="C1", book="2026-09-01T10:00:00", det="NO", court=""):
    return {"Booking #": booking, "Book Date": book, "Case #": case, "Det?": det,
            "Next Court Dt": court, "Committing Authority": "SYNTHETIC COURT",
            "Inmate Name": "PRIVATE SYNTHETIC NAME"}


def observe(store, source, rows, slot, *, observed_at=None, source_updated_at=None):
    checkpoint_key = f"private/checkpoints/{source}.json.gz"
    previous, version = read_json(store, checkpoint_key, {})
    ids = sorted({row.get("booking_number") or row["Booking #"] for row in rows})
    state = canonical_state(rows, ids, ids)
    key = observation_key(source, slot)
    point = {"slot": slot.isoformat(), "observed_at": (observed_at or slot).isoformat(),
             "population": len(ids)}
    if source_updated_at:
        point["source_updated_at"] = source_updated_at.isoformat()
    manifest = {"schema": 2, "source": source, "point": point,
                "history": make_history(store, source, slot, state, previous)}
    write_json(store, key, manifest, create_only=True)
    write_json(store, checkpoint_key, cached_state(key, manifest, state, []), expected=version)


def detail(booking, *, case="C1", committed="09/01/2026", detainers=(), court=None):
    return {"booking_number": booking, "incarceration": {"Commitment Date": committed},
            "charges": [{"Case #": case}], "detainers": list(detainers),
            "hearings": [{"Next Court Date": court}] if court else []}


def test_versions_are_distinct_workbooks_aligned_to_the_nearest_roster():
    xfer = [(f"x{i}", {"point": {"source_updated_at": src.isoformat(), "observed_at": obs.isoformat()},
                       "history": {"state_sha256": sha}})
            for i, (src, obs, sha) in enumerate([(at(-5), at(0), "a"), (at(-5), at(15), "a"),
                                                  (at(115), at(120), "b"), (at(300), at(315), "c")])]
    iml = [(f"i{m}", {"point": {"observed_at": at(m).isoformat()}}) for m in (0, 15, 120)]
    versions = align(xfer_versions(xfer), iml)
    assert [v["xfer_key"] for v in versions] == ["x0", "x2", "x3"]
    assert [v["iml_key"] for v in versions] == ["i0", "i120", None]  # 180 minutes is too far
    assert versions[1]["offset_minutes"] == 5.0


def test_reconcile_counts_each_kind_of_difference(tmp_path):
    store = LocalStore(tmp_path)
    # B4 was listed by IML earlier and later dropped; B5 is released today in IML.
    observe(store, "iml", [roster("B1"), roster("B2"), roster("B4")], at(-240))
    observe(store, "iml", [roster("B1"), roster("B2"), roster("B3"), roster("B5", "2026-09-20")], at(0))
    observe(store, "xfer", [workbook("B1"), workbook("B1", case="C2"), workbook("B2"),
                            workbook("B4"), workbook("B5"), workbook("B9")],
            at(0), observed_at=at(2), source_updated_at=at(-3))
    details = [detail("B1", case="C1"), detail("B2", committed="09/02/2026")]
    result = reconcile(store, CHICAGO, details)
    latest = result["latest"]
    assert latest["xfer_bookings"] == 5 and latest["iml_held"] == 3 and latest["both"] == 2
    assert latest["xfer_not_on_roster"] == 2  # B4 and B9
    assert latest["xfer_not_on_roster_seen_before"] == 1  # only B4 was ever on the roster
    assert latest["xfer_listed_iml_released"] == 1  # B5
    assert latest["iml_held_not_in_xfer"] == 1 and latest["iml_held_not_in_xfer_recent"] == 1  # B3
    agreement = result["latest_field_agreement"]
    assert agreement["bookings_compared"] == 2
    assert agreement["book_date"] == {"Same date": 1, "XFER book date earlier": 1}
    assert agreement["case_numbers"] == {"IML lists fewer (subset of XFER)": 1, "Identical": 1}
    assert result["unaligned_versions"] == []
    differences = result["latest_differences"]
    assert differences["xfer_only"]["committing_authority"] == {"SYNTHETIC COURT": 2}
    # Booked Sept 1; the workbook is from Sept 20.
    assert differences["xfer_only"]["book_date_age"] == {"8–30 days": 2}
    assert differences["iml_only"]["current_location"] == {"No IML record page": 1}
    assert by_day(result["pairs"], CHICAGO)[0]["both"] == 2


def test_field_agreement_compares_detainers_and_court_dates():
    rows = [workbook("B1", det="YES", court="2026-10-01T09:00:00"), workbook("B2", det="NO")]
    details = [detail("B1", detainers=[{"Issued By": "X"}], court="10/01/2026 09:00"),
               detail("B2", detainers=[{"Issued By": "X"}], court="10/05/2026 09:00")]
    result = field_agreement(rows, details, {"B1", "B2", "B3"})
    assert result["detainer"] == {"Both show a detainer": 1, "Only IML shows a detainer": 1}
    assert result["next_court"] == {"Same earliest date": 1, "Only one lists a date": 1}


def test_case_relations():
    assert case_relation({"A"}, {"A"}) == "Identical"
    assert case_relation({"A"}, {"A", "B"}) == "XFER lists fewer (subset of IML)"
    assert case_relation({"A", "C"}, {"A", "B"}) == "Partly overlapping"
    assert case_relation({"C"}, {"B"}) == "No case number in common"
    assert case_relation(set(), {"B"}) == "One side lists no case numbers"
