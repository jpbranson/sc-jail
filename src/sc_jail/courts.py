"""Incremental collection of the public XFER criminal court report folders."""

import csv
import hashlib
import io
import re
import time
from collections import defaultdict
from datetime import datetime, timedelta
from urllib.parse import quote, urlencode

import xlrd

from .archive import advance_checkpoint, reconcile_source
from .excel import identifier
from .history import (
    canonical_state,
    make_history,
    observation_key,
    restore_observation,
)
from .http import SourceError, SourceHTTP
from .provenance import provenance
from .storage import archive_blob, encode, read_json, write_json
from .xfer import URL, parse_listing, xml_response

CACHE_KEY = "private/checkpoints/xfer_courts.json.gz"
PARSER_VERSION = 1
DIRECTORIES = (
    "/GS-Criminalcourtcalendar",
    "/CriminalCourtCalendar",
    "/StateCriminalCourtCalendar",
    "/GS-CriminalCourtDispositions",
)
CALENDAR_HEADERS = [
    "Party Name",
    "Hearing Location",
    "Hearing Date/Time",
    "Judicial Officer",
    "Hearing Type",
    "Connection Type",
    "Case Number",
    "Case Type",
]
INDICTMENT_HEADERS = [
    "Case Number",
    "Location",
    "Judge",
    "Next Hearing",
    "Cross Reference Numbers",
    "IndictmentDate",
    "Defendant",
    "Address",
    "City",
    "State",
    "",
    "Zip",
    "Offenses",
]
PENDING_HEADERS = [
    "Case Number",
    "Def Name",
    "Booking Nbr",
    "Indictment",
    "AGNumber",
    "Offense",
    "Hearing Date",
    "Start Time",
    "Hearing Type",
    "Judicial Officer",
    "Court Session",
    "Attorney",
]


def family_for(directory, name):
    if directory == "/GS-CriminalCourtDispositions":
        return "gs_dispositions"
    if directory == "/GS-Criminalcourtcalendar" and re.fullmatch(r"Calendar\d+\.csv", name, re.I):
        return "gs_calendar"
    if (
        directory == "/CriminalCourtCalendar"
        and name.startswith("Odyssey-JobOutput-")
        and name.endswith(".txt")
    ):
        return "criminal_calendar"
    if directory == "/StateCriminalCourtCalendar":
        if name.startswith("CriminalCourtDailyIndictment_") and name.endswith(".xls"):
            return "indictments"
        if name.startswith("CriminalCourtPendingHearings_") and name.endswith(".xls"):
            return "pending_hearings"
    return "unrecognized"


def _excel_values(book, sheet, index):
    result = []
    for cell in sheet.row(index):
        if cell.ctype == xlrd.XL_CELL_DATE:
            value = xlrd.xldate_as_datetime(cell.value, book.datemode).isoformat()
        elif cell.ctype == xlrd.XL_CELL_ERROR:
            raise SourceError("Court workbook contains an Excel error cell")
        elif cell.ctype == xlrd.XL_CELL_NUMBER:
            value = identifier(book, cell) if cell.value >= 0 and cell.value == int(cell.value) else str(
                cell.value
            )
        else:
            value = str(cell.value)
        result.append(value.strip())
    return result


def _normalize_rows(rows, expected=None):
    rows = [row for row in rows if any(str(v).strip() for v in row)]
    header_at = next(
        (
            i
            for i, row in enumerate(rows[:10])
            if any(str(v).strip() in {"Case Number", "Case #"} for v in row)
        ),
        None,
    )
    if header_at is None:
        raise SourceError("Court report has no recognized case-number heading")
    headers = [str(v).strip() for v in rows[header_at]]
    if expected is not None and headers != expected:
        raise SourceError("Court report column headings changed")
    names = [h if h else f"_unnamed_column_{i + 1}" for i, h in enumerate(headers)]
    if len(set(names)) != len(names):
        raise SourceError("Court report has ambiguous duplicate column headings")
    records = []
    for values in rows[header_at + 1 :]:
        values = [str(v).strip() for v in values]
        if values == headers:
            continue
        if len(values) != len(names):
            raise SourceError("Court report has a truncated or changed row")
        records.append(dict(zip(names, values, strict=True)))
    return {"columns": names, "records": records}


def parse_report(content, family):
    if family == "unrecognized":
        raise SourceError("Unrecognized court report filename or family")
    if content.startswith(bytes.fromhex("d0cf11e0a1b11ae1")):
        try:
            # County exports sometimes have a short final OLE sector; xlrd accepts
            # them. Preserve the original bytes and suppress its noisy warning.
            book = xlrd.open_workbook(
                file_contents=content, on_demand=True, formatting_info=True, logfile=io.StringIO()
            )
        except xlrd.XLRDError as exc:
            raise SourceError("Court report is not a readable XLS workbook") from exc
        try:
            if book.nsheets != 1:
                raise SourceError("Court report sheet structure changed")
            sheet = book.sheet_by_index(0)
            if sheet.nrows > 500_000 or sheet.ncols > 100:
                raise SourceError("Court report dimensions exceed supported limits")
            expected = {"indictments": INDICTMENT_HEADERS, "pending_hearings": PENDING_HEADERS}.get(
                family
            )
            if expected is None and family != "gs_dispositions":
                raise SourceError("Court report file format changed")
            return _normalize_rows(
                [_excel_values(book, sheet, i) for i in range(sheet.nrows)], expected
            )
        finally:
            book.release_resources()
    if family not in {"gs_calendar", "criminal_calendar", "gs_dispositions"}:
        raise SourceError("Court report file format changed")
    if b"<html" in content[:1000].lower() or b"<!doctype" in content[:1000].lower():
        raise SourceError("Court download returned an HTML error page")
    try:
        decoded = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        decoded = content.decode("cp1252")
    try:
        rows = list(csv.reader(io.StringIO(decoded, newline=""), strict=True))
    except csv.Error as exc:
        raise SourceError("Court report is not valid CSV") from exc
    expected = CALENDAR_HEADERS if family in {"gs_calendar", "criminal_calendar"} else None
    return _normalize_rows(rows, expected)


def login(session):
    response = session.request(
        "POST",
        "/Web%20Client/Login.xml",
        params={"Command": "Login"},
        data={"user": "public", "pword": "public", "language": "en,US"},
    )
    if xml_response(response.content).findtext("result") != "0":
        raise SourceError("XFER public login did not confirm success")


def download(session, file):
    if not 0 < file["size"] <= 25_000_000:
        raise SourceError("Court report size is outside the supported range")
    # Serv-U does not interpret '+' as a space in Download filenames.
    query = urlencode({"Command": "Download", "File": file["path"]}, quote_via=quote)
    response = session.request("GET", "/?" + query)
    if len(response.content) != file["size"]:
        raise SourceError("Court report size differs from its directory listing")
    if b"<html" in response.content[:1000].lower():
        raise SourceError("Court report download returned an HTML error page")
    return response.content


def is_due(file, previous, moment, hours):
    if not previous or previous.get("parser_version") != PARSER_VERSION:
        return True
    if previous.get("size") != file["size"] or previous.get("modified_at") != file["modified_at"]:
        return True
    checked = previous.get("checked_at")
    return not checked or moment - datetime.fromisoformat(checked) >= timedelta(hours=hours)


def download_queue(files, old, moment, hours):
    groups = defaultdict(list)
    for file in files:
        previous = old.get(file["path"], {})
        failed = previous.get("failed_at")
        if failed and moment - datetime.fromisoformat(failed) < timedelta(hours=1):
            continue
        if is_due(file, previous, moment, hours):
            groups[file["family"]].append(file)
    # Cover the newest report in each family before working through the backlog.
    for group in groups.values():
        group.sort(key=lambda f: (f["modified_at"], f["name"]), reverse=True)
    ordered = []
    while groups:
        for family in sorted(list(groups)):
            ordered.append(groups[family].pop(0))
            if not groups[family]:
                del groups[family]
    return ordered


def _commit_cache(store, key, manifest, state, previous, version):
    cache = advance_checkpoint("xfer_courts", key, manifest, state, previous)
    write_json(store, CACHE_KEY, cache, expected=version)
    return manifest["point"]


def collect_courts(config, store, slot, *, deadline, now):
    previous, version = reconcile_source(store, "xfer_courts", slot, deadline=deadline)
    key = observation_key("xfer_courts", slot)
    manifest, _ = read_json(store, key)
    if manifest:
        state = restore_observation(store, key, manifest, previous)
        return _commit_cache(store, key, manifest, state, previous, version)
    moment = now()
    budget = min(config.court_budget, deadline - time.monotonic())
    if budget <= 10 or config.court_batch <= 0:
        raise SourceError("Court collection deferred by the execution budget")
    old = {r["path"]: r for r in previous.get("state", {}).get("records", [])}
    current, directories, artifacts = dict(old), {}, []
    downloads = changed = failures = 0
    with SourceHTTP(URL, user_agent=config.user_agent, budget=budget) as session:
        login(session)
        files = []
        for directory in DIRECTORIES:
            try:
                listing = session.request(
                    "GET",
                    "/Web%20Client/ListError.xml",
                    params={"Command": "List", "Dir": directory},
                )
                entries = parse_listing(listing.content, directory)
                if len(entries) > 2000:
                    raise SourceError("Court directory exceeds the supported file count")
                for file in entries:
                    file["family"] = family_for(directory, file["name"])
                files.extend(entries)
                paths = {f["path"] for f in entries}
                current = {
                    p: r for p, r in current.items() if r["directory"] != directory or p in paths
                }
                for file in entries:
                    if file["path"] not in current:
                        current[file["path"]] = {
                            **file,
                            "directory": directory,
                            "status": "pending",
                        }
                digest = hashlib.sha256(listing.content).hexdigest()
                prior = previous.get("directories", {}).get(directory, {})
                reference = prior.get("listing")
                if not reference or reference["sha256"] != digest:
                    reference = archive_blob(store, "court-listing.xml", listing.content)
                    artifacts.append(reference)
                directories[directory] = {
                    "status": "empty" if not entries else "listed",
                    "files": len(entries),
                    "listing": reference,
                }
            except Exception as exc:
                failures += 1
                directories[directory] = {
                    **previous.get("directories", {}).get(directory, {}),
                    "status": "failed",
                    "error": str(exc)[:200] if isinstance(exc, SourceError) else type(exc).__name__,
                }
        queue = download_queue(files, old, moment, config.court_verify_hours)
        consecutive_failures = 0
        for file in queue[: config.court_batch]:
            if time.monotonic() >= deadline - 5 or time.monotonic() >= session.deadline - 5:
                break
            path = file["path"]
            stamp = now().isoformat()
            try:
                raw = download(session, file)
                downloads += 1
                digest = hashlib.sha256(raw).hexdigest()
                prior = old.get(path, {})
                if (
                    digest == prior.get("content_sha256")
                    and prior.get("parser_version") == PARSER_VERSION
                ):
                    current[path] = {**prior, **file, "checked_at": stamp}
                    current[path].pop("failed_at", None)
                    current[path].pop("error", None)
                    consecutive_failures = 0
                    continue
                reference = archive_blob(store, file["name"], raw)
                try:
                    parsed = parse_report(raw, file["family"])
                    normalized = archive_blob(store, "court-records.json", encode(parsed))
                    status, reason, count = "parsed", None, len(parsed["records"])
                except (SourceError, ValueError, UnicodeError) as exc:
                    normalized, status, count = None, "unsupported", None
                    reason = str(exc)[:200] if isinstance(exc, SourceError) else type(exc).__name__
                path_id = hashlib.sha256(path.encode()).hexdigest()
                revision_key = (
                    f"private/court-reports/{file['family']}/{path_id}/"
                    f"{digest}-v{PARSER_VERSION}.json.gz"
                )
                revision = {
                    "schema": 1,
                    "parser_version": PARSER_VERSION,
                    "provenance": provenance("xfer_courts"),
                    "source_url": URL,
                    "file": file,
                    "observed_at": stamp,
                    "raw": reference,
                    "normalized": normalized,
                    "status": status,
                    "rows": count,
                    "error": reason,
                }
                write_json(store, revision_key, revision, create_only=True)
                current[path] = {
                    **file,
                    "directory": path.rsplit("/", 1)[0],
                    "checked_at": stamp,
                    "content_sha256": digest,
                    "revision_key": revision_key,
                    "parser_version": PARSER_VERSION,
                    "status": status,
                    "rows": count,
                }
                artifacts.append({"revision_key": revision_key, **reference})
                changed += 1
                consecutive_failures = 0
            except Exception as exc:
                failures += 1
                current[path] = {
                    **current[path],
                    "failed_at": stamp,
                    "error": str(exc)[:200] if isinstance(exc, SourceError) else type(exc).__name__,
                }
                consecutive_failures += 1
                if consecutive_failures >= 3:
                    break
    listed = {f["path"]: f for f in files}
    pending = sum(
        is_due(file, current.get(path), moment, config.court_verify_hours)
        for path, file in listed.items()
    )
    point = {
        "slot": slot.isoformat(),
        "observed_at": moment.isoformat(),
        "finished_at": now().isoformat(),
        "listed_files": len(listed),
        "archived_files": sum("revision_key" in r for r in current.values()),
        "parsed_files": sum(r.get("status") == "parsed" for r in current.values()),
        "unsupported_files": sum(r.get("status") == "unsupported" for r in current.values()),
        "downloaded": downloads,
        "changed": changed,
        "pending": pending,
        "failed": failures,
        "verify_hours": config.court_verify_hours,
        "directories": {
            d: {"status": v["status"], "files": v.get("files")} for d, v in directories.items()
        },
    }
    state = canonical_state(
        list(current.values()),
        sorted(current),
        sorted(p for p, r in current.items() if "revision_key" in r),
    )
    manifest = {
        "schema": 2,
        "source": "xfer_courts",
        "source_url": URL,
        "provenance": provenance("xfer_courts"),
        "point": point,
        "artifacts": artifacts,
        "directories": directories,
        "history": make_history(store, "xfer_courts", slot, state, previous),
    }
    write_json(store, key, manifest, create_only=True)
    return _commit_cache(store, key, manifest, state, previous, version)
