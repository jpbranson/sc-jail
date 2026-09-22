"""Resumable conversion of v1 manifests; original objects remain as backups."""

import gzip
import json

from .history import (
    HistoryError,
    cached_state,
    make_history,
    replay_history,
    restore_observation,
)
from .storage import read_json, write_json


def migrate_archive(store, *, verify_only=False):
    """Hold the collector lease; validate each replacement before committing it."""
    report = {"observations_verified": 0, "manifests_converted": 0, "kinds": {}}
    previous_by_source = {}
    with store.lease():
        for key in store.keys("private/observations/"):
            if not key.endswith(".json.gz"):
                continue
            raw, version = store.read(key)
            manifest = json.loads(gzip.decompress(raw))
            source = manifest["source"]
            previous = previous_by_source.get(source)
            state = restore_observation(store, key, manifest, previous)
            if manifest["schema"] == 1 and not verify_only:
                converted = {
                    "schema": 2,
                    "source": source,
                    "source_url": manifest["source_url"],
                    "point": manifest["point"],
                    "artifacts": manifest["artifacts"],
                    "history": make_history(
                        store, source, manifest["point"]["slot"], state, previous
                    ),
                }
                restored = replay_history(
                    store, converted["history"], previous["state"] if previous else None
                )
                if restored != state:
                    raise HistoryError("Migration did not preserve normalized records and IDs")
                backup_key = key.replace("private/observations/", "private/legacy/observations/", 1)
                store.write(backup_key, raw, create_only=True)
                backup, _ = store.read(backup_key)
                if backup != raw:
                    raise HistoryError("Legacy manifest backup differs; refusing replacement")
                write_json(store, key, converted, expected=version)
                manifest = converted
                report["manifests_converted"] += 1
            previous_by_source[source] = cached_state(
                key, manifest, state, previous["seen_ids"] if previous else []
            )
            if "checks" in manifest:
                checks = dict(previous.get("checks", {}) if previous else {})
                checks.update(manifest["checks"])
                active = set(state["active_ids"])
                previous_by_source[source]["checks"] = {k: v for k, v in checks.items() if k in active}
            if "directories" in manifest:
                previous_by_source[source]["directories"] = manifest["directories"]
            kind = manifest.get("history", {}).get("kind", "legacy")
            report["kinds"][kind] = report["kinds"].get(kind, 0) + 1
            report["observations_verified"] += 1
        if not verify_only:
            for source, latest in previous_by_source.items():
                checkpoint_key = f"private/checkpoints/{source}.json.gz"
                checkpoint, version = read_json(store, checkpoint_key, {})
                if checkpoint.get("slot", "") > latest["slot"]:
                    raise HistoryError("Working state is newer than the archive being migrated")
                latest["seen_ids"] = sorted(
                    set(latest["seen_ids"]) | set(checkpoint.get("seen_ids", []))
                )
                write_json(store, checkpoint_key, latest, expected=version)
    return report
