"""Daily normalized checkpoints and verified, duplicate-preserving change logs."""

import gzip
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone

from .storage import archive_blob, encode, read_json

MAX_CHAIN = 96
STATE_FIELDS = ("records", "active_ids", "observed_ids")


class HistoryError(RuntimeError):
    """Missing or inconsistent private history; never include source rows in errors."""


def observation_key(source, slot):
    if not re.fullmatch(r"[a-z][a-z0-9_-]*", source):
        raise ValueError("Invalid source name")
    if isinstance(slot, str):
        slot = datetime.fromisoformat(slot)
    if slot.tzinfo is None:
        raise ValueError("Observation time must include a timezone")
    slot = slot.astimezone(timezone.utc)
    if slot.minute % 15 or slot.second or slot.microsecond:
        raise ValueError("Observation time must be a quarter-hour boundary")
    return f"private/observations/{source}/{slot:%Y/%m/%d/%H%M}.json.gz"


def canonical_state(records, active_ids, observed_ids):
    if not isinstance(records, list) or any(not isinstance(row, dict) for row in records):
        raise HistoryError("Normalized records must be a list of objects")
    if any(
        not isinstance(ids, list) or any(not isinstance(value, str) for value in ids)
        for ids in (active_ids, observed_ids)
    ):
        raise HistoryError("Observation IDs must be lists of strings")
    # A row's position has no meaning; multiplicity does, especially for XFER charges.
    return {
        "records": sorted(records, key=encode),
        "active_ids": sorted(set(active_ids)),
        "observed_ids": sorted(set(observed_ids)),
    }


def state_hash(state):
    return hashlib.sha256(encode(state)).hexdigest()


def _verified_state(state, expected):
    if (
        not isinstance(state, dict)
        or set(state) != set(STATE_FIELDS)
        or canonical_state(**state) != state
        or state_hash(state) != expected
    ):
        raise HistoryError("Normalized state checksum or structure is invalid")
    return state


def _read_blob(store, reference):
    digest = reference["sha256"]
    if reference["key"] != f"private/blobs/{digest[:2]}/{digest}.gz":
        raise HistoryError("Invalid history blob reference")
    raw, _ = store.read(reference["key"])
    if raw is None:
        raise HistoryError("History blob is missing")
    try:
        content = gzip.decompress(raw)
        if hashlib.sha256(content).hexdigest() != digest:
            raise HistoryError("History blob checksum does not match")
        return json.loads(content)
    except (OSError, EOFError, ValueError) as exc:
        raise HistoryError("History blob is unreadable") from exc


def _row_inventory(records):
    rows, counts = {}, Counter()
    for row in records:
        digest = hashlib.sha256(encode(row)).hexdigest()
        if digest in rows and rows[digest] != row:
            raise HistoryError("Conflicting normalized row hashes")
        rows[digest] = row
        counts[digest] += 1
    return rows, counts


def _set_changes(old, new):
    before, after = set(old), set(new)
    return {"add": sorted(after - before), "remove": sorted(before - after)}


def make_patch(before, after):
    _, old = _row_inventory(before["records"])
    rows, new = _row_inventory(after["records"])
    return {
        "records": {
            "add": [
                {"row": rows[key], "count": count} for key, count in sorted((new - old).items())
            ],
            "remove": [
                {"sha256": key, "count": count} for key, count in sorted((old - new).items())
            ],
        },
        "active_ids": _set_changes(before["active_ids"], after["active_ids"]),
        "observed_ids": _set_changes(before["observed_ids"], after["observed_ids"]),
    }


def apply_patch(before, patch):
    """Apply a multiset patch; an edited row is a removal plus an addition."""
    rows, counts = _row_inventory(before["records"])
    try:
        touched = set()
        for entry in patch["records"]["remove"]:
            digest, count = entry["sha256"], entry["count"]
            if type(count) is not int or count <= 0 or counts[digest] < count or digest in touched:
                raise HistoryError("Change log removes missing or invalid rows")
            counts[digest] -= count
            touched.add(digest)
        touched = set()
        for entry in patch["records"]["add"]:
            row, count = entry["row"], entry["count"]
            if not isinstance(row, dict) or type(count) is not int or count <= 0:
                raise HistoryError("Change log adds invalid rows")
            digest = hashlib.sha256(encode(row)).hexdigest()
            if digest in touched or (digest in rows and rows[digest] != row):
                raise HistoryError("Change log has conflicting row additions")
            rows[digest] = row
            counts[digest] += count
            touched.add(digest)
        restored = [rows[key] for key, count in counts.items() for _ in range(count)]
        ids = {}
        for name in ("active_ids", "observed_ids"):
            added, removed = patch[name]["add"], patch[name]["remove"]
            if (
                any(not isinstance(value, str) for value in added + removed)
                or len(set(added)) != len(added)
                or len(set(removed)) != len(removed)
                or set(added) & set(removed)
                or set(added) & set(before[name])
                or not set(removed) <= set(before[name])
            ):
                raise HistoryError("Change log contains inconsistent ID changes")
            ids[name] = sorted((set(before[name]) - set(removed)) | set(added))
        return canonical_state(restored, **ids)
    except (KeyError, TypeError, ValueError) as exc:
        raise HistoryError("Change log structure is invalid") from exc


def make_history(store, source, slot, state, previous=None):
    """Archive a daily baseline, or embed a small patch in the observation."""
    key = observation_key(source, slot)
    digest = state_hash(state)
    _verified_state(state, digest)
    checkpoint = previous is None or "state" not in previous
    if not checkpoint:
        old = _verified_state(previous["state"], previous["state_sha256"])
        previous_key = observation_key(source, previous["slot"])
        if previous_key != previous["manifest_key"] or previous_key >= key:
            raise HistoryError("Previous observation is not earlier in this source")
        checkpoint = previous_key.rsplit("/", 1)[0] != key.rsplit("/", 1)[0]
        if not checkpoint:
            history = {
                "kind": "unchanged" if digest == previous["state_sha256"] else "delta",
                "previous": previous_key,
                "before_sha256": previous["state_sha256"],
                "state_sha256": digest,
            }
            if history["kind"] == "delta":
                history["changes"] = make_patch(old, state)
                if apply_patch(old, history["changes"]) != state:
                    raise HistoryError("Generated change log failed reconstruction")
                # A major schema/report change can be cheaper as a new checkpoint.
                checkpoint = len(gzip.compress(encode(history), mtime=0)) >= len(
                    gzip.compress(encode(state), mtime=0)
                )
            if not checkpoint:
                return history
    return {
        "kind": "checkpoint",
        "state_sha256": digest,
        "data": archive_blob(store, f"{source}-state.json", encode(state)),
    }


def replay_history(store, history, previous=None):
    kind = history.get("kind")
    if kind == "checkpoint":
        return _verified_state(_read_blob(store, history["data"]), history["state_sha256"])
    if kind not in {"delta", "unchanged"} or previous is None:
        raise HistoryError("Change log has no valid checkpoint")
    _verified_state(previous, history["before_sha256"])
    state = apply_patch(previous, history["changes"]) if kind == "delta" else previous
    return _verified_state(state, history["state_sha256"])


def reconstruct_state(store, key, *, manifest=None):
    """Reconstruct a v1 or v2 observation, checking every link (at most one day)."""
    chain, visited = [], set()
    current_key, current = key, manifest
    try:
        while True:
            if current_key in visited or len(visited) >= MAX_CHAIN:
                raise HistoryError("History is cyclic or exceeds one day")
            visited.add(current_key)
            if current is None:
                current, _ = read_json(store, current_key)
            if current is None:
                raise HistoryError("Observation in history chain is missing")
            source, slot = current["source"], current["point"]["slot"]
            if current_key != observation_key(source, slot):
                raise HistoryError("Observation identity does not match its key")
            if current.get("schema") == 1:
                state = canonical_state(
                    _read_blob(store, current["records"]),
                    current["active_ids"],
                    current["observed_ids"],
                )
                break
            if current.get("schema") != 2:
                raise HistoryError("Unsupported observation schema")
            history = current["history"]
            if history["kind"] == "checkpoint":
                state = replay_history(store, history)
                break
            previous_key = history["previous"]
            if (
                previous_key >= current_key
                or previous_key.rsplit("/", 1)[0] != current_key.rsplit("/", 1)[0]
            ):
                raise HistoryError("Change log crosses a source/day or points forward")
            chain.append(history)
            current_key, current = previous_key, None
        digest = state_hash(state)
        for history in reversed(chain):
            if history["kind"] == "unchanged":
                # The already-verified state is identical; avoid rehashing thousands
                # of rows once per unchanged poll when replaying a full day.
                if history["before_sha256"] != digest or history["state_sha256"] != digest:
                    raise HistoryError("Normalized state checksum does not match")
            else:
                state = replay_history(store, history, state)
                digest = history["state_sha256"]
        return state
    except HistoryError:
        raise
    except (KeyError, TypeError, ValueError, OSError, EOFError) as exc:
        raise HistoryError("Observation history is invalid or unreadable") from exc


def restore_observation(store, key, manifest, previous=None):
    """Use the verified working cache for retries or sequential archive scans."""
    if key != observation_key(manifest["source"], manifest["point"]["slot"]):
        raise HistoryError("Observation identity does not match its key")
    history = manifest.get("history", {})
    if manifest.get("schema") == 2 and previous and "state" in previous:
        if previous["manifest_key"] == key:
            return _verified_state(previous["state"], history["state_sha256"])
        if (
            history.get("previous") == previous["manifest_key"]
            and key.rsplit("/", 1)[0] == previous["manifest_key"].rsplit("/", 1)[0]
            and key > previous["manifest_key"]
        ):
            return replay_history(store, history, previous["state"])
    return reconstruct_state(store, key, manifest=manifest)


def cached_state(manifest_key, manifest, state, seen_ids):
    """Mutable current state bounds routine collection to one cloud state read."""
    return {
        "slot": manifest["point"]["slot"],
        "observed_at": manifest["point"]["observed_at"],
        "active_ids": state["active_ids"],
        "seen_ids": sorted(set(seen_ids) | set(state["observed_ids"])),
        "manifest_key": manifest_key,
        "state_sha256": state_hash(state),
        "state": state,
    }
