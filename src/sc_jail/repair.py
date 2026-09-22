"""Correct derived XFER history while retaining raw reports and original manifests."""

import gzip
import json
from datetime import datetime

from .history import (
    HistoryError,
    cached_state,
    canonical_state,
    make_history,
    replay_history,
    restore_observation,
)
from .pipeline import delta_metrics
from .storage import read_json, write_json
from .xfer import is_heading_record

MARKER = "private/maintenance/xfer-headers.json"
BACKUP = "private/repairs/xfer-headers-v1/"


def backup_key(key):
    return BACKUP + key.removeprefix("private/")


class OriginalArchive:
    def __init__(self, store, keys):
        self.store, self.keys = store, set(keys)

    def read(self, key):
        if key in self.keys:
            raw, version = self.store.read(backup_key(key))
            if raw is None:
                raise HistoryError("Original XFER manifest backup is missing")
            return raw, version
        return self.store.read(key)


def repair_xfer_headers(store):
    """All backups precede replacements; interrupted repairs replay originals."""
    with store.lease():
        marker, marker_version = read_json(store, MARKER, {})
        if marker.get("phase") == "complete":
            return {**marker["report"], "already_complete": True}
        if not marker:
            marker = {
                "phase": "backup",
                "keys": [
                    k for k in store.keys("private/observations/xfer/") if k.endswith(".json.gz")
                ],
            }
            marker_version = write_json(store, MARKER, marker, expected=marker_version)
        if marker["phase"] == "backup":
            for key in marker["keys"]:
                raw, _ = store.read(key)
                if raw is None:
                    raise HistoryError("XFER observation disappeared during repair")
                store.write(backup_key(key), raw, create_only=True)
                if store.read(backup_key(key))[0] != raw:
                    raise HistoryError("XFER repair backup conflicts with original")
            public, _ = store.read("public/index.json")
            if public is not None:
                store.write(BACKUP + "public-index.json", public, create_only=True)
            marker["phase"] = "rewrite"
            marker_version = write_json(store, MARKER, marker, expected=marker_version)
        original = OriginalArchive(store, marker["keys"])
        old_previous = new_previous = None
        points = {}
        report = {"observations_repaired": 0, "heading_rows_removed": 0}
        for key in marker["keys"]:
            raw, _ = original.read(key)
            manifest = json.loads(gzip.decompress(raw))
            before = restore_observation(original, key, manifest, old_previous)
            rows = [r for r in before["records"] if not is_heading_record(r)]
            ids = sorted({str(r["Booking #"]).strip() for r in rows})
            if not ids or not all(ids):
                raise HistoryError("XFER repair produced invalid booking IDs")
            removed = len(before["records"]) - len(rows)
            after = canonical_state(rows, ids, ids)
            slot = datetime.fromisoformat(manifest["point"]["slot"])
            observed = datetime.fromisoformat(manifest["point"]["observed_at"])
            seen = sorted(set(new_previous["seen_ids"] if new_previous else []) | set(ids))
            point = {
                **manifest["point"],
                "population": len(ids),
                "charge_rows": len(rows),
                "people_or_bookings_seen": len(seen),
                "heading_rows_removed": removed,
                **delta_metrics(new_previous, ids, observed, slot),
            }
            replacement = {
                "schema": 2,
                "source": "xfer",
                "source_url": manifest["source_url"],
                "point": point,
                "artifacts": manifest["artifacts"],
                "corrections": ["xfer_repeated_headers_v1"],
                "history": make_history(store, "xfer", slot, after, new_previous),
            }
            restored = replay_history(
                store, replacement["history"], new_previous["state"] if new_previous else None
            )
            if restored != after:
                raise HistoryError("Corrected XFER history failed verification")
            current, version = read_json(store, key)
            if current != replacement:
                write_json(store, key, replacement, expected=version)
            old_previous = cached_state(
                key, manifest, before, old_previous["seen_ids"] if old_previous else []
            )
            new_previous = cached_state(key, replacement, after, seen)
            points[point["slot"]] = point
            report["observations_repaired"] += 1
            report["heading_rows_removed"] += removed
        if new_previous:
            checkpoint_key = "private/checkpoints/xfer.json.gz"
            checkpoint, version = read_json(store, checkpoint_key, {})
            if checkpoint.get("slot", "") > new_previous["slot"]:
                raise HistoryError("XFER cache advanced during repair")
            write_json(store, checkpoint_key, new_previous, expected=version)
            index, index_version = read_json(store, "public/index.json", {"sources": {}})
            source = index["sources"].get("xfer")
            if source:
                source["history"] = [points.get(p["slot"], p) for p in source["history"]]
                source["current"] = points[new_previous["slot"]]
                write_json(store, "public/index.json", index, expected=index_version)
            report["latest_population"] = len(new_previous["active_ids"])
            report["latest_charge_rows"] = len(new_previous["state"]["records"])
        marker.update(phase="complete", report=report)
        write_json(store, MARKER, marker, expected=marker_version)
        return report
