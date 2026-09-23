import time
from datetime import datetime, timezone

from sc_jail import pipeline, supplemental
from sc_jail.config import Config
from sc_jail.http import SourceError
from sc_jail.storage import LocalStore, read_json

NOW = datetime(2026, 9, 19, 8, tzinfo=timezone.utc)


def test_population_commits_before_supplements_and_failures_do_not_erase_it(tmp_path, monkeypatch):
    store = LocalStore(tmp_path)

    def core(*args):
        return {
            "metrics": {"population": 1},
            "active_ids": ["TEST"],
            "seen_ids": ["TEST"],
            "source_updated_at": None,
            "records": [{"name": "PRIVATE SYNTHETIC"}],
            "artifacts": [],
            "source_url": "https://example.test",
        }

    monkeypatch.setattr(pipeline, "SOURCES", {"iml": core, "xfer": core})
    seen = []

    def courts(*args, **kwargs):
        public, _ = read_json(store, "public/index.json")
        assert public["sources"]["iml"]["current"]["population"] == 1
        assert public["sources"]["xfer"]["current"]["population"] == 1
        seen.append("courts")
        raise SourceError("Synthetic court outage")

    def details(*args, **kwargs):
        seen.append("details")
        return {
            "slot": NOW.isoformat(),
            "finished_at": NOW.isoformat(),
            "failed": 0,
            "available": 1,
        }

    monkeypatch.setattr(supplemental, "collect_courts", courts)
    monkeypatch.setattr(supplemental, "collect_details", details)
    result = pipeline.collect_all(Config(), store, now=lambda: NOW)
    assert result["status"] == "success"
    assert seen == ["courts", "details"]
    index, _ = read_json(store, "public/index.json")
    assert index["sources"]["xfer"]["current"]["population"] == 1
    assert index["supplements"]["xfer_courts"]["error"] == "Synthetic court outage"
    assert b"PRIVATE SYNTHETIC" not in store.read("public/index.json")[0]


def test_deadline_defers_supplements_without_network(tmp_path):
    def forbidden(*args, **kwargs):
        raise AssertionError("No budget remains")

    index = {}
    result = supplemental.collect_supplements(
        Config(),
        LocalStore(tmp_path),
        index,
        NOW,
        deadline=time.monotonic(),
        now=lambda: NOW,
        collectors={"iml_details": forbidden},
    )
    assert result["iml_details"]["status"] == "failed"
    assert "budget" in index["supplements"]["iml_details"]["error"]


def test_expansion_settings_reject_unbounded_or_invalid_values():
    import pytest

    for kwargs in (
        {"detail_batch": -1},
        {"detail_refresh_hours": 0},
        {"detail_refresh_ahead_hours": -1},
        {"detail_refresh_ahead_hours": float("nan")},
        {"detail_refresh_ahead_hours": float("inf")},
        {"court_budget": float("nan")},
        {"court_batch": 2001},
    ):
        with pytest.raises(ValueError):
            Config(**kwargs)


def test_early_refresh_environment_setting(monkeypatch):
    monkeypatch.setenv("SCJ_DETAIL_REFRESH_AHEAD_HOURS", "2.5")
    assert Config.from_env().detail_refresh_ahead_hours == 2.5
    monkeypatch.setenv("SCJ_DETAIL_REFRESH_AHEAD_HOURS", "0")
    assert Config.from_env().detail_refresh_ahead_hours == 0
