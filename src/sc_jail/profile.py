"""Aggregate profile of the people currently listed as held, from IML detail pages.

This describes a point-in-time population (a stock), which over-represents long
stays compared with everyone booked over a period. Person-level values stay in
memory; only counts leave this module.
"""

import statistics
from collections import Counter
from datetime import datetime

GRADES = {
    "FM": "First-degree murder (FM)",
    "FA": "Class A felony",
    "FB": "Class B felony",
    "FC": "Class C felony",
    "FD": "Class D felony",
    "FE": "Class E felony",
    "MA": "Class A misdemeanor",
    "MB": "Class B misdemeanor",
    "MC": "Class C misdemeanor",
}
VIOLATION_GRADES = {"I", "IE"}
AGE_BANDS = [(0, 17, "Under 18"), (18, 24, "18–24"), (25, 34, "25–34"), (35, 44, "35–44"),
             (45, 54, "45–54"), (55, 64, "55–64"), (65, 200, "65 and older")]
HELD_BANDS = [(0, 6, "Under 1 week"), (7, 30, "1–4 weeks"), (31, 90, "1–3 months"),
              (91, 180, "3–6 months"), (181, 365, "6–12 months"), (366, 730, "1–2 years"),
              (731, 1095, "2–3 years"), (1096, 100_000, "More than 3 years")]
BOND_BANDS = [(0, 1_000, "$1,000 or less"), (1_000, 5_000, "$1,001–$5,000"),
              (5_000, 10_000, "$5,001–$10,000"), (10_000, 25_000, "$10,001–$25,000"),
              (25_000, 50_000, "$25,001–$50,000"), (50_000, 100_000, "$50,001–$100,000"),
              (100_000, 250_000, "$100,001–$250,000"), (250_000, float("inf"), "More than $250,000")]
COURT_BANDS = [(None, -1, "Listed date before today"), (0, 0, "Today"), (1, 7, "1–7 days"),
               (8, 30, "8–30 days"), (31, 90, "31–90 days"), (91, None, "More than 90 days")]


def parse_date(value):
    try:
        return datetime.strptime(value.strip()[:10], "%m/%d/%Y").date()
    except (AttributeError, ValueError):
        return None


def money(value):
    try:
        return float(str(value).replace(",", "").replace("$", ""))
    except ValueError:
        return None


def band(value, bands):
    for low, high, label in bands:
        if (low is None or value >= low) and (high is None or value <= high):
            return label
    return None


def money_band(value):
    for low, high, label in BOND_BANDS:
        if low < value <= high or (low == 0 and value == 0):
            return label
    return None


def ordered(counter, labels):
    return [{"label": label, "count": counter.get(label, 0)} for label in labels]


def age_on(birth, day):
    return day.year - birth.year - ((day.month, day.day) < (birth.month, birth.day))


def most_serious(charges):
    grades = {c["Grade"] for c in charges}
    for grade in GRADES:
        if grade in grades:
            return GRADES[grade]
    if grades & VIOLATION_GRADES:
        return "Probation, parole, or diversion violation only"
    return "Other or none listed"


def legal_status(bonds):
    statuses = {b["Status"] for b in bonds}
    if not bonds:
        return "No case entries listed"
    if statuses == {"Sentenced"}:
        return "Sentenced on every listed case"
    if "Sentenced" in statuses:
        return "Sentenced on some cases, others open"
    return "No case marked sentenced"


def money_bond_only(record):
    """Open cases with an assessed money bond, and no other stated reason to be held."""
    bonds = record["bonds"]
    if not bonds or record["detainers"]:
        return None
    if any(c["Grade"] in VIOLATION_GRADES for c in record["charges"]):
        return None
    if any(b["Status"] != "Open" or b["Bond Type"] != "Bond Assessed - Courts" for b in bonds):
        return None
    total = money(record["bond_totals"].get("Grand Total", ""))
    return total if total and total > 0 else None


def profile(details, roster, today):
    """Summarize detail records for roster entries without a release date."""
    current = {r["booking_number"] for r in roster if not r["release_date"]}
    people = [d for d in details if d["booking_number"] in current]
    counts = {name: Counter() for name in (
        "sex", "race", "ethnicity", "age", "facility", "held", "status", "grade", "bond", "court")}
    held_days, bond_totals, offenses = [], [], Counter()
    held_by_status = {}
    flags = Counter()
    for person in people:
        counts["sex"][{"M": "Male", "F": "Female"}.get(person["physical"]["Sex"], "Not listed")] += 1
        counts["race"][person["inmate"].get("Race") or "Not listed"] += 1
        counts["ethnicity"][person["inmate"].get("Ethnicity") or "Not listed"] += 1
        counts["facility"][person["incarceration"].get("Current Location") or "Not listed"] += 1
        birth = parse_date(person["physical"]["DOB"])
        counts["age"][band(age_on(birth, today), AGE_BANDS) if birth else "Not listed"] += 1
        start = parse_date(person["incarceration"].get("Commitment Date", ""))
        if start is None or start > today:
            flags["commitment_missing_or_future"] += 1
        else:
            held_days.append((today - start).days)
            counts["held"][band(held_days[-1], HELD_BANDS)] += 1
        status = legal_status(person["bonds"])
        counts["status"][status] += 1
        if start is not None and start <= today:
            held_by_status.setdefault(status, []).append(held_days[-1])
        counts["grade"][most_serious(person["charges"])] += 1
        flags["detainer"] += bool(person["detainers"])
        flags["violation_charge"] += any(c["Grade"] in VIOLATION_GRADES for c in person["charges"])
        flags["no_bond_set"] += any(b["Bond Type"] == "No Bond Set" for b in person["bonds"])
        offenses.update({c["Description"] for c in person["charges"] if c["Description"]})
        total = money_bond_only(person)
        if total is not None:
            bond_totals.append(total)
            counts["bond"][money_band(total)] += 1
        hearings = [parse_date(h["Next Court Date"]) for h in person["hearings"]]
        hearings = [h for h in hearings if h]
        if hearings:
            counts["court"][band((min(hearings) - today).days, COURT_BANDS)] += 1
        else:
            counts["court"]["No date listed"] += 1

    def share(n):
        return n / len(people) if people else None

    return {
        "as_of": today.isoformat(),
        "people": len(people),
        "roster_current": len(current),
        "missing_details": len(current) - len(people),
        "sex": counts["sex"].most_common(),
        "race": counts["race"].most_common(),
        "ethnicity": counts["ethnicity"].most_common(),
        "facility": counts["facility"].most_common(),
        "age": ordered(counts["age"], [b[2] for b in AGE_BANDS] + ["Not listed"]),
        "held": ordered(counts["held"], [b[2] for b in HELD_BANDS]),
        "held_median_days": statistics.median(held_days) if held_days else None,
        "held_over_year_share": share(sum(d > 365 for d in held_days)),
        "held_over_two_years_share": share(sum(d > 730 for d in held_days)),
        "status": counts["status"].most_common(),
        "held_by_status": {
            status: {
                "people": len(days),
                "median_days": statistics.median(days),
                "over_year": sum(d > 365 for d in days),
            }
            for status, days in sorted(held_by_status.items())
        },
        "grade": ordered(counts["grade"], list(GRADES.values()) + [
            "Probation, parole, or diversion violation only", "Other or none listed"]),
        "flags": dict(flags),
        "top_offenses": offenses.most_common(15),
        "money_bond_only": {
            "people": len(bond_totals),
            "median": statistics.median(bond_totals) if bond_totals else None,
            "at_most_5000": sum(t <= 5_000 for t in bond_totals),
            "at_most_10000": sum(t <= 10_000 for t in bond_totals),
            "bands": ordered(counts["bond"], [b[2] for b in BOND_BANDS]),
        },
        "court": ordered(counts["court"], [b[2] for b in COURT_BANDS] + ["No date listed"]),
    }


def movement(registry, zone):
    """Daily bookings first seen and listed releases, for complete local days only.

    Uses the repeat-visit registry rather than adjacent-slot comparisons, so a
    missed collection slot delays when a booking is seen but does not lose it.
    Bookings present in the first observation predate coverage and are excluded.
    """
    first = datetime.fromisoformat(registry["coverage_start"]).astimezone(zone).date()
    last = datetime.fromisoformat(registry["through"]).astimezone(zone).date()
    days = {}

    def entry(day):
        return days.setdefault(day, {"day": day, "first_seen": 0, "released": 0})

    for visit in registry["visits"].values():
        if visit["first_seen_at"] != registry["coverage_start"]:
            entry(datetime.fromisoformat(visit["first_seen_at"]).astimezone(zone).date().isoformat())[
                "first_seen"] += 1
        if visit["release_date"]:
            entry(visit["release_date"])["released"] += 1
    return [days[d] for d in sorted(days) if first.isoformat() < d < last.isoformat()]


def suppress(count, threshold=10):
    return count if count == 0 or count >= threshold else f"<{threshold}"
