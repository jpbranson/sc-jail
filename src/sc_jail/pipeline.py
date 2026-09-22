import logging
import time
from dataclasses import replace
from datetime import datetime, timedelta, timezone

from . import iml, xfer
from .history import (
    cached_state,
    canonical_state,
    make_history,
    observation_key,
    restore_observation,
)
from .http import SourceError
from .storage import archive_blob, read_json, write_json

log = logging.getLogger(__name__)
SOURCES = {"iml": iml.collect, "xfer": xfer.collect}


def utc_now():
    return datetime.now(timezone.utc)


def slot_for(moment):
    moment = moment.astimezone(timezone.utc)
    return moment.replace(minute=(moment.minute // 15) * 15, second=0, microsecond=0)


def empty_index():
    return {"schema": 1, "created_at": utc_now().isoformat(), "sources": {}}


def delta_metrics(previous, active, observed_at, slot):
    if not previous:
        return {"arrivals": None, "departures": None, "comparison_minutes": None}
    gap = (observed_at - datetime.fromisoformat(previous["observed_at"])).total_seconds()
    adjacent = (slot - datetime.fromisoformat(previous["slot"])).total_seconds() == 900
    if not adjacent or not 0 < gap <= 1200:
        return {"arrivals": None, "departures": None, "comparison_minutes": round(gap / 60, 1)}
    old, new = set(previous["active_ids"]), set(active)
    return {
        "arrivals": len(new - old),
        "departures": len(old - new),
        "comparison_minutes": round(gap / 60, 1),
    }


def collect_all(config, store, *, scheduled_at=None, adapters=None, now=utc_now):
    include_supplements = adapters is None
    adapters = adapters or SOURCES
    observed = now()
    slot = slot_for(scheduled_at or observed)
    # Delayed retries cannot truthfully reconstruct a past quarter-hour.
    if (observed - slot).total_seconds() >= 900 or (observed - slot).total_seconds() < -60:
        return {"status": "expired", "slot": slot.isoformat(), "sources": {}}
    results = {}
    started = time.monotonic()
    with store.lease():
        index, index_version = read_json(store, "public/index.json", empty_index())
        for name, adapter in adapters.items():
            state = index["sources"].setdefault(name, {"history": [], "attempts": []})
            if state.get("last_slot") == slot.isoformat():
                results[name] = {"status": "already_collected"}
                continue
            manifest_key = observation_key(name, slot)
            checkpoint_key = f"private/checkpoints/{name}.json.gz"
            checkpoint, checkpoint_version = read_json(store, checkpoint_key, {})
            attempt_at = now().isoformat()
            try:
                if name == "xfer":
                    repair, _ = read_json(store, "private/maintenance/xfer-headers.json", {})
                    if repair and repair.get("phase") != "complete":
                        raise SourceError("XFER history repair must finish before collection resumes")
                manifest, _ = read_json(store, manifest_key)
                if manifest is None:
                    source_start = now()
                    remaining = started + 540 - time.monotonic()
                    if remaining <= 0:
                        raise SourceError("Population collection reached its shared time budget")
                    source_config = replace(
                        config,
                        source_timeout=min(config.source_timeout, remaining),
                        iml_timeout=min(config.iml_timeout, remaining),
                    )
                    payload = adapter(source_config, source_start, checkpoint)
                    seen = set(checkpoint.get("seen_ids", [])) | set(payload["seen_ids"])
                    point = {
                        "slot": slot.isoformat(),
                        "observed_at": source_start.isoformat(),
                        "finished_at": now().isoformat(),
                        "source_updated_at": payload["source_updated_at"],
                        **payload["metrics"],
                        **delta_metrics(checkpoint, payload["active_ids"], source_start, slot),
                        "people_or_bookings_seen": len(seen),
                    }
                    artifacts = [
                        archive_blob(store, file, data) for file, data in payload["artifacts"]
                    ]
                    normalized = canonical_state(
                        payload["records"], payload["active_ids"], payload["seen_ids"]
                    )
                    manifest = {
                        "schema": 2,
                        "source": name,
                        "source_url": payload["source_url"],
                        "point": point,
                        "artifacts": artifacts,
                        "history": make_history(store, name, slot, normalized, checkpoint),
                    }
                    # Source + storage must finish before a distributed lease can expire.
                    if time.monotonic() - started > 600:
                        raise SourceError("Collection reached its safe execution deadline")
                    write_json(store, manifest_key, manifest, create_only=True)
                else:
                    # A retry may find an immutable observation after a failed state write.
                    normalized = restore_observation(store, manifest_key, manifest, checkpoint)
                point = manifest["point"]
                checkpoint = cached_state(
                    manifest_key, manifest, normalized, checkpoint.get("seen_ids", [])
                )
                write_json(store, checkpoint_key, checkpoint, expected=checkpoint_version)
                state.update(
                    last_slot=slot.isoformat(),
                    last_success=point["finished_at"],
                    current=point,
                    error=None,
                )
                state["history"] = [p for p in state["history"] if p["slot"] != point["slot"]]
                state["history"].append(point)
                state["history"].sort(key=lambda p: p["slot"])
                results[name] = {"status": "success", **point}
                log.info("%s collected: population=%s", name, point["population"])
            except Exception as exc:
                # Log operational failures, never downloaded rows or session cookies.
                log.exception("%s collection failed", name)
                message = (
                    str(exc)
                    if isinstance(exc, SourceError)
                    else f"{type(exc).__name__}: collection failed"
                )
                state["error"] = message[:250]
                write_json(
                    store,
                    f"private/failures/{name}/{slot:%Y/%m/%d}/{now():%H%M%S%f}.json",
                    {"slot": slot.isoformat(), "at": attempt_at, "error": state["error"]},
                    create_only=True,
                )
                results[name] = {"status": "failed", "error": state["error"]}
            state["last_attempt"] = attempt_at
            state["attempts"].append(
                {"at": attempt_at, "slot": slot.isoformat(), "status": results[name]["status"]}
            )
            state["attempts"] = state["attempts"][-192:]
            cutoff = (now() - timedelta(days=config.history_days)).isoformat()
            state["history"] = [p for p in state["history"] if p["observed_at"] >= cutoff]
            index["updated_at"] = now().isoformat()
            index_version = write_json(store, "public/index.json", index, expected=index_version)
        supplementary = {}
        if include_supplements:
            from .supplemental import collect_supplements

            supplementary = collect_supplements(
                config, store, index, slot, deadline=started + 570, now=now
            )
            from .repeats import refresh_repeat_visits

            try:
                index["repeat_visits"] = refresh_repeat_visits(store, deadline=started + 570)
            except Exception:
                log.exception("Repeat-visit aggregate refresh failed")
                index.setdefault("repeat_visits", {})["error"] = (
                    "Repeat-visit refresh is delayed; showing the last completed calculation"
                )
            index["updated_at"] = now().isoformat()
            write_json(store, "public/index.json", index, expected=index_version)
        return {
            "supplements": supplementary,
            "status": "failed"
            if any(r["status"] == "failed" for r in results.values())
            else "success",
            "slot": slot.isoformat(),
            "sources": results,
        }
