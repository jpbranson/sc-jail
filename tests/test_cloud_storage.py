import json

import pytest
from google.api_core.exceptions import NotFound, PreconditionFailed

from sc_jail.storage import Conflict, GCSStore, read_json, write_json


class Bucket:
    def __init__(self):
        self.objects = {}
        self.version = 0

    def blob(self, key):
        bucket = self

        class Blob:
            generation = None

            def reload(self, **kwargs):
                if key not in bucket.objects:
                    raise NotFound("not present")
                self.generation = bucket.objects[key][1]

            def download_as_bytes(self, if_generation_match, **kwargs):
                data, version = bucket.objects[key]
                if version != if_generation_match:
                    raise PreconditionFailed("changed")
                return data

            def upload_from_string(self, data, if_generation_match, **kwargs):
                old = bucket.objects.get(key)
                if (old[1] if old else 0) != if_generation_match:
                    raise PreconditionFailed("changed")
                bucket.version += 1
                self.generation = bucket.version
                bucket.objects[key] = (data, self.generation)

        return Blob()


def store(bucket):
    result = GCSStore.__new__(GCSStore)
    result.bucket = bucket
    result._lease_expires = None
    result._retry = None
    return result


def test_gcs_generation_checks_and_immutable_dedup():
    client = store(Bucket())
    version = write_json(client, "public/a.json", {"n": 1})
    assert read_json(client, "public/a.json")[0] == {"n": 1}
    with pytest.raises(Conflict):
        write_json(client, "public/a.json", {"n": 2}, expected=version + 1)
    client.write("private/blob", b"first", create_only=True)
    client.write("private/blob", b"second", create_only=True)
    assert client.read("private/blob")[0] == b"first"


def test_gcs_concurrent_collector_is_rejected():
    bucket = Bucket()
    one, two = store(bucket), store(bucket)
    with one.lease():
        with pytest.raises(Conflict):
            with two.lease():
                pytest.fail("Both collectors acquired the lease")
    with two.lease():
        assert two._lease_expires is not None


def test_expired_owner_cannot_commit_or_release_new_owner(monkeypatch):
    clock = [1000.0]
    monkeypatch.setattr("sc_jail.storage.time.time", lambda: clock[0])
    bucket = Bucket()
    one, two = store(bucket), store(bucket)
    first = one.lease()
    first.__enter__()
    clock[0] = 1700.0
    second = two.lease()
    second.__enter__()
    with pytest.raises(Conflict):
        write_json(one, "public/index.json", {})
    first.__exit__(None, None, None)
    assert json.loads(two.read("private/collector-lease.json")[0])["expires"] > clock[0]
    second.__exit__(None, None, None)


def test_checkpoint_history_and_migration_use_cloud_objects():
    from datetime import datetime, timedelta, timezone
    from types import SimpleNamespace

    from sc_jail.history import canonical_state, observation_key, reconstruct_state
    from sc_jail.migration import migrate_archive
    from sc_jail.storage import archive_blob, encode

    bucket = Bucket()
    bucket.list_blobs = lambda prefix, **kwargs: (
        SimpleNamespace(name=key) for key in bucket.objects if key.startswith(prefix)
    )
    client = store(bucket)
    moment = datetime(2026, 9, 19, 8, tzinfo=timezone.utc)
    expected = {}
    for i in range(3):
        when = moment + timedelta(minutes=15 * i)
        rows = [{"id": f"TEST-{n:04}", "value": n} for n in range(200)]
        if i:
            rows[0]["value"] = 999
        normalized = canonical_state(rows, ["A"], ["A"])
        key = observation_key("iml", when)
        manifest = {
            "schema": 1,
            "source": "iml",
            "source_url": "https://example.test",
            "point": {"slot": when.isoformat(), "observed_at": when.isoformat()},
            "artifacts": [],
            "active_ids": ["A"],
            "observed_ids": ["A"],
            "records": archive_blob(client, "iml-records.json", encode(rows)),
        }
        write_json(client, key, manifest, create_only=True)
        expected[key] = normalized
    report = migrate_archive(client)
    assert report["manifests_converted"] == 3
    assert report["kinds"] == {"checkpoint": 1, "delta": 1, "unchanged": 1}
    for key, normalized in expected.items():
        assert reconstruct_state(client, key) == normalized
    assert migrate_archive(client)["manifests_converted"] == 0


def test_maintenance_renews_lease_and_releases_latest_generation(monkeypatch):
    clock = [1000.0]
    monkeypatch.setattr("sc_jail.storage.time.time", lambda: clock[0])
    bucket = Bucket()
    one, two = store(bucket), store(bucket)
    with one.lease(renewable=True):
        clock[0] = 1500.0
        write_json(one, "public/test.json", {})
        clock[0] = 1700.0
        with pytest.raises(Conflict), two.lease():
            pass
        assert one._lease_expires == 2160.0
    with two.lease():
        assert two._lease_expires > clock[0]
