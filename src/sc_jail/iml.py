import json
import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup

from .http import SourceError, SourceHTTP

URL = "https://imljail.shelbycountytn.gov/IML"
CHICAGO = ZoneInfo("America/Chicago")
log = logging.getLogger(__name__)


def parse_page(html):
    soup = BeautifulSoup(html, "lxml")
    text = soup.get_text(" ", strip=True)
    match = re.search(r"Showing\s+([\d,]+)\s+to\s+([\d,]+)\s+of\s+([\d,]+)\s+results", text, re.I)
    if not match:
        raise SourceError("IML result range missing; possible login, error, or layout change")
    start, end, total = (int(x.replace(",", "")) for x in match.groups())
    if total < 1 or total > 50_000 or not 1 <= start <= end <= total:
        raise SourceError("IML returned an implausible result range")
    rows = []
    for link in soup.find_all(
        "a", class_="underlined", href=re.compile(r"javascript:submitInmate\(")
    ):
        cells = link.find_parent("tr").find_all("td", recursive=False)
        if len(cells) != 5:
            raise SourceError("IML roster columns changed")
        values = [" ".join(c.get_text(" ", strip=True).split()) for c in cells]
        result = re.search(r"submitInmate\('([^']+)'", link["href"])
        if not result or not values[1] or not values[2]:
            raise SourceError("IML record identifier missing")
        release = values[4]
        if release:
            try:
                release = datetime.strptime(release, "%m/%d/%Y").date().isoformat()
            except ValueError as exc:
                raise SourceError("Unrecognized IML release date") from exc
        rows.append(
            dict(
                zip(
                    ["name", "booking_number", "permanent_id", "date_of_birth", "release_date"],
                    values,
                    strict=True,
                )
            )
            | {"release_date": release, "result_id": result.group(1)}
        )
    if len(rows) != end - start + 1:
        raise SourceError("IML page has fewer records than its advertised range")
    return start, end, total, rows


def summarize(rows, observed_at):
    today = observed_at.astimezone(CHICAGO).date().isoformat()
    active = {r["permanent_id"] for r in rows if not r["release_date"] or r["release_date"] > today}
    seen = {r["permanent_id"] for r in rows}
    return (
        {
            "population": len(active),
            "listed_people": len(seen),
            "listed_records": len(rows),
            "bookings": len({r["booking_number"] for r in rows}),
            "released_people": len(seen - active),
        },
        sorted(active),
        sorted(seen),
    )


def start_search(session):
    session.request("GET", "/IML")
    return session.request(
        "POST",
        "/IML",
        data={
            "flow_action": "searchbyid",
            "quantity": "10",
            "systemUser_identifiervalue": "",
            "searchtype": "PIN",
            "systemUser_includereleasedinmate": "Y",
            "systemUser_includereleasedinmate2": "Y",
            "systemUser_firstName": "",
            "systemUser_lastName": "",
            "systemUser_dateOfBirth": "",
            "releasedB": "checkbox",
            "identifierbox": "PIN",
            "identifier": "",
        },
    )


def collect(config, observed_at, previous=None):
    started = time.monotonic()
    pages, rows, total = [], [], None
    try:
        with SourceHTTP(
            "https://imljail.shelbycountytn.gov",
            user_agent=config.user_agent,
            budget=config.iml_timeout,
        ) as session:
            response = start_search(session)
            start, end, total, rows = parse_page(response.text)
            if start != 1:
                raise SourceError("IML search did not begin on the first page")
            pages = [response.text]
            page_size = len(rows)
            log.info("IML scan started: %s records, %s per page, %.0fs budget, %s page workers",
                     total, page_size, config.iml_timeout, config.iml_page_workers)
            # IML accepts explicit offsets in one search session. Bound concurrency to two
            # and retain pacing; consume responses in roster order, irrespective of completion.
            with ThreadPoolExecutor(max_workers=config.iml_page_workers) as pool:
                while end < total:
                    batch = []
                    for offset in range(
                        end + 1, min(total + 1, end + 1 + page_size * config.iml_page_workers),
                        page_size,
                    ):
                        time.sleep(config.page_delay)
                        batch.append((offset, pool.submit(
                            session.request, "POST", "/IML",
                            data={"flow_action": "next", "currentStart": str(offset)},
                        )))
                    try:
                        for offset, future in batch:
                            response = future.result()
                            next_start, next_end, next_total, next_rows = parse_page(response.text)
                            if (
                                next_total != total
                                or next_start != offset
                                or next_end != min(offset + page_size - 1, total)
                            ):
                                raise SourceError(
                                    f"IML pagination shifted during collection "
                                    f"(expected row {offset} of {total}; "
                                    f"got rows {next_start}-{next_end} of {next_total})"
                                )
                            pages.append(response.text)
                            rows.extend(next_rows)
                            end = next_end
                            if len(pages) % 20 == 0 or end == total:
                                log.info("IML scan: %s pages, %s/%s records, %.1fs elapsed",
                                         len(pages), len(rows), total, time.monotonic() - started)
                    finally:
                        for _, future in batch:
                            future.cancel()
            if len(rows) != total or len({r["result_id"] for r in rows}) != total:
                raise SourceError("IML roster is incomplete or contains duplicate result IDs")
    except SourceError as exc:
        raise SourceError(
            f"{exc}; {len(pages)} pages, {len(rows)}/{total if total is not None else '?'} "
            f"records in {time.monotonic() - started:.1f}s"
        ) from exc
    metrics, active, seen = summarize(rows, observed_at)
    return {
        "metrics": metrics | {
            "pages": len(pages), "scan_seconds": round(time.monotonic() - started, 1)
        },
        "active_ids": active,
        "seen_ids": seen,
        "source_updated_at": None,
        "records": rows,
        "artifacts": [("iml-pages.json", json.dumps(pages).encode())],
        "source_url": URL,
    }
