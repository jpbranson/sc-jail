"""Distinct observed IML bookings per permanent ID; only aggregates are public."""

import time
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from statistics import median
from zoneinfo import ZoneInfo

from .history import (
    HistoryError,
    observation_key,
    reconstruct_state,
    replay_history,
    restore_observation,
)
from .storage import read_json, write_json

CACHE_KEY = "private/analytics/repeat-visits.json.gz"
CHICAGO = ZoneInfo("America/Chicago")
GAP_BINS = (
    ("Same day", 0),
    ("1–7 days", 7),
    ("8–30 days", 30),
    ("31–90 days", 90),
    ("91–365 days", 365),
    ("366+ days", float("inf")),
)


def _date(value, *, detail=False):
    if not value:
        return None
    try:
        parsed = datetime.strptime(value, "%m/%d/%Y").date() if detail else date.fromisoformat(value)
        return parsed.isoformat()
    except (TypeError, ValueError):
        return None


def record_roster(registry, records, observed_at):
    """Seeing the same booking again, even after a gap, never creates a visit."""
    for row in records:
        person, booking = row["permanent_id"], row["booking_number"]
        if not person or not booking:
            raise HistoryError("Repeat-visit identity is missing")
        visit = registry["visits"].setdefault(
            booking,
            {
                "person_ids": [person],
                "first_seen_at": observed_at,
                "commitment_date": None,
                "release_date": None,
            },
        )
        visit["person_ids"] = sorted(set(visit["person_ids"]) | {person})
        visit["first_seen_at"] = min(visit["first_seen_at"], observed_at)
        # A correction can remove a previously reported release date.
        visit["release_date"] = _date(row.get("release_date"))


def record_details(registry, records, observed_at):
    for row in records:
        visit = registry["visits"].get(row["booking_number"])
        if visit is None:
            continue
        person = row["permanent_id"]
        visit["person_ids"] = sorted(set(visit["person_ids"]) | {person})
        start = _date(row.get("incarceration", {}).get("Commitment Date"), detail=True)
        observed_date = datetime.fromisoformat(observed_at).astimezone(CHICAGO).date().isoformat()
        visit["commitment_date"] = start if start and start <= observed_date else None


def summarize_visits(registry):
    # Conflicting identities cannot safely establish either person-level counts or intervals.
    conflicted = {
        person
        for visit in registry["visits"].values()
        if len(visit["person_ids"]) != 1
        for person in visit["person_ids"]
    }
    people = defaultdict(list)
    excluded = 0
    for visit in registry["visits"].values():
        if any(person in conflicted for person in visit["person_ids"]):
            excluded += 1
        else:
            people[visit["person_ids"][0]].append(visit)
    frequencies = Counter(len(visits) for visits in people.values())
    repeat_people = sum(count for visits, count in frequencies.items() if visits > 1)
    repeat_bookings = sum(visits * count for visits, count in frequencies.items() if visits > 1)
    gaps, missing, invalid = [], 0, 0
    for visits in people.values():
        if len(visits) < 2:
            continue
        # Do not guess the order or bridge an unknown booking in a person's history.
        if any(not visit["commitment_date"] for visit in visits):
            missing += len(visits) - 1
            continue
        ordered = sorted(visits, key=lambda visit: visit["commitment_date"])
        for previous, current in zip(ordered, ordered[1:]):
            release = previous["release_date"]
            if release is None:
                missing += 1
                continue
            start = current["commitment_date"]
            if (
                previous["commitment_date"] >= start
                or release < previous["commitment_date"]
                or release > start
            ):
                invalid += 1
                continue
            gaps.append((date.fromisoformat(start) - date.fromisoformat(release)).days)
    interval_distribution = [{"label": label, "count": 0} for label, _ in GAP_BINS]
    for gap in gaps:
        for bucket, (_, upper) in zip(interval_distribution, GAP_BINS, strict=True):
            if gap <= upper:
                bucket["count"] += 1
                break
    return {
        "available": bool(registry.get("coverage_start")),
        "coverage_start": registry.get("coverage_start"),
        "through": registry.get("through"),
        "people_seen": len(people),
        "bookings_seen": sum(visits * count for visits, count in frequencies.items()),
        "people_once": frequencies[1],
        "repeat_people": repeat_people,
        "repeat_bookings": repeat_bookings,
        "additional_visits": repeat_bookings - repeat_people,
        "max_visits": max(frequencies, default=0),
        "visit_distribution": [
            {"label": f"{visits} visits", "count": frequencies[visits]} for visits in (2, 3, 4)
        ] + [{"label": "5+ visits", "count": sum(n for visits, n in frequencies.items() if visits >= 5)}],
        "interval_distribution": interval_distribution,
        "measured_intervals": len(gaps),
        "missing_date_intervals": missing,
        "invalid_date_intervals": invalid,
        "median_days_between_visits": median(gaps) if gaps else None,
        "excluded_bookings": excluded,
    }


def _new_keys(store, source, cursor, latest):
    prefix = f"private/observations/{source}/"
    if not cursor:
        return [key for key in store.keys(prefix) if key.endswith(".json.gz") and key <= latest]
    if cursor["key"] > latest:
        raise HistoryError("Repeat-visit history moved backwards; rebuild the aggregate")
    if cursor["key"] == latest:
        return []
    # Routine refresh lists only the days since the last processed observation.
    start = datetime.strptime(cursor["key"][len(prefix):][:10], "%Y/%m/%d").date()
    end = datetime.strptime(latest[len(prefix):][:10], "%Y/%m/%d").date()
    keys = []
    while start <= end:
        keys.extend(store.keys(f"{prefix}{start:%Y/%m/%d}/"))
        start += timedelta(days=1)
    return sorted(key for key in keys if key.endswith(".json.gz") and cursor["key"] < key <= latest)


def refresh_repeat_visits(store, *, deadline=None, rebuild=False):
    """Run under the collector lease. Backfill once, then consume only new observations."""
    registry, version = read_json(store, CACHE_KEY)
    if rebuild or registry is None:
        registry = {"schema": 1, "visits": {}, "cursors": {}, "coverage_start": None, "through": None}
    if registry.get("schema") != 1:
        raise HistoryError("Unsupported repeat-visit cache schema")
    changed = rebuild
    for source, ingest in (("iml", record_roster), ("iml_details", record_details)):
        current, _ = read_json(store, f"private/checkpoints/{source}.json.gz")
        if not current:
            continue
        cursor = registry["cursors"].get(source)
        state = None
        for key in _new_keys(store, source, cursor, current["manifest_key"]):
            if deadline is not None and time.monotonic() >= deadline - 5:
                raise TimeoutError("Repeat-visit refresh deferred by the execution budget")
            manifest, _ = read_json(store, key)
            if (
                not manifest
                or manifest["source"] != source
                or key != observation_key(source, manifest["point"]["slot"])
            ):
                raise HistoryError("Repeat-visit observation identity is invalid")
            history = manifest.get("history", {})
            linked = cursor and history.get("previous") == cursor["key"]
            if history.get("kind") == "unchanged" and linked:
                if (
                    history["before_sha256"] != cursor["state_sha256"]
                    or history["state_sha256"] != cursor["state_sha256"]
                ):
                    raise HistoryError("Repeat-visit history checksum does not match")
            else:
                if key == current["manifest_key"]:
                    # The current cache avoids replaying an entire day's large detail history.
                    state = restore_observation(store, key, manifest, current)
                elif state is not None and linked:
                    state = replay_history(store, history, state)
                else:
                    state = reconstruct_state(store, key, manifest=manifest)
                ingest(registry, state["records"], manifest["point"]["observed_at"])
            cursor = {"key": key, "state_sha256": history.get("state_sha256")}
            registry["cursors"][source] = cursor
            if source == "iml":
                stamp = manifest["point"]["observed_at"]
                registry["coverage_start"] = registry["coverage_start"] or stamp
                registry["through"] = stamp
            changed = True
    summary = summarize_visits(registry)
    if changed:
        write_json(store, CACHE_KEY, registry, expected=version)
    return summary
