from datetime import datetime, timezone
from pathlib import PurePosixPath
from urllib.parse import unquote
from xml.etree import ElementTree as ET

import xlrd

from .http import SourceError, SourceHTTP

URL = "https://xfer.shelbycountytn.gov/"
REQUIRED = [
    "Inmate Name",
    "Booking #",
    "Book Date",
    "DOB",
    "Age",
    "Case #",
    "Chg Code",
    "Charge",
    "Committing Authority",
    "Bond",
    "Det?",
    "Next Court Dt",
]


def xml_response(content):
    if b"<!DOCTYPE" in content.upper() or b"<!ENTITY" in content.upper():
        raise SourceError("Unexpected document in XFER response")
    try:
        root = ET.fromstring(content)
    except ET.ParseError as exc:
        raise SourceError("XFER returned invalid XML") from exc
    if root.tag != "response":
        raise SourceError("XFER response envelope changed")
    for element in ("result", ".//ErrorResponse"):
        code = root.findtext(element)
        if code is not None and code != "0":
            raise SourceError("XFER reported an unsuccessful operation")
    return root


def parse_listing(content, directory):
    root = xml_response(content)
    if root.find("files") is None or root.findtext(".//ErrorResponse") != "0":
        raise SourceError("XFER listing did not confirm success")
    files = []
    for node in root.findall("./files/file"):
        if node.findtext("FileIsDir") == "1":
            continue
        name = unquote(node.findtext("FileName", ""))
        path = unquote(node.findtext("FilePath", ""))
        if not name or PurePosixPath(path).parent.as_posix() != directory:
            raise SourceError("XFER file path is outside the requested directory")
        if ".." in PurePosixPath(path).parts or PurePosixPath(path).name != name:
            raise SourceError("Unexpected XFER path")
        try:
            size = int(node.findtext("FileSize", ""))
            modified = datetime.fromtimestamp(
                int(node.findtext("FileDate", "")), tz=timezone.utc
            ).isoformat()
        except (ValueError, OverflowError) as exc:
            raise SourceError("Invalid XFER file metadata") from exc
        files.append({"name": name, "path": path, "size": size, "modified_at": modified})
    return files


def is_heading_row(values):
    return [str(value).strip() for value in values] == REQUIRED


def is_heading_record(row):
    return set(row) == set(REQUIRED) and is_heading_row([row[k] for k in REQUIRED])


def parse_workbook(content):
    if not content or not content.startswith(bytes.fromhex("d0cf11e0a1b11ae1")):
        raise SourceError("XFER download is not an Excel XLS file")
    try:
        book = xlrd.open_workbook(file_contents=content, on_demand=True)
    except xlrd.XLRDError as exc:
        raise SourceError("XFER download is not a readable Excel workbook") from exc
    try:
        if book.nsheets != 1:
            raise SourceError("XFER workbook sheet structure changed")
        sheet = book.sheet_by_index(0)
        if sheet.nrows < 2 or sheet.ncols != len(REQUIRED):
            raise SourceError("XFER workbook is empty or its columns changed")
        headers = [str(v).strip() for v in sheet.row_values(0)]
        if headers != REQUIRED:
            raise SourceError("XFER workbook column headings changed")
        records, bookings = [], set()
        for n in range(1, sheet.nrows):
            cells = sheet.row(n)
            if all(c.value == "" for c in cells):
                continue
            values = []
            for cell in cells:
                if cell.ctype == xlrd.XL_CELL_DATE:
                    values.append(xlrd.xldate_as_datetime(cell.value, book.datemode).isoformat())
                else:
                    values.append(cell.value)
            if is_heading_row(values):
                continue
            booking = str(values[1]).strip()
            if not booking or not str(values[0]).strip():
                raise SourceError("XFER contains a row without a name or booking number")
            bookings.add(booking)
            records.append(dict(zip(REQUIRED, values, strict=True)))
        if not bookings:
            raise SourceError("XFER report contains no bookings")
        return records, sorted(bookings)
    finally:
        book.release_resources()


def collect(config, observed_at, previous=None):
    with SourceHTTP(URL, user_agent=config.user_agent, budget=config.source_timeout) as session:
        login = session.request(
            "POST",
            "/Web%20Client/Login.xml",
            params={"Command": "Login"},
            data={"user": "public", "pword": "public", "language": "en,US"},
        )
        if xml_response(login.content).findtext("result") != "0":
            raise SourceError("XFER public login did not confirm success")
        listing = session.request(
            "GET", "/Web%20Client/ListError.xml", params={"Command": "List", "Dir": config.xfer_dir}
        )
        files = parse_listing(listing.content, config.xfer_dir)
        selected = [f for f in files if f["name"] == config.xfer_file]
        if len(selected) != 1:
            raise SourceError("The expected SCSO-InJail report is missing or ambiguous")
        file = selected[0]
        if not 0 < file["size"] <= 25_000_000:
            raise SourceError("XFER report size is outside the supported range")
        # Fetch each quarter hour, even when size/date are unchanged. The source
        # can replace content without updating either metadata field.
        download = session.request("GET", "/", params={"Command": "Download", "File": file["path"]})
        if len(download.content) != file["size"]:
            raise SourceError("XFER download size differs from the directory listing")
        records, bookings = parse_workbook(download.content)
    return {
        "metrics": {"population": len(bookings), "charge_rows": len(records), "files": 1},
        "active_ids": bookings,
        "seen_ids": bookings,
        "source_updated_at": file["modified_at"],
        "records": records,
        "artifacts": [(file["name"], download.content), ("xfer-listing.xml", listing.content)],
        "source_url": URL,
        "file": file,
    }
