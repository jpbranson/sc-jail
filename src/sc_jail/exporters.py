"""Private, provenance-rich record exports; never mounted on the public app."""

import gzip
import hashlib
import json

from .history import MAX_CHAIN, HistoryError, observation_key, reconstruct_state
from .storage import read_json


def archived_json(store, reference):
    raw, _ = store.read(reference["key"])
    if raw is None:
        raise HistoryError("Export blob is missing")
    content = gzip.decompress(raw)
    if hashlib.sha256(content).hexdigest() != reference["sha256"]:
        raise HistoryError("Export blob checksum failed")
    return json.loads(content)


def detail_checks_at(store, key):
    chain = []
    for _ in range(MAX_CHAIN):
        manifest, _ = read_json(store, key)
        if not manifest or manifest["source"] != "iml_details":
            raise HistoryError("Detail freshness history is missing")
        chain.append(manifest["checks"])
        if manifest["history"]["kind"] == "checkpoint":
            break
        previous = manifest["history"]["previous"]
        if previous >= key or previous.rsplit("/", 1)[0] != key.rsplit("/", 1)[0]:
            raise HistoryError("Detail freshness history has an invalid link")
        key = previous
    else:
        raise HistoryError("Detail freshness history exceeds one day")
    checks = {}
    for update in reversed(chain):
        checks.update(update)
    return checks


def export_details(store, *, slot=None, booking=None, case=None):
    if slot:
        key = observation_key("iml_details", slot)
        state = reconstruct_state(store, key)
        checks = detail_checks_at(store, key)
        manifest, _ = read_json(store, key)
        stamp = manifest["point"]["slot"]
    else:
        cache, _ = read_json(store, "private/checkpoints/iml_details.json.gz", {})
        if not cache:
            return
        # Validate the cache against its committed manifest before exporting.
        from .history import restore_observation

        manifest, _ = read_json(store, cache["manifest_key"])
        state = restore_observation(store, cache["manifest_key"], manifest, cache)
        checks, stamp = cache["checks"], cache["slot"]
    for record in state["records"]:
        if booking and record["booking_number"] != booking:
            continue
        if case and not any(r.get("Case #") == case for r in record["charges"] + record["bonds"]):
            continue
        yield {
            "source": "iml_details",
            "observation_slot": stamp,
            **record,
            "retrieval": checks.get(record["booking_number"], {}),
        }


def report_inventory(store, *, slot=None, family=None, all_versions=False):
    if all_versions:
        if slot:
            raise ValueError("Choose either an observation slot or all report versions")
        prefix = "private/court-reports/" + (family + "/" if family else "")
        for key in store.keys(prefix):
            if key.endswith(".json.gz"):
                revision, _ = read_json(store, key)
                yield key, revision
        return
    if slot:
        state = reconstruct_state(store, observation_key("xfer_courts", slot))
    else:
        cache, _ = read_json(store, "private/checkpoints/xfer_courts.json.gz", {})
        if not cache:
            return
        from .history import restore_observation

        manifest, _ = read_json(store, cache["manifest_key"])
        state = restore_observation(store, cache["manifest_key"], manifest, cache)
    selected = {}
    for record in state["records"]:
        if "revision_key" not in record or (family and record["family"] != family):
            continue
        old = selected.get(record["family"])
        if old is None or (record["modified_at"], record["name"]) > (
            old["modified_at"],
            old["name"],
        ):
            selected[record["family"]] = record
    for record in selected.values():
        revision, _ = read_json(store, record["revision_key"])
        if revision is None:
            raise HistoryError("Court report revision is missing")
        # The content version may have been seen under older file metadata.
        revision = {
            **revision,
            "file": {
                **revision["file"],
                **{k: record[k] for k in ("name", "path", "modified_at", "size")},
            },
            "checked_at": record["checked_at"],
        }
        yield record["revision_key"], revision


def export_courts(store, *, slot=None, family=None, all_versions=False, booking=None, case=None):
    for key, revision in report_inventory(
        store, slot=slot, family=family, all_versions=all_versions
    ):
        if revision["status"] != "parsed":
            # An explicit inventory record makes quarantined formats visible.
            yield {
                "source": "xfer_courts",
                "report": revision["file"],
                "revision_key": key,
                "status": revision["status"],
                "error": revision["error"],
                "raw": revision["raw"],
                "record": None,
            }
            continue
        parsed = archived_json(store, revision["normalized"])
        for record in parsed["records"]:
            if booking and record.get("Booking Nbr", record.get("Booking #")) != booking:
                continue
            if case and record.get("Case Number", record.get("Case #")) != case:
                continue
            yield {
                "source": "xfer_courts",
                "report": revision["file"],
                "revision_key": key,
                "first_captured_at": revision["observed_at"],
                "last_checked_at": revision.get("checked_at"),
                "raw_sha256": revision["raw"]["sha256"],
                "record": record,
            }
