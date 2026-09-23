from datetime import datetime, timedelta, timezone

from sc_jail.config import Config
from sc_jail.storage import LocalStore, write_json
from sc_jail.web import create_app, create_collector_app, source_health


def test_empty_dashboard_csv_and_charts(tmp_path):
    client = create_app(Config(), LocalStore(tmp_path)).test_client()
    assert client.get("/").status_code == 200
    assert b"No data" in client.get("/").data
    assert client.get("/chart/population.svg?width=360").status_code == 200
    assert b"Waiting for consecutive" in client.get("/chart/changes.svg").data
    assert client.get("/history.csv").status_code == 200
    assert client.get("/chart/invalid.svg").status_code == 404
    assert b"is being prepared" in client.get("/chart/repeat-visits.svg?width=360").data
    assert client.get("/chart/visit-intervals.svg?width=invalid").status_code == 200
    assert client.get("/api/repeat-visits").json == {}
    assert client.post("/collect").status_code == 404
    assert client.get("/private/checkpoints/iml.json.gz").status_code == 404


def test_dashboard_has_working_chart_sources_without_javascript(tmp_path):
    from bs4 import BeautifulSoup

    client = create_app(Config(), LocalStore(tmp_path)).test_client()
    page = BeautifulSoup(client.get("/?days=30").data, "html.parser")
    plots = page.select("img.plot")
    assert len(plots) == 4
    for plot in plots:
        response = client.get(plot["src"])
        assert response.status_code == 200
        assert response.mimetype == "image/svg+xml"
        assert "days=30" in plot["src"]
    # Layout and chart initialization arrive atomically with the document.
    assert page.select_one("style").string
    assert not page.select("script[src], link[rel=stylesheet]")


def test_stale_and_failed_states_are_honest():
    now = datetime.now(timezone.utc)
    assert source_health({}, now)[0] == "No data"
    assert (
        source_health({"last_success": (now - timedelta(minutes=31)).isoformat()}, now)[0]
        == "Collection overdue"
    )
    assert (
        source_health({"last_success": now.isoformat(), "error": "failure"}, now)[0]
        == "Collection failed"
    )


def test_public_data_does_not_include_archived_personal_data(tmp_path):
    store = LocalStore(tmp_path)
    write_json(store, "private/test.json", {"name": "PRIVATE TEST NAME"})
    client = create_app(Config(), store).test_client()
    for route in ["/", "/api/status", "/history.csv", "/api/repeat-visits"]:
        assert b"PRIVATE TEST NAME" not in client.get(route).data


def test_corrupt_index_returns_unavailable_not_zero(tmp_path):
    store = LocalStore(tmp_path)
    store.write("public/index.json", b"broken")
    client = create_app(Config(), store).test_client()
    assert client.get("/").status_code == 503
    assert b"Data temporarily unavailable" in client.get("/").data
    assert client.get("/").headers["Cache-Control"] == "no-store"


def test_local_collector_endpoint_is_closed(tmp_path, monkeypatch):
    monkeypatch.delenv("K_SERVICE", raising=False)
    client = create_collector_app(Config(), LocalStore(tmp_path)).test_client()
    assert client.post("/collect").status_code == 403


def test_mobile_chart_labels_stay_inside_svg():
    import re
    from xml.etree import ElementTree as ET

    from sc_jail.web import make_chart

    now = datetime.now(timezone.utc)
    point = {
        "observed_at": now.isoformat(),
        "slot": now.isoformat(),
        "population": 3000,
        "arrivals": 2,
        "departures": 1,
    }
    index = {"sources": {name: {"history": [point]} for name in ("iml", "xfer")}}
    for changes in (False, True):
        svg = make_chart(index, 7, 378, changes=changes)
        root = ET.fromstring(svg)
        _, _, view_width, view_height = map(float, root.attrib["viewBox"].split())
        labels = root.findall(".//{http://www.w3.org/2000/svg}text")
        assert len(labels) > 5
        for label in labels:
            if "y" in label.attrib:
                assert 0 <= float(label.attrib["y"]) <= view_height - 2
            size = re.search(r"font-size: ([\d.]+)px", label.attrib.get("style", ""))
            if size:
                assert float(size.group(1)) * 378 / view_width >= 16 - 0.01
        assert "Arial" in svg


def test_repeat_charts_and_api_render_aggregate_values(tmp_path):
    from sc_jail.repeats import record_details, record_roster, summarize_visits

    store = LocalStore(tmp_path)
    stamp = datetime.now(timezone.utc).isoformat()
    registry = {"visits": {}, "coverage_start": stamp, "through": stamp}
    record_roster(registry, [
        {"permanent_id": "PRIVATE-ID", "booking_number": "PRIVATE-ONE",
         "release_date": "2026-01-02"},
        {"permanent_id": "PRIVATE-ID", "booking_number": "PRIVATE-TWO", "release_date": ""},
    ], stamp)
    record_details(registry, [
        {"permanent_id": "PRIVATE-ID", "booking_number": "PRIVATE-ONE",
         "incarceration": {"Commitment Date": "01/01/2026"}},
        {"permanent_id": "PRIVATE-ID", "booking_number": "PRIVATE-TWO",
         "incarceration": {"Commitment Date": "01/05/2026"}},
    ], stamp)
    summary = summarize_visits(registry)
    write_json(store, "public/index.json", {"sources": {}, "repeat_visits": summary})
    write_json(store, "private/analytics/repeat-visits.json.gz", registry)
    client = create_app(Config(), store).test_client()
    assert b"Visits per returning person" in client.get("/").data
    assert client.get("/api/repeat-visits").json["repeat_people"] == 1
    for route in ("/", "/api/repeat-visits", "/chart/repeat-visits.svg?width=360",
                  "/chart/visit-intervals.svg?width=1000"):
        response = client.get(route)
        assert response.status_code == 200
        assert b"PRIVATE-ID" not in response.data
        assert b"PRIVATE-ONE" not in response.data
    assert client.get("/private/analytics/repeat-visits.json.gz").status_code == 404


def test_coverage_panel_and_api_are_aggregate_only(tmp_path):
    store = LocalStore(tmp_path)
    now = datetime.now(timezone.utc).isoformat()
    write_json(
        store,
        "public/index.json",
        {
            "sources": {},
            "supplements": {
                "iml_details": {
                    "last_success": now,
                    "current": {
                        "available": 80,
                        "eligible": 3200,
                        "fresh": 80,
                        "pending": 3120,
                        "refresh_hours": 24,
                    },
                },
                "xfer_courts": {
                    "last_success": now,
                    "current": {
                        "archived_files": 8,
                        "listed_files": 40,
                        "parsed_files": 8,
                        "pending": 32,
                        "directories": {"/GS-CriminalCourtDispositions": {"status": "empty"}},
                    },
                },
            },
        },
    )
    write_json(store, "private/test.json", {"name": "PRIVATE SYNTHETIC NAME"})
    client = create_app(Config(), store).test_client()
    response = client.get("/")
    assert response.status_code == 200
    assert b"80 of 3,200 listed bookings" in response.data
    assert b"No disposition files" in response.data
    assert client.get("/api/coverage").json["iml_details"]["current"]["available"] == 80
    for route in ("/", "/api/coverage", "/history.csv"):
        assert b"PRIVATE SYNTHETIC NAME" not in client.get(route).data


def test_warm_index_survives_storage_outage_with_warning_and_backoff(tmp_path, monkeypatch):
    from sc_jail.storage import read_json

    store = LocalStore(tmp_path)
    stamp = datetime.now(timezone.utc).isoformat()
    write_json(store, "public/index.json", {"sources": {"iml": {
        "last_success": stamp, "current": {"population": 3210},
    }}})
    clock = [100.0]
    monkeypatch.setattr("sc_jail.web.time.monotonic", lambda: clock[0])
    client = create_app(Config(), store).test_client()
    assert b"3,210" in client.get("/").data
    reads = []

    def unavailable(*_):
        reads.append(True)
        raise OSError("synthetic outage")

    with monkeypatch.context() as m:
        m.setattr(store, "read", unavailable)
        clock[0] = 131
        response = client.get("/")
        assert response.status_code == 200 and b"3,210" in response.data
        assert b"Storage refresh failed" in response.data
        assert response.headers["X-Data-Stale"] == "true"
        assert client.get("/api/freshness").status_code == 503
        assert len(reads) == 1
    clock[0] = 162
    assert "X-Data-Stale" not in client.get("/").headers
    assert read_json(store, "public/index.json")[0]["sources"]["iml"]["current"]["population"] == 3210


def test_chart_cache_uses_version_and_width_buckets(tmp_path, monkeypatch):
    calls = []
    clock = [100.0]
    monkeypatch.setattr("sc_jail.web.time.monotonic", lambda: clock[0])
    monkeypatch.setattr("sc_jail.web.make_chart", lambda *a, **kw: calls.append(a) or "<svg/>")
    store = LocalStore(tmp_path)
    version = write_json(store, "public/index.json", {"sources": {}})
    client = create_app(Config(), store).test_client()
    client.get("/chart/population.svg?width=1000")
    client.get("/chart/population.svg?width=1001&retry=ignored")
    assert len(calls) == 1
    write_json(store, "public/index.json", {"sources": {}, "updated_at": "changed"}, expected=version)
    clock[0] = 131
    client.get("/chart/population.svg?width=1000")
    assert len(calls) == 2


def test_full_ninety_day_changes_are_bounded_and_preserve_totals():
    from sc_jail.charts import change_bins, make_chart

    now = datetime.now(timezone.utc)
    points = [{"observed_at": (now - timedelta(minutes=15*n)).isoformat(),
               "arrivals": 2, "departures": 1} for n in range(8640)]
    bins, seconds = change_bins(points, 90)
    assert seconds == 86400 and len(bins) <= 91
    assert sum(b["arrivals"] for b in bins) == 17280
    assert sum(b["departures"] for b in bins) == 8640
    svg = make_chart({"sources": {"iml": {"history": points}}}, 90, 1000, changes=True)
    assert svg.count('id="patch_') < 200
    assert len(svg) < 100_000


def test_coverage_backlog_is_not_reported_as_complete():
    stamp = datetime.now(timezone.utc)
    source = {"last_success": stamp.isoformat(), "current": {"pending": 300}}
    assert source_health(source, stamp) == ("Coverage incomplete", "warning")
