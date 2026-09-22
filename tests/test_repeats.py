from datetime import datetime, timedelta, timezone

import pytest

from sc_jail.history import cached_state, canonical_state, make_history, observation_key
from sc_jail.repeats import (
    CACHE_KEY,
    record_details,
    record_roster,
    refresh_repeat_visits,
    summarize_visits,
)
from sc_jail.storage import LocalStore, read_json, write_json

NOW = datetime(2026, 9, 21, 13, tzinfo=timezone.utc)


def registry():
    return {"schema": 1, "visits": {}, "cursors": {},
            "coverage_start": NOW.isoformat(), "through": NOW.isoformat()}


def roster(person, booking, release=""):
    return {"permanent_id": person, "booking_number": booking, "release_date": release,
            "name": "PRIVATE SYNTHETIC NAME"}


def detail(person, booking, start):
    return {"permanent_id": person, "booking_number": booking,
            "incarceration": {"Commitment Date": start}}


def observe(store, source, rows, moment):
    checkpoint_key = f"private/checkpoints/{source}.json.gz"
    previous, version = read_json(store, checkpoint_key, {})
    ids = sorted({row["booking_number"] for row in rows})
    state = canonical_state(rows, ids, ids)
    key = observation_key(source, moment)
    manifest = {
        "schema": 2, "source": source,
        "point": {"slot": moment.isoformat(), "observed_at": moment.isoformat()},
        "history": make_history(store, source, moment, state, previous),
    }
    write_json(store, key, manifest, create_only=True)
    cache = cached_state(key, manifest, state, previous.get("seen_ids", []))
    write_json(store, checkpoint_key, cache, expected=version)
    return key


def test_distinct_bookings_not_polls_or_reappearance():
    data = registry()
    first = roster("PERSON-A", "BOOK-A", "2026-09-02")
    record_roster(data, [first, roster("PERSON-B", "BOOK-B")], NOW.isoformat())
    record_roster(data, [], (NOW + timedelta(minutes=15)).isoformat())
    record_roster(data, [first], (NOW + timedelta(hours=1)).isoformat())
    record_roster(data, [first, roster("PERSON-A", "BOOK-C")], NOW.isoformat())
    record_details(data, [detail("PERSON-A", "BOOK-A", "09/01/2026"),
                          detail("PERSON-A", "BOOK-C", "09/04/2026")], NOW.isoformat())
    result = summarize_visits(data)
    assert result["people_seen"] == 2
    assert result["bookings_seen"] == 3
    assert result["repeat_people"] == 1
    assert result["repeat_bookings"] == 2
    assert result["people_once"] == 1
    assert result["additional_visits"] == 1
    assert result["median_days_between_visits"] == 2
    assert result["interval_distribution"][1]["count"] == 1


def test_missing_and_overlapping_dates_are_not_zero_or_bridged():
    data = registry()
    rows = [
        roster("A", "A1", "2026-09-01"), roster("A", "A2"), roster("A", "A3"),
        roster("B", "B1", "2026-09-10"), roster("B", "B2"),
        roster("C", "C1", "2026-09-03"), roster("C", "C2"),
        roster("D", "D1", "2026-09-03"), roster("D", "D2"),
    ]
    record_roster(data, rows, NOW.isoformat())
    record_details(data, [
        detail("A", "A1", "08/01/2026"), detail("A", "A3", "09/15/2026"),
        detail("B", "B1", "08/01/2026"), detail("B", "B2", "09/05/2026"),
        detail("C", "C1", "09/03/2026"), detail("C", "C2", "09/03/2026"),
        detail("D", "D1", "08/01/2026"), detail("D", "D2", "09/03/2026"),
    ], NOW.isoformat())
    result = summarize_visits(data)
    assert result["additional_visits"] == 5
    assert result["missing_date_intervals"] == 2
    assert result["invalid_date_intervals"] == 2
    assert result["measured_intervals"] == 1
    assert result["median_days_between_visits"] == 0
    assert result["interval_distribution"][0]["count"] == 1


def test_date_corrections_and_identity_conflicts():
    data = registry()
    record_roster(data, [roster("A", "ONE", "2026-09-02"), roster("A", "TWO")], NOW.isoformat())
    record_details(data, [detail("A", "ONE", "09/01/2026"),
                          detail("A", "TWO", "09/04/2026")], NOW.isoformat())
    assert summarize_visits(data)["measured_intervals"] == 1
    record_roster(data, [roster("A", "ONE")], NOW.isoformat())
    assert summarize_visits(data)["missing_date_intervals"] == 1
    record_roster(data, [roster("B", "ONE")], NOW.isoformat())
    result = summarize_visits(data)
    assert result["excluded_bookings"] == 2
    assert result["repeat_people"] == 0


def test_archive_backfill_retains_departed_bookings_and_is_idempotent(tmp_path):
    store = LocalStore(tmp_path)
    old = NOW - timedelta(days=120)
    observe(store, "iml", [roster("PERSON-A", "OLD", "2026-06-01")], old)
    observe(store, "iml_details", [detail("PERSON-A", "OLD", "05/01/2026")], old)
    observe(store, "iml", [roster("PERSON-A", "NEW")], NOW)
    observe(store, "iml_details", [detail("PERSON-A", "NEW", "09/21/2026")], NOW)
    summary = refresh_repeat_visits(store)
    assert summary["repeat_people"] == 1
    assert summary["bookings_seen"] == 2
    assert summary["median_days_between_visits"] == 112
    assert summary["coverage_start"] == old.isoformat()
    before = store.read(CACHE_KEY)[0]
    assert refresh_repeat_visits(store) == summary
    assert store.read(CACHE_KEY)[0] == before
    later = NOW + timedelta(minutes=15)
    observe(store, "iml", [roster("PERSON-A", "NEW")], later)
    updated = refresh_repeat_visits(store)
    assert updated["bookings_seen"] == 2
    assert updated["through"] == later.isoformat()
    assert "PERSON-A" not in str(updated)
    assert "PRIVATE SYNTHETIC NAME" not in str(updated)
    assert refresh_repeat_visits(store, rebuild=True) == updated


def test_late_details_fill_missing_intervals_without_new_visits(tmp_path):
    store = LocalStore(tmp_path)
    observe(store, "iml", [roster("A", "ONE", "2026-09-02"), roster("A", "TWO")], NOW)
    summary = refresh_repeat_visits(store)
    assert summary["missing_date_intervals"] == 1
    observe(store, "iml_details", [
        detail("A", "ONE", "09/01/2026"), detail("A", "TWO", "09/05/2026"),
    ], NOW)
    result = refresh_repeat_visits(store)
    assert result["repeat_people"] == 1
    assert result["missing_date_intervals"] == 0
    assert result["median_days_between_visits"] == 3


def test_incomplete_refresh_preserves_last_good_registry(tmp_path):
    store = LocalStore(tmp_path)
    observe(store, "iml", [roster("A", "ONE")], NOW)
    refresh_repeat_visits(store)
    original = store.read(CACHE_KEY)[0]
    observe(store, "iml", [roster("A", "TWO")], NOW + timedelta(minutes=15))
    with pytest.raises(TimeoutError):
        refresh_repeat_visits(store, deadline=0)
    assert store.read(CACHE_KEY)[0] == original
    assert refresh_repeat_visits(store)["repeat_people"] == 1


def test_collector_refreshes_repeats_and_preserves_them_on_failure(tmp_path, monkeypatch):
    from sc_jail import pipeline, repeats, supplemental
    from sc_jail.config import Config

    store = LocalStore(tmp_path)
    rows = [roster("A", "ONE"), roster("A", "TWO")]
    payload = {
        "metrics": {"population": 1},
        "active_ids": ["A"], "seen_ids": ["A"],
        "source_updated_at": None, "records": rows,
        "artifacts": [("synthetic.txt", b"SYNTHETIC")], "source_url": "https://example.test",
    }
    monkeypatch.setattr(pipeline, "SOURCES", {"iml": lambda *_: payload})
    monkeypatch.setattr(supplemental, "collect_supplements", lambda *a, **kw: {})
    result = pipeline.collect_all(Config(), store, now=lambda: NOW)
    assert result["status"] == "success"
    index, _ = read_json(store, "public/index.json")
    assert index["repeat_visits"]["repeat_people"] == 1
    assert index["repeat_visits"]["bookings_seen"] == 2

    def failed(*args, **kwargs):
        raise OSError("SYNTHETIC FAILURE")

    monkeypatch.setattr(repeats, "refresh_repeat_visits", failed)
    later = NOW + timedelta(minutes=15)
    result = pipeline.collect_all(Config(), store, now=lambda: later)
    assert result["sources"]["iml"]["status"] == "success"
    index, _ = read_json(store, "public/index.json")
    assert index["repeat_visits"]["repeat_people"] == 1
    assert "delayed" in index["repeat_visits"]["error"]
    assert index["sources"]["iml"]["last_success"] == later.isoformat()
