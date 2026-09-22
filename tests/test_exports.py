import time
from datetime import timedelta

from test_courts import NOW
from test_courts import collect as collect_courts
from test_courts import install_http as courts_http
from test_details import collect, detail_html, install_http, seed_roster

from sc_jail import iml_details
from sc_jail.config import Config
from sc_jail.exporters import export_courts, export_details
from sc_jail.storage import LocalStore


def test_private_detail_export_reconstructs_freshness_and_filters(tmp_path, monkeypatch):
    store = LocalStore(tmp_path)
    seed_roster(store)
    install_http(monkeypatch, iter([detail_html()]))
    collect(store)
    later = NOW + timedelta(minutes=15)
    collect(store, later)
    rows = list(export_details(store, slot=later.isoformat(), booking="TEST-BK-1", case="CASE-02"))
    assert len(rows) == 1 and len(rows[0]["charges"]) == 2
    assert rows[0]["retrieval"]["checked_at"] == NOW.isoformat()
    assert rows[0]["retrieval"]["raw_html"]["sha256"]
    assert not list(export_details(store, booking="UNKNOWN"))
    assert not list(export_details(store, case="UNKNOWN"))


def test_new_daily_checkpoint_includes_all_detail_retrieval_metadata(tmp_path, monkeypatch):
    store = LocalStore(tmp_path)
    seed_roster(store)
    install_http(monkeypatch, iter([detail_html()]))
    collect(store)
    # Advance roster freshness into the next UTC day without changing its content.
    from sc_jail.storage import read_json, write_json

    roster, version = read_json(store, "private/checkpoints/iml.json.gz")
    later = NOW + timedelta(days=1)
    roster["observed_at"] = roster["slot"] = later.isoformat()
    write_json(store, "private/checkpoints/iml.json.gz", roster, expected=version)
    iml_details.collect_details(
        Config(detail_refresh_hours=48),
        store,
        later,
        deadline=time.monotonic() + 60,
        now=lambda: later,
    )
    assert (
        list(export_details(store, slot=later.isoformat()))[0]["retrieval"]["checked_at"]
        == NOW.isoformat()
    )


def test_private_court_export_includes_source_metadata_and_exact_identifiers(tmp_path, monkeypatch):
    store = LocalStore(tmp_path)
    courts_http(monkeypatch)
    collect_courts(store)
    rows = list(export_courts(store, family="criminal_calendar", case="00123"))
    assert len(rows) == 1 and rows[0]["record"]["Case Number"] == "00123"
    assert rows[0]["raw_sha256"] and rows[0]["first_captured_at"]
    assert not list(export_courts(store, case="123"))
    assert len(list(export_courts(store, all_versions=True))) == 1
