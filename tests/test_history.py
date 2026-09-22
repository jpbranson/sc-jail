import copy
from datetime import datetime, timedelta, timezone

import pytest

from sc_jail.history import (
    HistoryError,
    apply_patch,
    cached_state,
    canonical_state,
    make_history,
    make_patch,
    observation_key,
    reconstruct_state,
)
from sc_jail.migration import migrate_archive
from sc_jail.storage import LocalStore, archive_blob, encode, read_json, write_json

NOW = datetime(2026, 9, 19, 8, tzinfo=timezone.utc)


def state():
    rows = [{"booking": f"B{i:04}", "charge": f"SYNTHETIC CHARGE {i}"} for i in range(250)]
    ids = [row["booking"] for row in rows]
    return canonical_state(rows, ids, ids)


def altered(before):
    rows = copy.deepcopy(before["records"])
    rows[0]["charge"] = "SYNTHETIC CORRECTION"
    rows.extend([rows[-1].copy(), rows[-1].copy()])
    return canonical_state(rows, before["active_ids"][1:], before["observed_ids"])


def persist(store, normalized, moment=NOW, previous=None, source="xfer"):
    key = observation_key(source, moment)
    manifest = {
        "schema": 2,
        "source": source,
        "source_url": "https://example.test/",
        "point": {"slot": moment.isoformat(), "observed_at": moment.isoformat()},
        "artifacts": [],
        "history": make_history(store, source, moment, normalized, previous),
    }
    write_json(store, key, manifest, create_only=True)
    return cached_state(key, manifest, normalized, [])


def legacy(store, normalized, moment=NOW, source="xfer"):
    key = observation_key(source, moment)
    manifest = {
        "schema": 1,
        "source": source,
        "source_url": "https://example.test/",
        "point": {"slot": moment.isoformat(), "observed_at": moment.isoformat()},
        "artifacts": [archive_blob(store, "source.xls", b"SYNTHETIC ORIGINAL")],
        "records": archive_blob(store, f"{source}-records.json", encode(normalized["records"])),
        "active_ids": normalized["active_ids"],
        "observed_ids": normalized["observed_ids"],
    }
    write_json(store, key, manifest, create_only=True)
    return key, manifest


def history(store, reference):
    return read_json(store, reference["manifest_key"])[0]["history"]


def test_checkpoints_changes_and_unchanged_round_trip_with_duplicate_rows(tmp_path):
    store = LocalStore(tmp_path)
    original = state()
    one = persist(store, original)
    changed = altered(original)
    two = persist(store, changed, NOW + timedelta(minutes=15), one)
    three = persist(store, changed, NOW + timedelta(minutes=30), two)
    four = persist(store, original, NOW + timedelta(minutes=45), three)
    assert [history(store, item)["kind"] for item in (one, two, three, four)] == [
        "checkpoint",
        "delta",
        "unchanged",
        "delta",
    ]
    for item, expected in ((one, original), (two, changed), (three, changed), (four, original)):
        assert reconstruct_state(store, item["manifest_key"]) == expected
    assert history(store, two)["changes"]["records"]["add"][-1]["count"] == 2
    assert history(store, three)["state_sha256"] == history(store, two)["state_sha256"]


def test_row_order_does_not_create_spurious_change(tmp_path):
    store = LocalStore(tmp_path)
    original = state()
    reordered = canonical_state(
        list(reversed(original["records"])),
        list(reversed(original["active_ids"])),
        original["observed_ids"],
    )
    one = persist(store, original)
    two = persist(store, reordered, NOW + timedelta(minutes=15), one)
    assert history(store, two)["kind"] == "unchanged"


def test_id_set_change_without_record_change_is_preserved(tmp_path):
    store = LocalStore(tmp_path)
    original = state()
    changed = canonical_state(
        original["records"], original["active_ids"][1:], original["observed_ids"]
    )
    one = persist(store, original)
    two = persist(store, changed, NOW + timedelta(minutes=15), one)
    assert history(store, two)["kind"] == "delta"
    assert history(store, two)["changes"]["records"] == {"add": [], "remove": []}
    assert reconstruct_state(store, two["manifest_key"]) == changed


def test_next_utc_day_starts_an_independent_checkpoint(tmp_path):
    store = LocalStore(tmp_path)
    one = persist(store, state(), NOW.replace(hour=23, minute=45))
    two = persist(store, state(), NOW.replace(hour=0) + timedelta(days=1), one)
    assert history(store, two)["kind"] == "checkpoint"
    store.path(one["manifest_key"]).unlink()
    assert reconstruct_state(store, two["manifest_key"]) == state()


def test_large_change_uses_a_cheaper_checkpoint(tmp_path):
    store = LocalStore(tmp_path)
    one = persist(store, state())
    empty = canonical_state([], [], [])
    two = persist(store, empty, NOW + timedelta(minutes=15), one)
    assert history(store, two)["kind"] == "checkpoint"
    assert reconstruct_state(store, two["manifest_key"]) == empty


def test_full_day_chain_reconstructs_and_a_gap_remains_a_real_gap(tmp_path):
    store = LocalStore(tmp_path)
    previous = None
    normalized = state()
    midnight = NOW.replace(hour=0)
    for interval in range(96):
        previous = persist(store, normalized, midnight + timedelta(minutes=15 * interval), previous)
    assert reconstruct_state(store, previous["manifest_key"]) == normalized
    gap_store = LocalStore(tmp_path / "gap")
    first = persist(gap_store, normalized)
    after = persist(gap_store, altered(normalized), NOW + timedelta(hours=4), first)
    assert reconstruct_state(gap_store, after["manifest_key"]) == altered(normalized)
    assert len(gap_store.keys("private/observations/")) == 2


@pytest.mark.parametrize("field", ["before_sha256", "state_sha256"])
def test_bad_chain_hash_is_rejected(tmp_path, field):
    store = LocalStore(tmp_path)
    one = persist(store, state())
    two = persist(store, altered(state()), NOW + timedelta(minutes=15), one)
    manifest, version = read_json(store, two["manifest_key"])
    manifest["history"][field] = "0" * 64
    write_json(store, two["manifest_key"], manifest, expected=version)
    with pytest.raises(HistoryError, match="checksum"):
        reconstruct_state(store, two["manifest_key"])


@pytest.mark.parametrize("damage", ["missing", "corrupt", "wrong_hash"])
def test_checkpoint_blob_damage_is_rejected(tmp_path, damage):
    store = LocalStore(tmp_path)
    one = persist(store, state())
    blob = store.path(history(store, one)["data"]["key"])
    if damage == "missing":
        blob.unlink()
    elif damage == "corrupt":
        blob.write_bytes(b"not gzip")
    else:
        import gzip

        blob.write_bytes(gzip.compress(b"{}"))
    with pytest.raises(HistoryError):
        reconstruct_state(store, one["manifest_key"])


def test_missing_prior_observation_and_cross_day_link_are_rejected(tmp_path):
    store = LocalStore(tmp_path)
    one = persist(store, state())
    two = persist(store, altered(state()), NOW + timedelta(minutes=15), one)
    store.path(one["manifest_key"]).unlink()
    with pytest.raises(HistoryError, match="missing"):
        reconstruct_state(store, two["manifest_key"])
    manifest, version = read_json(store, two["manifest_key"])
    manifest["history"]["previous"] = observation_key("xfer", NOW - timedelta(days=1))
    write_json(store, two["manifest_key"], manifest, expected=version)
    with pytest.raises(HistoryError, match="crosses"):
        reconstruct_state(store, two["manifest_key"])


@pytest.mark.parametrize("count", [0, -1, 10000, True])
def test_invalid_removal_counts_are_rejected(count):
    before = state()
    patch = make_patch(before, altered(before))
    patch["records"]["remove"][0]["count"] = count
    with pytest.raises(HistoryError):
        apply_patch(before, patch)


def test_unknown_row_removal_is_rejected():
    before = state()
    patch = make_patch(before, altered(before))
    patch["records"]["remove"][0]["sha256"] = "0" * 64
    with pytest.raises(HistoryError):
        apply_patch(before, patch)


def test_bad_working_cache_is_rejected(tmp_path):
    store = LocalStore(tmp_path)
    one = persist(store, state())
    one["state"]["records"][0]["charge"] = "DAMAGED CACHE"
    with pytest.raises(HistoryError, match="checksum"):
        make_history(store, "xfer", NOW + timedelta(minutes=15), state(), one)


def test_legacy_observations_remain_readable(tmp_path):
    store = LocalStore(tmp_path)
    key, _ = legacy(store, altered(state()))
    assert reconstruct_state(store, key) == altered(state())


def test_migration_verifies_history_retains_originals_and_is_idempotent(tmp_path):
    store = LocalStore(tmp_path)
    expected, originals = {}, {}
    for source in ("iml", "xfer"):
        for i in range(4):
            normalized = state() if i < 2 else altered(state())
            key, manifest = legacy(store, normalized, NOW + timedelta(minutes=15 * i), source)
            expected[key] = normalized
            originals[key] = store.read(key)[0]
            for ref in [manifest["records"], *manifest["artifacts"]]:
                originals[ref["key"]] = store.read(ref["key"])[0]
    first = migrate_archive(store)
    assert first["observations_verified"] == 8
    assert first["manifests_converted"] == 8
    assert first["kinds"] == {"checkpoint": 2, "delta": 2, "unchanged": 4}
    for key, normalized in expected.items():
        assert reconstruct_state(store, key) == normalized
        manifest = read_json(store, key)[0]
        assert "active_ids" not in manifest and "records" not in manifest
        backup_key = key.replace("private/observations/", "private/legacy/observations/")
        assert store.read(backup_key)[0] == originals[key]
    for key, raw in originals.items():
        if key.startswith("private/blobs/"):
            assert store.read(key)[0] == raw
    assert read_json(store, "private/checkpoints/xfer.json.gz")[0]["state"] == altered(state())
    assert migrate_archive(store)["manifests_converted"] == 0
    assert migrate_archive(store, verify_only=True)["observations_verified"] == 8


def test_migration_resumes_after_interruption_without_losing_originals(tmp_path, monkeypatch):
    store = LocalStore(tmp_path)
    first, _ = legacy(store, state())
    second, _ = legacy(store, altered(state()), NOW + timedelta(minutes=15))
    real_write = store.write

    def interrupted(key, *args, **kwargs):
        if key == second and not kwargs.get("create_only"):
            raise OSError("SYNTHETIC INTERRUPTION")
        return real_write(key, *args, **kwargs)

    monkeypatch.setattr(store, "write", interrupted)
    with pytest.raises(OSError):
        migrate_archive(store)
    assert read_json(store, first)[0]["schema"] == 2
    assert read_json(store, second)[0]["schema"] == 1
    monkeypatch.setattr(store, "write", real_write)
    assert migrate_archive(store)["manifests_converted"] == 1
    assert reconstruct_state(store, second) == altered(state())


def test_verify_only_leaves_legacy_archive_untouched(tmp_path):
    store = LocalStore(tmp_path)
    key, _ = legacy(store, state())
    before = store.keys("private/")
    assert migrate_archive(store, verify_only=True)["observations_verified"] == 1
    assert store.keys("private/") == before
    assert read_json(store, key)[0]["schema"] == 1


@pytest.mark.parametrize(
    "slot", ["2026-09-19T08:01:00Z", "2026-09-19T08:00:01Z", "2026-09-19T08:00"]
)
def test_reconstruction_requires_an_exact_timezone_aware_slot(slot):
    with pytest.raises(ValueError):
        observation_key("xfer", slot)


def test_unchanged_chain_checks_its_checksum(tmp_path):
    store = LocalStore(tmp_path)
    one = persist(store, state())
    two = persist(store, state(), NOW + timedelta(minutes=15), one)
    manifest, version = read_json(store, two["manifest_key"])
    manifest["history"]["state_sha256"] = "0" * 64
    write_json(store, two["manifest_key"], manifest, expected=version)
    with pytest.raises(HistoryError, match="checksum"):
        reconstruct_state(store, two["manifest_key"])


def test_conflicting_migration_backup_prevents_replacement(tmp_path):
    store = LocalStore(tmp_path)
    key, _ = legacy(store, state())
    backup_key = key.replace("private/observations/", "private/legacy/observations/")
    store.write(backup_key, b"CONFLICTING BACKUP", create_only=True)
    with pytest.raises(HistoryError, match="backup differs"):
        migrate_archive(store)
    assert read_json(store, key)[0]["schema"] == 1
    assert reconstruct_state(store, key) == state()
