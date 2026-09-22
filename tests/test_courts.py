import csv
import io
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import parse_qs, unquote, urlparse

import pytest

from sc_jail import courts
from sc_jail.config import Config
from sc_jail.history import reconstruct_state
from sc_jail.http import SourceError
from sc_jail.storage import LocalStore, read_json

NOW = datetime(2026, 9, 19, 8, tzinfo=timezone.utc)


def csv_report(extra=False):
    out = io.StringIO(newline="")
    writer = csv.writer(out)
    writer.writerow(courts.CALENDAR_HEADERS)
    row = [
        "SYNTHETIC PERSON",
        "TEST",
        "09/19/2026 09:00 AM",
        "TEST OFFICER",
        "TEST HEARING",
        "Defendant",
        "00123",
        "Criminal",
    ]
    writer.writerow(row)
    if extra:
        writer.writerow(courts.CALENDAR_HEADERS)
        writer.writerow(row)
    return out.getvalue().encode()


def test_csv_reports_preserve_ids_duplicates_and_skip_repeated_headers():
    parsed = courts.parse_report(csv_report(True), "criminal_calendar")
    assert len(parsed["records"]) == 2
    assert parsed["records"][0]["Case Number"] == "00123"
    for raw in (b"<html>error</html>", b"Wrong,Columns\n1,2", csv_report() + b"truncated,row\n"):
        with pytest.raises(SourceError):
            courts.parse_report(raw, "gs_calendar")


def test_excel_reports_preserve_blank_columns_and_leading_zero_ids():
    parsed = courts.parse_report(
        Path("tests/fixtures/court-indictments.xls").read_bytes(), "indictments"
    )
    assert len(parsed["records"]) == 2
    assert parsed["records"][0]["Zip"] == "00123"
    assert parsed["records"][0]["_unnamed_column_11"] == "TEST EXTRA VALUE"
    parsed = courts.parse_report(
        Path("tests/fixtures/court-pending.xls").read_bytes(), "pending_hearings"
    )
    assert parsed["records"][0]["Booking Nbr"] == "000123"


def file(name, directory="/CriminalCourtCalendar", modified=NOW):
    return {
        "name": name,
        "path": directory + "/" + name,
        "size": len(csv_report()),
        "modified_at": modified.isoformat(),
        "family": courts.family_for(directory, name),
    }


def test_selective_downloads_detect_metadata_changes_and_recheck_daily():
    item = file("Odyssey-JobOutput-test.txt")
    old = {**item, "checked_at": NOW.isoformat(), "parser_version": courts.PARSER_VERSION}
    assert not courts.is_due(item, old, NOW + timedelta(minutes=15), 24)
    assert courts.is_due(item, old, NOW + timedelta(days=1), 24)
    assert courts.is_due({**item, "size": item["size"] + 1}, old, NOW, 24)
    assert courts.is_due(
        {**item, "modified_at": (NOW + timedelta(seconds=1)).isoformat()}, old, NOW, 24
    )


def test_backfill_covers_each_family_before_older_reports():
    files = [file(f"Odyssey-JobOutput-{i}.txt", modified=NOW + timedelta(days=i)) for i in range(4)]
    files.append(file("Calendar091926.csv", "/GS-Criminalcourtcalendar"))
    queue = courts.download_queue(files, {}, NOW, 24)
    assert {f["family"] for f in queue[:2]} == {"criminal_calendar", "gs_calendar"}
    assert queue[0]["name"] == "Odyssey-JobOutput-3.txt"


def install_http(monkeypatch, *, unsupported=False):
    calls = []
    binary = b"new unsupported format" if unsupported else csv_report()
    name = "Odyssey-JobOutput-September 19, 2026.txt"

    class Session:
        def __init__(self, *args, **kwargs):
            self.deadline = time.monotonic() + 200

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def request(self, method, path, **kwargs):
            if "params" in kwargs:
                params = kwargs["params"]
                command = params["Command"]
            else:
                assert "%20" in path and "+" not in path
                params = {k: v[0] for k, v in parse_qs(urlparse(path).query).items()}
                command = params["Command"]
            calls.append(command)
            if command == "Login":
                raw = b"<response><result>0</result></response>"
            elif command == "List":
                directory = params["Dir"]
                entries = ""
                if directory == "/CriminalCourtCalendar":
                    entries = (
                        f"<file><FileName>{name}</FileName><FilePath>{directory}/{name}</FilePath>"
                        f"<FileSize>{len(binary)}</FileSize><FileDate>{int(NOW.timestamp())}</FileDate>"
                        "<FileIsDir>0</FileIsDir></file>"
                    )
                raw = (
                    f"<response><files>{entries}</files><hidden><ErrorResponse>0</ErrorResponse>"
                    "</hidden></response>"
                ).encode()
            else:
                assert unquote(params["File"]).endswith(name)
                raw = binary
            return SimpleNamespace(content=raw)

    monkeypatch.setattr(courts, "SourceHTTP", Session)
    return calls


def collect(store, moment=NOW):
    return courts.collect_courts(
        Config(), store, moment, deadline=time.monotonic() + 200, now=lambda: moment
    )


def test_court_collection_deduplicates_unchanged_files_and_reconstructs_catalog(
    tmp_path, monkeypatch
):
    store = LocalStore(tmp_path)
    calls = install_http(monkeypatch)
    first = collect(store)
    assert first["parsed_files"] == first["archived_files"] == 1
    assert first["directories"]["/GS-CriminalCourtDispositions"]["status"] == "empty"
    assert collect(store, NOW + timedelta(minutes=15))["downloaded"] == 0
    assert collect(store, NOW + timedelta(days=1))["changed"] == 0
    assert calls.count("Download") == 2
    assert len(store.keys("private/court-reports/")) == 1
    cache, _ = read_json(store, courts.CACHE_KEY)
    assert reconstruct_state(store, cache["manifest_key"]) == cache["state"]


def test_unknown_layout_keeps_raw_with_explicit_unsupported_status(tmp_path, monkeypatch):
    store = LocalStore(tmp_path)
    install_http(monkeypatch, unsupported=True)
    point = collect(store)
    assert point["unsupported_files"] == 1 and point["parsed_files"] == 0
    revision, _ = read_json(store, store.keys("private/court-reports/")[0])
    assert revision["normalized"] is None and revision["raw"]["sha256"]
    assert revision["status"] == "unsupported"


def test_court_retry_reuses_committed_manifest(tmp_path, monkeypatch):
    store = LocalStore(tmp_path)
    calls = install_http(monkeypatch)
    write = store.write
    failed = []

    def fail(key, *args, **kwargs):
        if key == courts.CACHE_KEY and not failed:
            failed.append(True)
            raise OSError("interrupted cache")
        return write(key, *args, **kwargs)

    monkeypatch.setattr(store, "write", fail)
    with pytest.raises(OSError):
        collect(store)
    monkeypatch.setattr(store, "write", write)
    assert collect(store)["parsed_files"] == 1
    assert calls.count("Download") == 1
