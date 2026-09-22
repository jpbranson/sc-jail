"""Identity-checked IML detail parsing and a bounded, age-based refresh queue."""

import hashlib
import time
from datetime import datetime, timedelta

from bs4 import BeautifulSoup

from .history import (
    cached_state,
    canonical_state,
    make_history,
    observation_key,
    restore_observation,
)
from .http import SourceError, SourceHTTP
from .iml import URL, start_search
from .storage import archive_blob, encode, read_json, write_json

SECTIONS = ("Inmate", "Incarceration", "Alias", "Detainer", "Bond", "Charge", "Hearing")
CHARGE_HEADERS = ["Case #", "Offense Date", "Code", "Description", "Grade", "Degree"]
ALIAS_HEADERS = ["Last Name", "First Name", "Middle Name"]
CACHE_KEY = "private/checkpoints/iml_details.json.gz"


def text(tag):
    return " ".join(tag.get_text(" ", strip=True).split())


def direct_rows(table):
    return [tr for tr in table.find_all("tr") if tr.find_parent("table") is table]


def section_tables(soup):
    sections = {}
    for label in soup.select("td.header"):
        if label.find("table"):
            continue
        title = text(label)
        if title not in {s + " Information" for s in SECTIONS}:
            continue
        table = label.find_parent("table")
        while table and len(direct_rows(table)) < 2:
            table = table.find_parent("table")
        if table is None or title in sections:
            raise SourceError("IML detail section structure changed")
        sections[title] = table
    if set(sections) != {s + " Information" for s in SECTIONS}:
        raise SourceError("IML detail is missing required sections")
    return sections


def section_rows(table):
    rows = []
    for tr in direct_rows(table)[1:]:
        cells = tr.find_all(["td", "th"], recursive=False)
        if any(c.find("table") for c in cells):
            raise SourceError("Unexpected nested table in IML detail section")
        if any(text(c) for c in cells):
            rows.append(cells)
    return rows


def absent(rows):
    return (
        len(rows) == 1
        and len(rows[0]) == 1
        and text(rows[0][0]).lower().startswith(("there is no ", "there are no "))
        and "information" in text(rows[0][0]).lower()
    )


def pairs(cells):
    values = []
    for i, cell in enumerate(cells):
        label = text(cell)
        if "bodysmallbold" in cell.get("class", []) and label.endswith(":"):
            if i + 1 >= len(cells):
                raise SourceError("IML detail has a label without a value")
            values.append((label[:-1].strip(), text(cells[i + 1])))
    return values


def field_groups(rows, *, first_label=None):
    if not rows or absent(rows):
        return []
    groups, current = [], {}
    for cells in rows:
        row_pairs = pairs(cells)
        if not row_pairs:
            raise SourceError("Unrecognized IML detail field row")
        for label, value in row_pairs:
            if current and ((first_label and label == first_label) or label in current):
                groups.append(current)
                current = {}
            current[label] = value
    if current:
        groups.append(current)
    return groups


def single_fields(rows):
    groups = field_groups(rows)
    if len(groups) != 1:
        raise SourceError("IML detail fields are missing or repeated")
    return groups[0]


def tabular(rows, headers=None):
    if not rows or absent(rows):
        return []
    labels = [text(c) for c in rows[0]]
    if headers is not None and labels != headers:
        raise SourceError("IML detail table columns changed")
    if not labels or not all(labels) or len(set(labels)) != len(labels):
        raise SourceError("IML detail table headings are ambiguous")
    records = []
    for cells in rows[1:]:
        values = [text(c) for c in cells]
        if values == labels:
            continue
        if len(values) != len(labels):
            raise SourceError("IML detail table row is incomplete")
        records.append(dict(zip(labels, values, strict=True)))
    return records


def parse_detail(html, expected):
    soup = BeautifulSoup(html, "lxml")
    sections = section_tables(soup)
    rows = {name.split()[0]: section_rows(table) for name, table in sections.items()}
    inmate = single_fields(rows["Inmate"])
    if (
        inmate.get("Booking #") != expected["booking_number"]
        or inmate.get("Permanent ID #") != expected["permanent_id"]
    ):
        raise SourceError("IML detail identity does not match its roster entry")
    physical = {}
    section_ids = {id(table) for table in sections.values()}
    for label in soup.select("td.bodysmallbold"):
        if any(id(parent) in section_ids for parent in label.parents):
            continue
        name = text(label)
        if name.endswith(":"):
            value = label.find_next_sibling("td")
            if value is None or name[:-1] in physical:
                raise SourceError("IML physical-information structure changed")
            physical[name[:-1]] = text(value)
    if "DOB" not in physical or "Sex" not in physical:
        raise SourceError("IML physical information is incomplete")
    bond_rows = rows["Bond"]
    totals, body = {}, []
    for cells in bond_rows:
        fields = pairs(cells)
        if fields and fields[0][0] == "Grand Total":
            totals.update(fields)
        else:
            body.append(cells)
    detainers = rows["Detainer"]
    if not detainers or absent(detainers):
        detainers = []
    elif pairs(detainers[0]):
        detainers = field_groups(detainers)
    else:
        detainers = tabular(detainers)
    names = soup.select(".header .bodywhite")
    if len(names) > 1:
        raise SourceError("IML detail name field is ambiguous")
    record = {
        "booking_number": expected["booking_number"],
        "permanent_id": expected["permanent_id"],
        "name": text(names[0]) if names else expected["name"],
        "physical": physical,
        "inmate": inmate,
        "incarceration": {}
        if absent(rows["Incarceration"])
        else single_fields(rows["Incarceration"]),
        "aliases": tabular(rows["Alias"], ALIAS_HEADERS),
        "charges": tabular(rows["Charge"], CHARGE_HEADERS),
        "bonds": field_groups(body, first_label="Case #"),
        "bond_totals": totals,
        "hearings": field_groups(rows["Hearing"], first_label="Case #"),
        "detainers": detainers,
    }
    # Table order is presentation, while duplicate charges/aliases remain meaningful.
    for field in ("aliases", "charges", "bonds", "hearings", "detainers"):
        record[field].sort(key=encode)
    return record


def roster_hash(row):
    return hashlib.sha256(encode({k: v for k, v in row.items() if k != "result_id"})).hexdigest()


def select_due(roster, checks, moment, refresh_hours):
    pending = []
    for row in roster:
        meta = checks.get(row["booking_number"], {})
        checked = meta.get("checked_at")
        changed = meta.get("roster_sha256") != roster_hash(row)
        old = not checked or moment - datetime.fromisoformat(checked) >= timedelta(
            hours=refresh_hours
        )
        if not changed and not old:
            continue
        attempted = meta.get("failed_at")
        if attempted and moment - datetime.fromisoformat(attempted) < timedelta(hours=1):
            continue
        priority = 0 if checked and changed else 1 if not checked else 2
        pending.append(
            (priority, bool(row["release_date"]), checked or "", row["booking_number"], row)
        )
    return [item[-1] for item in sorted(pending, key=lambda item: item[:-1])]


def _commit_cache(store, key, manifest, state, previous, version):
    cache = cached_state(key, manifest, state, previous.get("seen_ids", []))
    checks = dict(previous.get("checks", {}))
    checks.update(manifest["checks"])
    active = set(state["active_ids"])
    cache["checks"] = {k: v for k, v in checks.items() if k in active}
    write_json(store, CACHE_KEY, cache, expected=version)
    return manifest["point"]


def collect_details(config, store, slot, *, deadline, now):
    previous, version = read_json(store, CACHE_KEY, {})
    key = observation_key("iml_details", slot)
    manifest, _ = read_json(store, key)
    if manifest:
        state = restore_observation(store, key, manifest, previous)
        return _commit_cache(store, key, manifest, state, previous, version)
    roster_cache, _ = read_json(store, "private/checkpoints/iml.json.gz", {})
    moment = now()
    if not roster_cache or moment - datetime.fromisoformat(roster_cache["observed_at"]) > timedelta(
        hours=2
    ):
        raise SourceError("IML detail collection is waiting for a recent complete roster")
    roster = roster_cache["state"]["records"]
    by_id = {r["booking_number"]: r for r in roster}
    if len(by_id) != len(roster):
        raise SourceError("IML detail queue has duplicate booking numbers")
    checks = {k: v for k, v in previous.get("checks", {}).items() if k in by_id}
    records = {
        r["booking_number"]: r
        for r in previous.get("state", {}).get("records", [])
        if r["booking_number"] in by_id
    }
    queue = select_due(roster, checks, moment, config.detail_refresh_hours)
    updates, artifacts = {}, []
    attempted = succeeded = failures = changed = 0
    budget = min(config.detail_budget, deadline - time.monotonic())
    if queue and budget > 10 and config.detail_batch > 0:
        with SourceHTTP(
            "https://imljail.shelbycountytn.gov", user_agent=config.user_agent, budget=budget
        ) as session:
            start_search(session)
            consecutive_failures = 0
            for row in queue[: config.detail_batch]:
                if time.monotonic() >= deadline - 5 or time.monotonic() >= session.deadline - 5:
                    break
                ident = row["booking_number"]
                stamp = now().isoformat()
                meta = dict(checks.get(ident, {}))
                attempted += 1
                response = None
                try:
                    response = session.request(
                        "POST",
                        "/IML",
                        data={"flow_action": "edit", "sysID": row["result_id"], "imgSysID": ""},
                    )
                    record = parse_detail(response.text, row)
                    if records.get(ident) != record:
                        reference = archive_blob(store, "iml-detail.html", response.content)
                        artifacts.append({"booking_number": ident, **reference})
                        meta.update(changed_at=stamp, raw_html=reference)
                        changed += 1
                    records[ident] = record
                    meta.update(checked_at=stamp, roster_sha256=roster_hash(row))
                    meta.pop("failed_at", None)
                    meta.pop("error", None)
                    meta.pop("unparsed_html", None)
                    succeeded += 1
                    consecutive_failures = 0
                except Exception as exc:
                    # IDs/rows and server error pages must not leak into public diagnostics.
                    meta.update(
                        failed_at=stamp,
                        error=(
                            str(exc)[:200] if isinstance(exc, SourceError) else type(exc).__name__
                        ),
                    )
                    if response is not None and isinstance(exc, SourceError):
                        reference = archive_blob(
                            store, "iml-detail-unparsed.html", response.content
                        )
                        meta["unparsed_html"] = reference
                        artifacts.append({"booking_number": ident, "unparsed": True, **reference})
                    failures += 1
                    consecutive_failures += 1
                updates[ident] = meta
                checks[ident] = meta
                if consecutive_failures >= 3:
                    break
                time.sleep(config.page_delay)
    state = canonical_state(list(records.values()), sorted(by_id), sorted(records))
    fresh = sum(
        bool(meta.get("checked_at"))
        and moment - datetime.fromisoformat(meta["checked_at"])
        < timedelta(hours=config.detail_refresh_hours)
        and meta.get("roster_sha256") == roster_hash(by_id[ident])
        for ident, meta in checks.items()
    )
    checked_dates = [m["checked_at"] for m in checks.values() if m.get("checked_at")]
    point = {
        "slot": slot.isoformat(),
        "observed_at": moment.isoformat(),
        "finished_at": now().isoformat(),
        "roster_slot": roster_cache["slot"],
        "eligible": len(by_id),
        "available": len(records),
        "fresh": fresh,
        "pending": len(by_id) - fresh,
        "attempted": attempted,
        "checked": succeeded,
        "changed": changed,
        "failed": failures,
        "oldest_checked_at": min(checked_dates) if checked_dates else None,
        "refresh_hours": config.detail_refresh_hours,
    }
    history = make_history(store, "iml_details", slot, state, previous)
    manifest = {
        "schema": 2,
        "source": "iml_details",
        "source_url": URL,
        "point": point,
        "artifacts": artifacts,
        "checks": checks if history["kind"] == "checkpoint" else updates,
        "history": history,
    }
    write_json(store, key, manifest, create_only=True)
    return _commit_cache(store, key, manifest, state, previous, version)
