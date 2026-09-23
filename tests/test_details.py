import time
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from sc_jail import iml_details as details
from sc_jail.config import Config
from sc_jail.history import canonical_state, observation_key, reconstruct_state
from sc_jail.http import SourceError
from sc_jail.migration import migrate_archive
from sc_jail.storage import LocalStore, read_json, write_json

NOW = datetime(2026, 9, 19, 8, tzinfo=timezone.utc)


def roster(booking="TEST-BK-1", permanent="TEST-P1"):
    return {
        "booking_number": booking,
        "permanent_id": permanent,
        "result_id": "TEST-SYS",
        "name": "SYNTHETIC PERSON",
        "release_date": "",
        "date_of_birth": "01/01/1990",
    }


def fields(**values):
    return (
        "<tr>"
        + "".join(f'<td class="bodysmallbold">{k}:</td><td>{v}</td>' for k, v in values.items())
        + "</tr>"
    )


def section(name, body):
    return (
        f'<table><tr><td><table><tr><td class="header">{name} Information</td>'
        f"</tr></table></td></tr>{body}</table>"
    )


def table_rows(columns, rows):
    return (
        "<tr>"
        + "".join(f"<td>{c}</td>" for c in columns)
        + "</tr>"
        + "".join("<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>" for row in rows)
    )


def detail_html(booking="TEST-BK-1", permanent="TEST-P1", bond="500"):
    empty = "<tr><td>There is no hearing information for this inmate.</td></tr>"
    return (
        "<html><table>"
        + fields(Sex="X", DOB="01/01/1990")
        + "</table>"
        + section(
            "Inmate", fields(**{"Booking #": booking, "Permanent ID #": permanent, "Race": "TEST"})
        )
        + section(
            "Incarceration", fields(**{"Commitment Date": "09/01/2026", "Current Location": "TEST"})
        )
        + section("Alias", table_rows(details.ALIAS_HEADERS, [["TEST", "SYNTHETIC", ""]]))
        + section(
            "Charge",
            table_rows(
                details.CHARGE_HEADERS,
                [["CASE-01", "08/31/2026", "001", "TEST CHARGE", "F", "1"]] * 2,
            ),
        )
        + section(
            "Bond",
            fields(**{"Case #": "CASE-01", "Amount": bond})
            + fields(**{"Bond Type": "TEST", "Status": "Bond Assessed"})
            + fields(**{"Case #": "CASE-02", "Amount": ""})
            + fields(**{"Bond Type": "TEST", "Status": "No Bond"})
            + fields(**{"Grand Total": bond}),
        )
        + section("Hearing", empty)
        + section(
            "Detainer",
            table_rows(
                ["Comp Date", "Comp No", "Issued By", "Set By"],
                [["09/01/2026", "TEST-01", "TEST AGENCY", "TEST"]],
            ),
        )
        + "</html>"
    )


def seed_roster(store, rows=None):
    rows = rows or [roster()]
    write_json(
        store,
        "private/checkpoints/iml.json.gz",
        {
            "slot": NOW.isoformat(),
            "observed_at": NOW.isoformat(),
            "state": canonical_state(rows, ["TEST-P1"], ["TEST-P1"]),
        },
    )


def install_http(monkeypatch, responses):
    calls = []

    class Session:
        def __init__(self, *args, **kwargs):
            self.deadline = time.monotonic() + 200

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def request(self, *args, **kwargs):
            calls.append(kwargs["data"]["sysID"])
            value = next(responses)
            if isinstance(value, Exception):
                raise value
            return SimpleNamespace(text=value, content=value.encode())

    monkeypatch.setattr(details, "SourceHTTP", Session)
    monkeypatch.setattr(details, "start_search", lambda _: None)
    return calls


def collect(store, moment=NOW, **kwargs):
    return details.collect_details(
        Config(page_delay=0, **kwargs),
        store,
        moment,
        deadline=time.monotonic() + 200,
        now=lambda: moment,
    )


def test_detail_preserves_duplicate_charges_case_bonds_and_detainers():
    record = details.parse_detail(detail_html(), roster())
    assert len(record["charges"]) == 2
    assert len(record["bonds"]) == 2
    assert next(b for b in record["bonds"] if b["Case #"] == "CASE-02")["Status"] == "No Bond"
    assert record["hearings"] == []
    assert record["detainers"][0]["Comp No"] == "TEST-01"
    assert record["booking_number"] == "TEST-BK-1"


@pytest.mark.parametrize(
    "html",
    [
        detail_html(booking="WRONG"),
        detail_html(permanent="WRONG"),
        detail_html().replace("Charge Information", "Unknown Section"),
        detail_html().replace("<td>Grade</td>", "<td>Changed Header</td>"),
        "<html>Login required</html>",
    ],
)
def test_detail_rejects_mismatches_and_changed_layout(html):
    with pytest.raises(SourceError):
        details.parse_detail(html, roster())


def test_select_due_prioritizes_changes_new_and_overdue_and_cools_down_failures():
    rows = [roster(f"TEST-{i}") for i in range(5)]
    checks = {
        "TEST-0": {"checked_at": NOW.isoformat(), "roster_sha256": "old"},
        "TEST-2": {
            "checked_at": (NOW - timedelta(days=2)).isoformat(),
            "roster_sha256": details.roster_hash(rows[2]),
        },
        "TEST-3": {"failed_at": NOW.isoformat()},
        "TEST-4": {"checked_at": NOW.isoformat(), "roster_sha256": details.roster_hash(rows[4])},
    }
    assert [r["booking_number"] for r in details.select_due(rows, checks, NOW, 24)] == [
        "TEST-0",
        "TEST-1",
        "TEST-2",
    ]


def test_refresh_queue_uses_headroom_and_oldest_first_without_release_starvation():
    rows = [roster(f"TEST-{i}") for i in range(7)]
    rows[1]["release_date"] = "09/18/2026"
    rows[2]["release_date"] = "09/18/2026"
    ages = [24, 26, 23, 20, 19.99, 22, 0]
    checks = {
        row["booking_number"]: {
            "checked_at": (NOW - timedelta(hours=age)).isoformat(),
            "roster_sha256": details.roster_hash(row),
        }
        for row, age in zip(rows, ages, strict=True)
    }
    checks["TEST-5"]["failed_at"] = (NOW - timedelta(minutes=59)).isoformat()
    checks["TEST-6"]["roster_sha256"] = "changed"
    assert [row["booking_number"] for row in details.select_due(rows, checks, NOW, 24)] == [
        "TEST-6", "TEST-1", "TEST-0", "TEST-2", "TEST-3",
    ]


@pytest.mark.parametrize("lead,expected", [(0, []), (4, ["TEST-BK-1"])])
def test_early_refresh_can_be_disabled_and_is_capped_for_short_intervals(lead, expected):
    row = roster()
    checks = {row["booking_number"]: {
        "checked_at": (NOW - timedelta(minutes=18)).isoformat(),
        "roster_sha256": details.roster_hash(row),
    }}
    assert [r["booking_number"] for r in details.select_due(
        [row], checks, NOW, 0.4, refresh_ahead_hours=lead,
    )] == expected
    assert details.select_due([row], checks, NOW - timedelta(seconds=1), 0.4,
                              refresh_ahead_hours=lead) == []


def test_daily_expiry_wave_drains_in_bounded_batches_before_freshness_deadline():
    rows = [roster(f"TEST-{i}") for i in range(161)]
    checks = {row["booking_number"]: {
        "checked_at": NOW.isoformat(), "roster_sha256": details.roster_hash(row),
    } for row in rows}
    batch_counts = []
    for minutes in (1200, 1215, 1230):
        moment = NOW + timedelta(minutes=minutes)
        batch = details.select_due(rows, checks, moment, 24)[:80]
        batch_counts.append(len(batch))
        for row in batch:
            checks[row["booking_number"]]["checked_at"] = moment.isoformat()
    assert batch_counts == [80, 80, 1]
    assert details.select_due(rows, checks, NOW + timedelta(hours=24), 24) == []


def test_early_refresh_backlog_stays_fresh_but_unchecked_pages_expire(tmp_path, monkeypatch):
    store = LocalStore(tmp_path)
    seed_roster(store, [roster(), roster("TEST-BK-2", "TEST-P2")])
    install_http(monkeypatch, iter([
        detail_html(), detail_html("TEST-BK-2", "TEST-P2"), detail_html(),
    ]))
    collect(store)
    for hours, batch, expected_fresh in ((20, 1, 2), (24, 0, 1)):
        moment = NOW + timedelta(hours=hours)
        cache, version = read_json(store, "private/checkpoints/iml.json.gz")
        cache["observed_at"] = cache["slot"] = moment.isoformat()
        write_json(store, "private/checkpoints/iml.json.gz", cache, expected=version)
        point = collect(store, moment, detail_batch=batch)
        assert point["checked"] == batch
        assert point["fresh"] == expected_fresh
        assert point["pending"] == 2 - expected_fresh
        assert point["oldest_checked_at"] == NOW.isoformat()


def test_detail_skips_fresh_pages_and_archives_only_semantic_changes(tmp_path, monkeypatch):
    store = LocalStore(tmp_path)
    seed_roster(store)
    calls = install_http(
        monkeypatch,
        iter(
            [
                detail_html(),
                "<!-- changed presentation -->" + detail_html(),
                detail_html(bond="900"),
            ]
        ),
    )
    first = collect(store, detail_refresh_hours=0.4)
    assert first["available"] == first["checked"] == first["fresh"] == 1
    assert collect(store, NOW + timedelta(minutes=15), detail_refresh_hours=0.4)["checked"] == 0
    same = collect(store, NOW + timedelta(minutes=30), detail_refresh_hours=0.4)
    assert same["checked"] == 1 and same["changed"] == 0
    key = observation_key("iml_details", NOW + timedelta(minutes=30))
    manifest, _ = read_json(store, key)
    assert manifest["history"]["kind"] == "unchanged" and manifest["artifacts"] == []
    changed = collect(store, NOW + timedelta(hours=1), detail_refresh_hours=0.4)
    assert changed["changed"] == 1
    assert len(calls) == 3
    cache, _ = read_json(store, details.CACHE_KEY)
    assert reconstruct_state(store, cache["manifest_key"]) == cache["state"]
    migrate_archive(store)
    assert read_json(store, details.CACHE_KEY)[0]["checks"] == cache["checks"]


def test_partial_failure_preserves_last_good_record_and_freshness(tmp_path, monkeypatch):
    store = LocalStore(tmp_path)
    seed_roster(store)
    install_http(monkeypatch, iter([detail_html(), detail_html(booking="WRONG")]))
    collect(store, detail_refresh_hours=0.1)
    old, _ = read_json(store, details.CACHE_KEY)
    result = collect(store, NOW + timedelta(minutes=15), detail_refresh_hours=0.1)
    after, _ = read_json(store, details.CACHE_KEY)
    assert result["failed"] == 1 and result["available"] == 1 and result["fresh"] == 0
    assert after["state"] == old["state"]
    assert after["checks"]["TEST-BK-1"]["unparsed_html"]["sha256"]
    assert after["checks"]["TEST-BK-1"]["checked_at"] == NOW.isoformat()


def test_detail_batch_limit_and_resume_without_redownload(tmp_path, monkeypatch):
    store = LocalStore(tmp_path)
    seed_roster(store, [roster(), roster("TEST-BK-2", "TEST-P2")])
    calls = install_http(monkeypatch, iter([detail_html()]))
    write = store.write
    failures = []

    def fail(key, *args, **kwargs):
        if key == details.CACHE_KEY and not failures:
            failures.append(True)
            raise OSError("test interrupted cache write")
        return write(key, *args, **kwargs)

    monkeypatch.setattr(store, "write", fail)
    with pytest.raises(OSError):
        collect(store, detail_batch=1)
    monkeypatch.setattr(store, "write", write)
    point = collect(store, detail_batch=1)
    assert len(calls) == 1 and point["available"] == 1 and point["pending"] == 1


def test_explicit_absent_incarceration_information_is_preserved():
    original = section(
        "Incarceration", fields(**{"Commitment Date": "09/01/2026", "Current Location": "TEST"})
    )
    empty = section(
        "Incarceration", "<tr><td>There is no incarceration information for this inmate.</td></tr>"
    )
    record = details.parse_detail(detail_html().replace(original, empty), roster())
    assert record["incarceration"] == {}
