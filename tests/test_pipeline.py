from datetime import datetime, timedelta, timezone

import pytest

from sc_jail.config import Config
from sc_jail.http import SourceError
from sc_jail.pipeline import collect_all, delta_metrics, slot_for
from sc_jail.storage import Conflict, LocalStore, archive_blob, read_json, write_json

NOW = datetime(2026, 9, 19, 8, 0, tzinfo=timezone.utc)


def payload(ids=("A", "B")):
    return {
        "metrics": {"population": len(ids)},
        "active_ids": list(ids),
        "seen_ids": list(ids),
        "source_updated_at": None,
        "records": [{"private_name": "TEST PERSON"}],
        "artifacts": [("source.txt", b"private test data")],
        "source_url": "https://example.test",
    }


def test_population_sources_share_an_overall_deadline(tmp_path, monkeypatch):
    from sc_jail import pipeline

    clock = [100.0]
    budgets = []
    monkeypatch.setattr(pipeline.time, "monotonic", lambda: clock[0])

    def slow_iml(config, *_):
        budgets.append(("iml", config.iml_timeout))
        clock[0] += 410
        return payload()

    def xfer(config, *_):
        budgets.append(("xfer", config.source_timeout))
        return payload()

    result = collect_all(
        Config(), LocalStore(tmp_path),
        adapters={"iml": slow_iml, "xfer": xfer}, now=lambda: NOW,
    )
    assert result["status"] == "success"
    assert budgets == [("iml", 420), ("xfer", 130)]


def test_slot_alignment_converts_timezone_first():
    local = datetime(2026, 9, 19, 12, 52, tzinfo=timezone(timedelta(hours=5, minutes=45)))
    assert slot_for(local) == datetime(2026, 9, 19, 7, 0, tzinfo=timezone.utc)


def test_idempotency_and_private_data_separation(tmp_path):
    store = LocalStore(tmp_path)
    calls = []

    def adapter(*_):
        calls.append(True)
        return payload()

    config = Config(data_dir=tmp_path)
    first = collect_all(config, store, adapters={"iml": adapter}, now=lambda: NOW)
    second = collect_all(config, store, adapters={"iml": adapter}, now=lambda: NOW)
    assert first["status"] == "success"
    assert second["sources"]["iml"]["status"] == "already_collected"
    assert len(calls) == 1
    public, _ = store.read("public/index.json")
    assert b"TEST PERSON" not in public and b"private_name" not in public
    assert len(list(tmp_path.glob("private/observations/iml/**/*.gz"))) == 1


def test_failure_keeps_last_good_and_other_source_runs(tmp_path):
    store = LocalStore(tmp_path)
    config = Config(data_dir=tmp_path)
    collect_all(config, store, adapters={"iml": lambda *_: payload()}, now=lambda: NOW)

    def broken(*_):
        raise SourceError("Test outage")

    later = NOW + timedelta(minutes=15)
    result = collect_all(
        config,
        store,
        adapters={"iml": broken, "xfer": lambda *_: payload(("C",))},
        now=lambda: later,
    )
    index, _ = read_json(store, "public/index.json")
    assert result["status"] == "failed"
    assert index["sources"]["iml"]["current"]["population"] == 2
    assert index["sources"]["xfer"]["current"]["population"] == 1
    assert list(tmp_path.glob("private/failures/iml/**/*.json"))


def test_retry_recovers_persisted_manifest_without_scraping_again(tmp_path, monkeypatch):
    store = LocalStore(tmp_path)
    real_write = store.write
    calls = []

    def flaky(key, *a, **kw):
        if key.startswith("private/checkpoints") and not calls:
            calls.append(True)
            raise OSError("Test disk interruption")
        return real_write(key, *a, **kw)

    monkeypatch.setattr(store, "write", flaky)
    adapters = {"iml": lambda *_: payload()}
    assert collect_all(Config(), store, adapters=adapters, now=lambda: NOW)["status"] == "failed"

    def must_not_scrape(*_):
        raise AssertionError("Manifest should have been reused")

    result = collect_all(Config(), store, adapters={"iml": must_not_scrape}, now=lambda: NOW)
    assert result["status"] == "success"
    index, _ = read_json(store, "public/index.json")
    assert len(index["sources"]["iml"]["history"]) == 1


def test_failed_source_retries_without_redoing_successful_source(tmp_path):
    store = LocalStore(tmp_path)

    def failed(*_):
        raise SourceError("Test failure")

    collect_all(
        Config(), store, adapters={"iml": failed, "xfer": lambda *_: payload()}, now=lambda: NOW
    )

    def already(*_):
        raise AssertionError("Successful source must be skipped")

    result = collect_all(
        Config(), store, adapters={"iml": lambda *_: payload(), "xfer": already}, now=lambda: NOW
    )
    assert result["status"] == "success"


def test_no_arrivals_on_first_observation_or_across_a_gap():
    assert delta_metrics({}, ["A"], NOW, NOW)["arrivals"] is None
    before = {"active_ids": ["A", "B"], "observed_at": NOW.isoformat(), "slot": NOW.isoformat()}
    after = NOW + timedelta(minutes=15)
    assert delta_metrics(before, ["B", "C"], after, after)["arrivals"] == 1
    assert delta_metrics(before, ["B", "C"], after, after)["departures"] == 1
    after = NOW + timedelta(minutes=30)
    assert delta_metrics(before, ["B", "C"], after, after)["arrivals"] is None


def test_delayed_scheduler_retry_does_not_fabricate_past_data(tmp_path):
    def unexpected(*_):
        raise AssertionError("No historical scraping")

    result = collect_all(
        Config(),
        LocalStore(tmp_path),
        scheduled_at=NOW,
        now=lambda: NOW + timedelta(minutes=16),
        adapters={"iml": unexpected},
    )
    assert result["status"] == "expired"


def test_atomic_compare_and_swap_and_content_deduplication(tmp_path):
    store = LocalStore(tmp_path)
    version = write_json(store, "public/test.json", {"a": 1})
    with pytest.raises(Conflict):
        write_json(store, "public/test.json", {"a": 2}, expected="stale")
    assert read_json(store, "public/test.json")[0] == {"a": 1}
    write_json(store, "public/test.json", {"a": 3}, expected=version)
    one = archive_blob(store, "old.xls", b"same")
    two = archive_blob(store, "new.xls", b"same")
    assert one["key"] == two["key"]
    assert len(list(tmp_path.glob("private/blobs/**/*.gz"))) == 1


@pytest.mark.parametrize("key", ["../escape", "/absolute", "a/../../escape", "a\\escape"])
def test_storage_rejects_path_escape(tmp_path, key):
    with pytest.raises(ValueError):
        LocalStore(tmp_path).path(key)


def test_delta_retry_after_working_state_or_index_failure(tmp_path, monkeypatch):
    from sc_jail.history import reconstruct_state

    store = LocalStore(tmp_path)
    config = Config(data_dir=tmp_path)
    rows = [{"booking": f"TEST-{i:04}", "charge": f"SYNTHETIC {i}"} for i in range(250)]
    initial = payload()
    initial["records"] = rows
    collect_all(config, store, adapters={"xfer": lambda *_: initial}, now=lambda: NOW)
    real_write = store.write
    for step, failing_prefix in enumerate(("private/checkpoints", "public/index"), start=1):
        later = NOW + timedelta(minutes=15 * step)
        current = payload(("B", "C"))
        current["records"] = [dict(row) for row in rows]
        current["records"][0]["charge"] = f"CORRECTED {step}"
        interrupted = []

        def flaky(key, *args, **kwargs):
            if key.startswith(failing_prefix) and not interrupted:
                interrupted.append(True)
                raise OSError("SYNTHETIC WRITE FAILURE")
            return real_write(key, *args, **kwargs)

        monkeypatch.setattr(store, "write", flaky)
        try:
            result = collect_all(
                config, store, adapters={"xfer": lambda *_: current}, now=lambda: later
            )
            assert result["status"] == "failed"
        except OSError:
            assert failing_prefix == "public/index"
        monkeypatch.setattr(store, "write", real_write)

        def must_not_scrape(*_):
            raise AssertionError("Committed observation must be reused")

        result = collect_all(config, store, adapters={"xfer": must_not_scrape}, now=lambda: later)
        assert result["status"] == "success"
        checkpoint, _ = read_json(store, "private/checkpoints/xfer.json.gz")
        manifest, _ = read_json(store, checkpoint["manifest_key"])
        assert manifest["history"]["kind"] == "delta"
        assert reconstruct_state(store, checkpoint["manifest_key"]) == checkpoint["state"]
        assert checkpoint["state"]["active_ids"] == ["B", "C"]
        public, _ = read_json(store, "public/index.json")
        assert len(public["sources"]["xfer"]["history"]) == step + 1
