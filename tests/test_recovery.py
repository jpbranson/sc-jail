from datetime import timedelta

import pytest
from test_pipeline import NOW, payload

from sc_jail.archive import rebuild_index
from sc_jail.config import Config
from sc_jail.history import observation_key
from sc_jail.pipeline import collect_all
from sc_jail.storage import LocalStore, read_json


@pytest.mark.parametrize("failure_key", ["private/checkpoints/iml.json.gz", "public/index.json"])
def test_next_slot_reconciles_committed_work_and_seen_ids(tmp_path, monkeypatch, failure_key):
    store = LocalStore(tmp_path)
    collect_all(Config(), store, adapters={"iml": lambda *_: payload(("A",))}, now=lambda: NOW)
    original = store.write
    failed = []

    def interrupt(key, *args, **kwargs):
        if key == failure_key and not failed:
            failed.append(key)
            raise OSError("synthetic interruption")
        return original(key, *args, **kwargs)

    with monkeypatch.context() as m:
        m.setattr(store, "write", interrupt)
        try:
            collect_all(Config(), store, adapters={"iml": lambda *_: payload(("B",))},
                        now=lambda: NOW + timedelta(minutes=15))
        except OSError:
            assert failure_key == "public/index.json"
    result = collect_all(Config(), store, adapters={"iml": lambda *_: payload(("A",))},
                         now=lambda: NOW + timedelta(minutes=30))
    assert result["status"] == "success"
    cache, _ = read_json(store, "private/checkpoints/iml.json.gz")
    index, _ = read_json(store, "public/index.json")
    assert cache["seen_ids"] == ["A", "B"]
    assert len(index["sources"]["iml"]["history"]) == 3
    assert index["sources"]["iml"]["current"]["people_or_bookings_seen"] == 2
    assert index["sources"]["iml"]["current"]["arrivals"] == 1


def test_corrupt_cache_is_rebuilt_and_does_not_block_other_source(tmp_path):
    store = LocalStore(tmp_path)
    collect_all(Config(), store, adapters={"iml": lambda *_: payload(("A",))}, now=lambda: NOW)
    key = "private/checkpoints/iml.json.gz"
    _, version = store.read(key)
    store.write(key, b"invalid gzip", expected=version)
    result = collect_all(Config(), store,
                         adapters={"iml": lambda *_: payload(("B",)),
                                   "xfer": lambda *_: payload(("C",))},
                         now=lambda: NOW + timedelta(minutes=15))
    assert result["status"] == "success"
    assert read_json(store, key)[0]["seen_ids"] == ["A", "B"]


def test_unrecoverable_source_archive_does_not_block_other_source(tmp_path):
    store = LocalStore(tmp_path)
    collect_all(Config(), store, adapters={"iml": lambda *_: payload()}, now=lambda: NOW)
    for key in ("private/checkpoints/iml.json.gz", observation_key("iml", NOW)):
        _, version = store.read(key)
        store.write(key, b"invalid gzip", expected=version)
    result = collect_all(Config(), store,
                         adapters={"iml": lambda *_: payload(), "xfer": lambda *_: payload()},
                         now=lambda: NOW + timedelta(minutes=15))
    assert result["sources"]["iml"]["status"] == "failed"
    assert result["sources"]["xfer"]["status"] == "success"


def test_public_index_recovery_and_explicit_rebuild_preserve_archive(tmp_path):
    store = LocalStore(tmp_path)
    for n in range(2):
        collect_all(Config(), store, adapters={"iml": lambda *_: payload()},
                    now=lambda: NOW + timedelta(minutes=15 * n))
    originals = {k: store.read(k)[0] for k in store.keys("private/observations/")}
    _, version = store.read("public/index.json")
    store.write("public/index.json", b"not json", expected=version)
    collect_all(Config(), store, adapters={"iml": lambda *_: payload()},
                now=lambda: NOW + timedelta(minutes=30))
    assert len(read_json(store, "public/index.json")[0]["sources"]["iml"]["history"]) == 3
    with store.lease(renewable=True):
        rebuilt = rebuild_index(store, now=NOW + timedelta(minutes=30))
    assert len(rebuilt["sources"]["iml"]["history"]) == 3
    assert all(store.read(k)[0] == raw for k, raw in originals.items())
