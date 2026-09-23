"""Recover mutable projections from the committed observation journal."""

import gzip
import json
import time
from datetime import datetime, timedelta, timezone

from .history import (
    HistoryError,
    cached_state,
    canonical_state,
    observation_key,
    restore_observation,
    state_hash,
)
from .storage import read_json, write_json

SOURCES = ("iml", "xfer", "iml_details", "xfer_courts")


def read_projection(store, key, default):
    """Recover decode failures, but never hide a storage/permission outage."""
    raw, version = store.read(key)
    if raw is None:
        return default, version
    try:
        value = json.loads(gzip.decompress(raw) if key.endswith(".gz") else raw)
        if not isinstance(value, dict):
            raise ValueError("Projection must be an object")
        return value, version
    except (ValueError, OSError, EOFError, UnicodeError):
        return default, version


def observation_keys(store, source, *, after=None, through=None):
    prefix = f"private/observations/{source}/"
    if after is None:
        keys = store.keys(prefix)
    else:
        start = datetime.fromisoformat(after).astimezone(timezone.utc).date()
        end = (through or datetime.now(timezone.utc)).astimezone(timezone.utc).date()
        keys = []
        while start <= end:
            keys.extend(store.keys(f"{prefix}{start:%Y/%m/%d}/"))
            start += timedelta(days=1)
    limit = observation_key(source, through) if through is not None else None
    return sorted(k for k in keys if k.endswith(".json.gz") and (limit is None or k <= limit))


def advance_checkpoint(source, key, manifest, normalized, previous):
    cache = cached_state(key, manifest, normalized, previous.get("seen_ids", []))
    if source == "iml_details":
        checks = {} if manifest["history"]["kind"] == "checkpoint" else dict(
            previous.get("checks", {})
        )
        checks.update(manifest["checks"])
        active = set(normalized["active_ids"])
        cache["checks"] = {k: v for k, v in checks.items() if k in active}
    elif source == "xfer_courts":
        cache["seen_ids"] = normalized["observed_ids"]
        cache["directories"] = manifest["directories"]
    return cache


def publish_point(public, point, *, population=True):
    if population:
        history = {p["slot"]: p for p in public.get("history", [])}
        history[point["slot"]] = point
        public["history"] = [history[k] for k in sorted(history)]
        public.setdefault("attempts", [])
    if point["slot"] < public.get("current", {}).get("slot", ""):
        return
    if population:
        public["last_slot"] = point["slot"]
    public.update(current=point, last_success=point["finished_at"], error=None)
    if not population and point.get("failed"):
        public["error"] = "Some supplemental requests failed; showing the last verified records"
    elif not population and point.get("unsupported_files"):
        public["error"] = "Some court reports need parser support"


def _valid_checkpoint(source, cache):
    try:
        return (
            cache["manifest_key"] == observation_key(source, cache["slot"])
            and canonical_state(**cache["state"]) == cache["state"]
            and state_hash(cache["state"]) == cache["state_sha256"]
            and cache["active_ids"] == cache["state"]["active_ids"]
            and isinstance(cache["seen_ids"], list)
            and all(isinstance(k, str) for k in cache["seen_ids"])
            and (source != "iml_details" or isinstance(cache["checks"], dict))
            and (source != "xfer_courts" or isinstance(cache["directories"], dict))
        )
    except (KeyError, TypeError, ValueError, HistoryError):
        return False


def reconcile_source(store, source, through, *, public=None, rebuild=False, deadline=None):
    """Replay committed work before acquiring new data, including across slot boundaries.

    Caller holds the collector lease. Routine recovery lists only days since the
    oldest projection cursor. Missing/corrupt caches require a verified full replay.
    """
    checkpoint_key = f"private/checkpoints/{source}.json.gz"
    cache, version = read_projection(store, checkpoint_key, {})
    if rebuild or not _valid_checkpoint(source, cache):
        cache = {}
    if cache and cache["slot"] > through.isoformat():
        raise HistoryError("Working state is newer than the requested collection")
    after = cache.get("slot")
    if public is not None:
        published = public.get("current", {}).get("slot")
        after = min(after, published) if after and published else None
    changed = False
    for key in observation_keys(store, source, after=after, through=through):
        if deadline is not None and time.monotonic() >= deadline - 30:
            if changed:
                write_json(store, checkpoint_key, cache, expected=version)
            raise HistoryError("Archive reconciliation will resume in the next collection")
        cache_key = cache.get("manifest_key", "")
        published_key = (
            observation_key(source, public["current"]["slot"])
            if public is not None and public.get("current") else ""
        )
        if key <= cache_key and (public is None or key <= published_key):
            continue
        manifest, _ = read_json(store, key)
        if (not manifest or manifest.get("source") != source
                or key != observation_key(source, manifest["point"]["slot"])):
            raise HistoryError("Committed observation identity is invalid")
        point = manifest["point"]
        if key > cache_key:
            normalized = restore_observation(store, key, manifest, cache)
            cache = advance_checkpoint(source, key, manifest, normalized, cache)
            changed = True
            if source in ("iml", "xfer"):
                point = {**point, "people_or_bookings_seen": len(cache["seen_ids"])}
        if public is not None:
            publish_point(public, point, population=source in ("iml", "xfer"))
    if changed:
        version = write_json(store, checkpoint_key, cache, expected=version)
    return cache, version


def rebuild_index(store, *, history_days=90, now=None):
    """Explicit maintenance entry point; retained observations are never rewritten."""
    now = now or datetime.now(timezone.utc)
    through = now.replace(minute=now.minute // 15 * 15, second=0, microsecond=0)
    index, version = read_projection(store, "public/index.json", {})
    result = {"schema": 1, "created_at": index.get("created_at", now.isoformat()),
              "updated_at": now.isoformat(), "sources": {}, "supplements": {}}
    cutoff = (now - timedelta(days=history_days)).isoformat()
    for source in SOURCES:
        target = result["sources" if source in ("iml", "xfer") else "supplements"]
        target[source] = {}
        reconcile_source(store, source, through, public=target[source], rebuild=True)
        if source in ("iml", "xfer"):
            target[source]["history"] = [
                p for p in target[source].get("history", []) if p["observed_at"] >= cutoff
            ]
    if "repeat_visits" in index:
        result["repeat_visits"] = index["repeat_visits"]
    write_json(store, "public/index.json", result, expected=version)
    return result
