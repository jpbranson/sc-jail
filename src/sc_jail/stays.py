"""Length of stay for bookings that began after collection started (Kaplan-Meier).

A booking enters the cohort when the roster first lists it after the first archived
observation, so its whole stay is observable. Time runs in whole days from the IML
commitment date to the listed release date, the same date fields the population profile
uses. Bookings still held are censored at the latest roster date; bookings that left the
roster without a release date are censored when last seen.

Groups come from the record page after it fills in. Charges and bond entries are usually
entered hours after a booking first appears, and the bond decision (any bond type other
than "Not Assessed") later still, typically at the first court appearance. Charge grade
and detainer use the first page with case entries; bond situation and amount use the
first page showing a bond decision. Record pages keep being fetched while a released
booking is still listed, so waiting for them does not require the person to stay held.
"""

from collections import Counter
from datetime import date, datetime

from .survival import summarize

READOUT_DAYS = 30
# A commitment date well before a booking first appears marks an older stay (for example a
# return from elsewhere), not a new admission, so its full stay is not observable.
MAX_ADMISSION_LAG_DAYS = 7
GRADE_GROUPS = {
    "First-degree murder (FM)": "Felony A–B or murder",
    "Class A felony": "Felony A–B or murder",
    "Class B felony": "Felony A–B or murder",
    "Class C felony": "Felony C–E",
    "Class D felony": "Felony C–E",
    "Class E felony": "Felony C–E",
    "Class A misdemeanor": "Misdemeanor",
    "Class B misdemeanor": "Misdemeanor",
    "Class C misdemeanor": "Misdemeanor",
    "Probation, parole, or diversion violation only": "Violation only",
    "Other or none listed": "Other or none listed",
}
INCOMPLETE = "Record not complete"
NO_DECISION = "No bond decision seen"
GRADE_ORDER = ["Felony A–B or murder", "Felony C–E", "Misdemeanor", "Violation only",
               "Other or none listed", INCOMPLETE]
BOND_ORDER = ["Money bond alone", "No bond set on a case", "Released on recognizance",
              "Other: detainer, violation, sentence, or mixed", NO_DECISION]
DETAINER_ORDER = ["Detainer", "No detainer", INCOMPLETE]
AMOUNT_BANDS = [(1_000, "$1,000 or less"), (5_000, "$1,001–$5,000"), (25_000, "$5,001–$25,000"),
                (float("inf"), "More than $25,000")]


def local_date(moment, zone):
    return datetime.fromisoformat(moment).astimezone(zone).date()


def amount_band(total):
    return next(label for upper, label in AMOUNT_BANDS if total <= upper)


def complete(version):
    """A record-page version that lists case entries (charges and bonds are entered)."""
    return version["status"] != "No case entries listed"


def decided(version):
    """A version showing a bond decision: some bond type other than Not Assessed."""
    return complete(version) and bool(set(version.get("bond_types", [])) - {"Not Assessed"})


def first_complete(booking):
    return next((v for v in booking["details"] if complete(v)), None)


def first_decided(booking):
    return next((v for v in booking["details"] if decided(v)), None)


def bond_group(version):
    if version["money_bond_only"]:
        return "Money bond alone"
    if version["no_bond_set"]:
        return "No bond set on a case"
    if "Released on own Recognizance" in version.get("bond_types", []):
        return "Released on recognizance"
    return "Other: detainer, violation, sentence, or mixed"


def groups(entered, decision):
    """Group labels: charge and detainer when entered; bond when a decision is visible."""
    labels = {"grade": INCOMPLETE, "detainer": INCOMPLETE, "bond": NO_DECISION, "amount": None}
    if entered is not None:
        labels["grade"] = GRADE_GROUPS.get(entered["grade"], "Other or none listed")
        labels["detainer"] = "Detainer" if entered["detainers"] else "No detainer"
    if decision is not None:
        labels["bond"] = bond_group(decision)
        if decision["money_bond_only"]:
            labels["amount"] = amount_band(decision["bond_total"])
    return labels


def stay(booking, snapshot_date, zone):
    """(duration, released, origin) for one new booking, or (None, reason) if it is excluded."""
    first_seen = local_date(booking["first_seen_at"], zone)
    commitments = [d["commitment_date"] for d in booking["details"] if d["commitment_date"]]
    origin = date.fromisoformat(commitments[0]) if commitments else first_seen
    if (first_seen - origin).days > MAX_ADMISSION_LAG_DAYS:
        return None, "Commitment date more than a week before first listed"
    if origin > first_seen:
        return None, "Commitment date after first listed"
    release = booking["release_date"]
    if release and date.fromisoformat(release) <= snapshot_date:
        end, released = date.fromisoformat(release), True
    elif booking["outcome"] == "disappeared":
        end, released = local_date(booking["last_seen_at"], zone), False
    else:
        end, released = snapshot_date, False
    if end < origin:
        return None, "Release date before commitment date"
    return ((end - origin).days, released, "commitment" if commitments else "first_seen"), None


def listing_hours(bookings):
    """Hours released bookings stayed on the roster after their release date first appeared."""
    hours = sorted(
        (datetime.fromisoformat(b["last_seen_at"]) - datetime.fromisoformat(b["release_listed_at"]))
        .total_seconds() / 3600
        for b in bookings
        if b["outcome"] == "released" and b["release_listed_at"] and not b["on_latest_roster"]
    )
    if not hours:
        return None
    return {"bookings": len(hours), "median": hours[len(hours) // 2], "shortest": hours[0],
            "tenth_percentile": hours[len(hours) // 10]}


def analyze(bookings, coverage, zone):
    """Kaplan-Meier summaries overall and by group for bookings first seen after coverage began."""
    snapshot_date = local_date(coverage["last"], zone)
    start_date = local_date(coverage["first"], zone)
    excluded, origins, observations = Counter(), Counter(), []
    delays = {"entered": [], "bond_decided": []}
    by_group = {"grade": {}, "bond": {}, "amount": {}, "detainer": {}}
    already_released, same_day = 0, 0
    for booking in bookings:
        if booking["left_truncated"]:
            continue
        result, reason = stay(booking, snapshot_date, zone)
        if result is None:
            excluded[reason] += 1
            continue
        duration, released, origin = result
        origins[origin] += 1
        observations.append((duration, released))
        first_release = booking["release_history"][0] if booking["release_history"] else None
        if first_release and first_release[0] == booking["first_seen_at"] and first_release[1]:
            already_released += 1  # the whole stay fell between two collections
        if released and duration == 0:
            same_day += 1
        entered, decision = first_complete(booking), first_decided(booking)
        for stage, version in (("entered", entered), ("bond_decided", decision)):
            if version is not None:
                delays[stage].append((datetime.fromisoformat(version["at"]) - datetime.fromisoformat(
                    booking["first_seen_at"])).total_seconds() / 3600)
        labels = groups(entered, decision)
        for dimension, label in labels.items():
            if label is not None:
                by_group[dimension].setdefault(label, []).append((duration, released))
    followup = (snapshot_date - start_date).days

    def timing(hours):
        hours = sorted(hours)
        return {"reached": len(hours), "not_reached": len(observations) - len(hours),
                "median_hours": hours[len(hours) // 2] if hours else None,
                "ninetieth_percentile_hours": hours[int(len(hours) * 0.9)] if hours else None}

    return {
        "coverage_start": coverage["first"],
        "snapshot": coverage["last"],
        "followup_days": followup,
        "readout_days": READOUT_DAYS,
        "readout_ready": followup >= READOUT_DAYS,
        "cohort": len(observations),
        "excluded": dict(excluded),
        "origin": dict(origins),
        "overall": summarize(observations),
        "groups": {dimension: {label: summarize(obs) for label, obs in sorted(labels.items())}
                   for dimension, labels in by_group.items()},
        "short_stays": {"release_listed_when_first_seen": already_released,
                        "released_same_day": same_day,
                        "listing_after_release_hours": listing_hours(bookings)},
        "record_completion": {stage: timing(hours) for stage, hours in delays.items()},
    }
