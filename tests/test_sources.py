from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from sc_jail import iml, xfer
from sc_jail.config import Config
from sc_jail.http import SourceError

NOW = datetime(2026, 9, 19, 8, 0, tzinfo=timezone.utc)


def page(start, total, ids, release=""):
    rows = []
    for ident in ids:
        cells = [
            f"<a class=\"underlined\" href=\"javascript:submitInmate('{ident}','')\">TEST PERSON</a>",
            f"BK{ident}",
            f"P{ident}",
            "01/01/1990",
            release,
        ]
        rows.append("<tr>" + "".join(f"<td>{v}</td>" for v in cells) + "</tr>")
    return f"Showing {start} to {start + len(ids) - 1} of {total} results<table>{''.join(rows)}</table>"


def test_iml_page_uses_links_not_table_number():
    html = "<table><tr><td>Unrelated layout</td></tr></table>" + page(1, 3, [1, 2])
    start, end, total, records = iml.parse_page(html)
    assert (start, end, total, len(records)) == (1, 2, 3, 2)


@pytest.mark.parametrize(
    "html",
    [
        "<html>Service unavailable</html>",
        "Showing 1 to 30 of 30 results",
        page(1, 1, [1], release="not a date"),
    ],
)
def test_iml_rejects_error_partial_or_changed_dates(html):
    with pytest.raises(SourceError):
        iml.parse_page(html)


def test_iml_pagination_includes_first_and_last(monkeypatch):
    class Session:
        def __init__(self, *a, **kw):
            self.responses = iter(["form", page(1, 3, [1, 2]), page(3, 3, [3])])

        def __enter__(self):
            return self

        def __exit__(self, *a):
            pass

        def request(self, *a, **kw):
            return SimpleNamespace(text=next(self.responses))

    monkeypatch.setattr(iml, "SourceHTTP", Session)
    result = iml.collect(Config(page_delay=0), NOW)
    assert result["metrics"]["population"] == 3
    assert result["metrics"]["pages"] == 2


@pytest.mark.parametrize("last", [page(3, 4, [3, 4]), page(3, 3, [1])])
def test_iml_rejects_shifted_or_duplicate_results(monkeypatch, last):
    class Session:
        def __init__(self, *a, **kw):
            self.responses = iter(["form", page(1, 3, [1, 2]), last])

        def __enter__(self):
            return self

        def __exit__(self, *a):
            pass

        def request(self, *a, **kw):
            return SimpleNamespace(text=next(self.responses))

    monkeypatch.setattr(iml, "SourceHTTP", Session)
    with pytest.raises(SourceError):
        iml.collect(Config(page_delay=0), NOW)


def test_iml_uses_its_own_budget_and_reports_partial_progress(monkeypatch):
    budgets = []

    class Session:
        def __init__(self, *args, **kwargs):
            budgets.append(kwargs["budget"])
            self.responses = iter(["form", page(1, 3, [1, 2])])

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def request(self, *args, **kwargs):
            try:
                return SimpleNamespace(text=next(self.responses))
            except StopIteration:
                raise SourceError("Source collection exceeded its time budget") from None

    monkeypatch.setattr(iml, "SourceHTTP", Session)
    with pytest.raises(SourceError, match="1 pages, 2/3 records"):
        iml.collect(Config(page_delay=0, source_timeout=100, iml_timeout=360), NOW)
    assert budgets == [360]


def test_iml_concurrent_pages_are_consumed_in_order(monkeypatch):
    import threading

    later_finished = threading.Event()
    offsets = []

    class Session:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def request(self, method, path, **kwargs):
            data = kwargs.get("data", {})
            if method == "GET":
                return SimpleNamespace(text="form")
            if data["flow_action"] == "searchbyid":
                return SimpleNamespace(text=page(1, 5, [1, 2]))
            offset = int(data["currentStart"])
            offsets.append(offset)
            if offset == 3:
                assert later_finished.wait(2)
                return SimpleNamespace(text=page(3, 5, [3, 4]))
            assert offset == 5
            later_finished.set()
            return SimpleNamespace(text=page(5, 5, [5]))

    monkeypatch.setattr(iml, "SourceHTTP", Session)
    result = iml.collect(Config(page_delay=0), NOW)
    assert set(offsets) == {3, 5}
    assert [row["result_id"] for row in result["records"]] == ["1", "2", "3", "4", "5"]
    assert result["metrics"]["population"] == 5
    assert result["metrics"]["pages"] == 3


def test_iml_timeout_is_configurable_and_bounded(monkeypatch):
    monkeypatch.setenv("SCJ_IML_TIMEOUT_SECONDS", "450")
    assert Config.from_env().iml_timeout == 450
    assert Config.from_env().source_timeout == 240
    monkeypatch.setenv("SCJ_IML_PAGE_WORKERS", "1")
    assert Config.from_env().iml_page_workers == 1
    for value in (0, 3, 1.5, True):
        with pytest.raises(ValueError):
            Config(iml_page_workers=value)
    for value in (0, -1, float("inf"), float("nan"), 481):
        with pytest.raises(ValueError):
            Config(iml_timeout=value)


def test_release_dates_and_duplicate_people_use_memphis_day():
    rows = [
        {"permanent_id": "A", "booking_number": "1", "release_date": ""},
        {"permanent_id": "A", "booking_number": "2", "release_date": ""},
        {"permanent_id": "B", "booking_number": "3", "release_date": "2026-09-18"},
        {"permanent_id": "C", "booking_number": "4", "release_date": "2026-09-19"},
    ]
    # 01:00 UTC is still September 18 in Memphis.
    metrics, active, _ = iml.summarize(rows, datetime(2026, 9, 19, 1, tzinfo=timezone.utc))
    assert metrics["population"] == 2
    assert active == ["A", "C"]


def test_xfer_workbook_counts_bookings_not_charge_rows():
    records, bookings = xfer.parse_workbook(Path("tests/fixtures/injail.xls").read_bytes())
    assert len(records) == 3
    assert bookings == ["TEST-BK-1", "TEST-BK-2"]
    assert records[0]["DOB"].startswith("1990-01-01")


@pytest.mark.parametrize("raw", [b"<html>login</html>", b"", b"not excel"])
def test_xfer_rejects_non_workbooks(raw):
    with pytest.raises((SourceError, ValueError)):
        xfer.parse_workbook(raw)


def listing(path="%2FSCSO-InJail%2FSCSO-InJail.xls"):
    return f"""<response><files><file><FileName>SCSO-InJail.xls</FileName>
    <FileSize>123</FileSize><FileDate>1789803254</FileDate><FilePath>{path}</FilePath>
    <FileIsDir>0</FileIsDir></file></files><hidden><ErrorResponse>0</ErrorResponse></hidden></response>""".encode()


def test_listing_decodes_paths_and_checks_success():
    assert (
        xfer.parse_listing(listing(), "/SCSO-InJail")[0]["path"] == "/SCSO-InJail/SCSO-InJail.xls"
    )
    with pytest.raises(SourceError):
        xfer.parse_listing(
            listing().replace(b"<ErrorResponse>0", b"<ErrorResponse>1"), "/SCSO-InJail"
        )


def test_listing_cannot_escape_requested_directory():
    with pytest.raises(SourceError):
        xfer.parse_listing(listing("%2Fother%2FSCSO-InJail.xls"), "/SCSO-InJail")


def test_changed_content_same_metadata_is_always_downloaded(monkeypatch):
    binary = Path("tests/fixtures/injail.xls").read_bytes()
    calls = []

    class Session:
        def __init__(self, *a, **kw):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            pass

        def request(self, method, path, **kw):
            calls.append(kw["params"]["Command"])
            data = {
                "Login": b"<response><result>0</result></response>",
                "List": listing().replace(b"<FileSize>123", f"<FileSize>{len(binary)}".encode()),
                "Download": binary,
            }[kw["params"]["Command"]]
            return SimpleNamespace(content=data)

    monkeypatch.setattr(xfer, "SourceHTTP", Session)
    xfer.collect(Config(), NOW)
    xfer.collect(Config(), NOW, {"unchanged": True})
    assert calls.count("Download") == 2


def test_xfer_skips_repeated_full_headers_without_deduplicating_real_rows():
    records, bookings = xfer.parse_workbook(
        Path("tests/fixtures/injail-repeated-headings.xls").read_bytes()
    )
    assert len(records) == 3
    assert bookings == ["TEST-BK-1", "TEST-BK-2"]
    assert not any(xfer.is_heading_record(row) for row in records)
