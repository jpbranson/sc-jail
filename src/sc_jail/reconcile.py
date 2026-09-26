"""IML roster versus the XFER jail report: do the two public sources list the same bookings?

XFER regenerates its jail workbook about every two hours. Each distinct workbook version
is compared with the IML roster observation nearest to the workbook's own timestamp, by
exact booking number only; names are never read or compared. IML counts a booking as
held when its release date is blank or after that moment's Central date, matching the
collector's population rule. Results are counts, never person-level rows.
"""

from bisect import bisect_left
from collections import Counter, defaultdict
from datetime import datetime, timedelta

from .panel import replay
from .profile import parse_date
from .storage import read_json

MAX_ALIGN_MINUTES = 20
# XFER regenerates about every two hours, so a booking IML first listed within that window
# may simply not have reached the workbook yet.
RECENT = timedelta(hours=2)


def manifests(store, source):
    keys = sorted(k for k in store.keys(f"private/observations/{source}/") if k.endswith(".json.gz"))
    return [(key, read_json(store, key)[0]) for key in keys]


def xfer_versions(xfer):
    """The first observation of each distinct workbook (source timestamp and content)."""
    versions, last = [], None
    for key, manifest in xfer:
        point = manifest["point"]
        ident = (point.get("source_updated_at"), manifest["history"].get("state_sha256"))
        if ident != last and point.get("source_updated_at"):
            versions.append({"xfer_key": key, "source_updated_at": point["source_updated_at"],
                             "xfer_observed_at": point["observed_at"]})
        last = ident
    return versions


def align(versions, iml, max_minutes=MAX_ALIGN_MINUTES):
    """Pair each workbook with the nearest roster observation within max_minutes."""
    times = [datetime.fromisoformat(manifest["point"]["observed_at"]) for _, manifest in iml]
    for version in versions:
        moment = datetime.fromisoformat(version["source_updated_at"])
        index = bisect_left(times, moment)
        nearby = [k for k in (index - 1, index) if 0 <= k < len(times)]
        best = min(nearby, key=lambda k: abs(times[k] - moment), default=None)
        offset = abs(times[best] - moment).total_seconds() / 60 if best is not None else None
        if offset is not None and offset <= max_minutes:
            version.update(iml_key=iml[best][0], iml_observed_at=times[best].isoformat(),
                           offset_minutes=round(offset, 1))
        else:
            version.update(iml_key=None, iml_observed_at=None, offset_minutes=None)
    return versions


def iml_sets(records, observed_at, zone):
    today = datetime.fromisoformat(observed_at).astimezone(zone).date().isoformat()
    listed = {row["booking_number"] for row in records}
    held = {row["booking_number"] for row in records
            if not row["release_date"] or row["release_date"] > today}
    return listed, held


def capture_iml(store, wanted, zone):
    """Roster sets at the wanted observations, and when each booking was first listed."""
    sets, first_seen = {}, {}
    for key, manifest, state, _ in replay(store, "iml"):
        at = manifest["point"]["observed_at"]
        for row in state["records"]:
            first_seen.setdefault(row["booking_number"], at)
        if key in wanted:
            sets[key] = iml_sets(state["records"], at, zone)
    return sets, first_seen


def capture_xfer(store, wanted, latest_key):
    """Workbook booking sets at the wanted observations, plus rows of the latest one."""
    sets, latest_rows = {}, []
    for key, _, state, _ in replay(store, "xfer"):
        if key in wanted:
            sets[key] = {row["Booking #"] for row in state["records"] if row["Booking #"]}
        if key == latest_key:
            latest_rows = state["records"]
    return sets, latest_rows


def compare(version, xfer_bookings, listed, held, first_seen):
    moment = datetime.fromisoformat(version["source_updated_at"])
    roster_at = version["iml_observed_at"]
    missing = xfer_bookings - listed
    absent = held - xfer_bookings
    recent = {b for b in absent if datetime.fromisoformat(first_seen[b]) >= moment - RECENT}
    return {
        **version,
        "xfer_bookings": len(xfer_bookings),
        "iml_held": len(held),
        "iml_listed": len(listed),
        "both": len(xfer_bookings & held),
        "xfer_not_on_roster": len(missing),
        "xfer_not_on_roster_seen_before": sum(first_seen.get(b, "9") <= roster_at for b in missing),
        "xfer_listed_iml_released": len(xfer_bookings & (listed - held)),
        "iml_held_not_in_xfer": len(absent),
        "iml_held_not_in_xfer_recent": len(recent),
    }


def _iso(value):
    """Date part of an XFER timestamp such as 2026-09-23T00:00:00."""
    return value[:10] if value and len(value) >= 10 else None


def case_relation(xfer_cases, iml_cases):
    if not xfer_cases or not iml_cases:
        return "One side lists no case numbers"
    if xfer_cases == iml_cases:
        return "Identical"
    if xfer_cases < iml_cases:
        return "XFER lists fewer (subset of IML)"
    if iml_cases < xfer_cases:
        return "IML lists fewer (subset of XFER)"
    if xfer_cases & iml_cases:
        return "Partly overlapping"
    return "No case number in common"


def field_agreement(xfer_rows, details, bookings):
    """Compare published fields for bookings both sources list, using exact identifiers."""
    by_booking = defaultdict(list)
    for row in xfer_rows:
        if row["Booking #"] in bookings:
            by_booking[row["Booking #"]].append(row)
    detail = {d["booking_number"]: d for d in details if d["booking_number"] in bookings}
    book_date, cases, detainer, court = Counter(), Counter(), Counter(), Counter()
    for booking, rows in by_booking.items():
        record = detail.get(booking)
        if record is None:
            book_date["No IML record page"] += 1
            cases["No IML record page"] += 1
            detainer["No IML record page"] += 1
            court["No IML record page"] += 1
            continue
        xfer_days = {_iso(r["Book Date"]) for r in rows} - {None}
        committed = parse_date(record["incarceration"].get("Commitment Date", ""))
        if not xfer_days or committed is None:
            book_date["Date missing on one side"] += 1
        elif len(xfer_days) > 1:
            book_date["XFER lists several book dates"] += 1
        else:
            xfer_day = next(iter(xfer_days))
            iml_day = committed.isoformat()
            book_date["Same date" if xfer_day == iml_day else
                      "XFER book date later" if xfer_day > iml_day else "XFER book date earlier"] += 1
        cases[case_relation({r["Case #"] for r in rows if r["Case #"]},
                            {c["Case #"] for c in record["charges"] if c["Case #"]})] += 1
        xfer_hold = any(r["Det?"].strip().upper() == "YES" for r in rows)
        iml_hold = bool(record["detainers"])
        detainer["Both show a detainer" if xfer_hold and iml_hold else
                 "Neither shows a detainer" if not xfer_hold and not iml_hold else
                 "Only XFER shows a detainer" if xfer_hold else "Only IML shows a detainer"] += 1
        xfer_courts = sorted({_iso(r["Next Court Dt"]) for r in rows} - {None})
        iml_courts = sorted(filter(None, (parse_date(h["Next Court Date"]) for h in record["hearings"])))
        if not xfer_courts and not iml_courts:
            court["Neither lists a date"] += 1
        elif not xfer_courts or not iml_courts:
            court["Only one lists a date"] += 1
        else:
            court["Same earliest date" if xfer_courts[0] == iml_courts[0].isoformat()
                  else "Different earliest date"] += 1
    return {"bookings_compared": len(by_booking), "book_date": dict(book_date),
            "case_numbers": dict(cases), "detainer": dict(detainer), "next_court": dict(court)}


AGE_BANDS = ((1, "1 day or less"), (7, "2–7 days"), (30, "8–30 days"), (365, "31–365 days"),
             (float("inf"), "More than a year"))


def _age_band(days):
    return next(label for upper, label in AGE_BANDS if days <= upper)


def describe_differences(xfer_rows, details, xfer_only, iml_only, moment):
    """Aggregate traits of the bookings only one source lists; no identifiers leave here."""
    authority, ages, detainer = Counter(), Counter(), Counter()
    rows_by_booking = defaultdict(list)
    for row in xfer_rows:
        if row["Booking #"] in xfer_only:
            rows_by_booking[row["Booking #"]].append(row)
    for rows in rows_by_booking.values():
        named = Counter(r["Committing Authority"].strip() or "Not listed" for r in rows)
        authority[named.most_common(1)[0][0]] += 1
        booked = min((_iso(r["Book Date"]) for r in rows if _iso(r["Book Date"])), default=None)
        ages[_age_band((moment.date() - datetime.fromisoformat(booked).date()).days)
             if booked else "Book date missing"] += 1
        detainer["Detainer" if any(r["Det?"].strip().upper() == "YES" for r in rows)
                 else "No detainer"] += 1
    location = Counter()
    by_number = {d["booking_number"]: d for d in details}
    for booking in iml_only:
        record = by_number.get(booking)
        location[(record["incarceration"].get("Current Location") or "Not listed") if record
                 else "No IML record page"] += 1
    return {
        "xfer_only": {"committing_authority": dict(authority.most_common()),
                      "book_date_age": dict(ages), "detainer": dict(detainer)},
        "iml_only": {"current_location": dict(location.most_common())},
    }


def reconcile(store, zone, details):
    """Compare every aligned workbook version with its roster; details feed the latest check."""
    iml, xfer = manifests(store, "iml"), manifests(store, "xfer")
    versions = align(xfer_versions(xfer), iml)
    aligned = [v for v in versions if v["iml_key"]]
    if not aligned:
        raise ValueError("No XFER workbook version has a roster observation nearby")
    latest = aligned[-1]
    iml_sets_at, first_seen = capture_iml(store, {v["iml_key"] for v in aligned}, zone)
    xfer_sets_at, latest_rows = capture_xfer(store, {v["xfer_key"] for v in aligned},
                                             latest["xfer_key"])
    pairs = [compare(v, xfer_sets_at[v["xfer_key"]], *iml_sets_at[v["iml_key"]], first_seen)
             for v in aligned]
    listed, held = iml_sets_at[latest["iml_key"]]
    workbook = xfer_sets_at[latest["xfer_key"]]
    both = held & workbook
    return {
        "xfer_versions": len(versions),
        "aligned_versions": len(aligned),
        "unaligned_versions": [v["source_updated_at"] for v in versions if not v["iml_key"]],
        "max_align_minutes": MAX_ALIGN_MINUTES,
        "pairs": pairs,
        "latest": pairs[-1],
        "latest_field_agreement": field_agreement(latest_rows, details, both),
        "latest_differences": describe_differences(
            latest_rows, details, workbook - listed, held - workbook,
            datetime.fromisoformat(latest["source_updated_at"]).astimezone(zone)),
    }


def by_day(pairs, zone):
    """Median of each count across the workbook versions compared on each Central day."""
    days = defaultdict(list)
    for pair in pairs:
        days[datetime.fromisoformat(pair["source_updated_at"]).astimezone(zone).date().isoformat()].append(pair)
    fields = ("xfer_bookings", "iml_held", "both", "xfer_not_on_roster", "xfer_listed_iml_released",
              "iml_held_not_in_xfer")
    out = []
    for day in sorted(days):
        rows = days[day]
        entry = {"day": day, "versions": len(rows)}
        for field in fields:
            values = sorted(r[field] for r in rows)
            middle = len(values) // 2
            entry[field] = (values[middle] if len(values) % 2 else
                            (values[middle - 1] + values[middle]) / 2)
        out.append(entry)
    return out
