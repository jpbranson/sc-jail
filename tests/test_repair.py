from datetime import datetime, timedelta, timezone

import pytest

from sc_jail.config import Config
from sc_jail.history import reconstruct_state
from sc_jail.pipeline import collect_all
from sc_jail.repair import MARKER, backup_key, repair_xfer_headers
from sc_jail.storage import LocalStore, read_json
from sc_jail.xfer import REQUIRED, is_heading_record

NOW = datetime(2026, 9, 19, 8, tzinfo=timezone.utc)


def seed(store):
    rows = [{h: "" for h in REQUIRED} | {"Booking #": "TEST-01", "Inmate Name": "TEST PERSON"}]
    # Real duplicates must survive; headings may contain surrounding whitespace.
    rows = rows * 2 + [dict(zip(REQUIRED, [" " + h + " " for h in REQUIRED]))] * 3
    for i in range(3):
        payload = {
            "metrics": {"population": 2, "charge_rows": 5},
            "active_ids": ["TEST-01", "Booking #"],
            "seen_ids": ["TEST-01", "Booking #"],
            "source_updated_at": None,
            "records": rows,
            "artifacts": [("test.xls", b"raw")],
            "source_url": "https://example.test",
        }
        collect_all(
            Config(),
            store,
            adapters={"xfer": lambda *_: payload},
            now=lambda: NOW + timedelta(minutes=i * 15),
        )
    return store.keys("private/observations/xfer/")


def test_repair_corrects_all_counts_preserves_duplicates_and_originals(tmp_path):
    store = LocalStore(tmp_path)
    keys = seed(store)
    originals = {k: store.read(k)[0] for k in keys}
    result = repair_xfer_headers(store)
    assert result["heading_rows_removed"] == 9
    assert result["latest_population"] == 1
    for key in keys:
        state = reconstruct_state(store, key)
        assert len(state["records"]) == 2
        assert not any(is_heading_record(r) for r in state["records"])
        assert state["active_ids"] == ["TEST-01"]
        assert store.read(backup_key(key))[0] == originals[key]
    index, _ = read_json(store, "public/index.json")
    for i, point in enumerate(index["sources"]["xfer"]["history"]):
        assert point["population"] == 1 and point["people_or_bookings_seen"] == 1
        assert point["charge_rows"] == 2
        assert point["departures"] == (None if i == 0 else 0)
    assert repair_xfer_headers(store)["already_complete"]


@pytest.mark.parametrize(
    "fail_prefix", ["private/observations/xfer/", "private/checkpoints/", "public/index"]
)
def test_repair_resumes_after_partial_replacement(tmp_path, monkeypatch, fail_prefix):
    store = LocalStore(tmp_path)
    keys = seed(store)
    write = store.write
    failures = []

    def fail(key, *args, **kwargs):
        if key.startswith(fail_prefix):
            failures.append(key)
            if len(failures) == (2 if "observations" in fail_prefix else 1):
                raise OSError("test interrupted repair")
        return write(key, *args, **kwargs)

    monkeypatch.setattr(store, "write", fail)
    with pytest.raises(OSError):
        repair_xfer_headers(store)
    assert read_json(store, MARKER)[0]["phase"] == "rewrite"
    monkeypatch.setattr(store, "write", write)
    assert repair_xfer_headers(store)["observations_repaired"] == 3
    assert reconstruct_state(store, keys[-1])["active_ids"] == ["TEST-01"]
