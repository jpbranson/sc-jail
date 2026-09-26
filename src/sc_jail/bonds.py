"""Money bond and pretrial detention, from dated record-page versions in the booking panel.

Bond changes are found by comparing consecutive record-page versions that list case
entries. A change is dated when the collector saw it (record pages refresh about daily),
not when a court ordered it. Bond status is kept separate from court outcomes: a "Paid"
or "Sentenced" status is never treated as a disposition, and no case outcome is inferred.
"""

from collections import Counter
from datetime import date

from .stays import MAX_ADMISSION_LAG_DAYS, complete, first_decided, local_date
from .survival import summarize

READOUT_DAYS = 28
LOW_BONDS = (1_000, 5_000, 10_000)
ASSESSED = "Bond Assessed - Courts"
RECOGNIZANCE = "Released on own Recognizance"
EVENT_ORDER = ["New court-assessed bond", "Bond total reduced", "Bond total increased",
               "Recognizance entered", "Bond total cleared"]


def classify(before, after):
    """The kind of bond change between two complete record-page versions, or None."""
    old, new = before["bond_total"] or 0, after["bond_total"] or 0
    old_types, new_types = set(before.get("bond_types", [])), set(after.get("bond_types", []))
    if ASSESSED in new_types and ASSESSED not in old_types:
        return "New court-assessed bond"
    if RECOGNIZANCE in new_types and RECOGNIZANCE not in old_types:
        return "Recognizance entered"
    if old > 0 and new > 0 and new != old:
        return "Bond total reduced" if new < old else "Bond total increased"
    if old > 0 and new == 0:
        return "Bond total cleared"
    return None


def bond_events(booking):
    """First change of each kind for one booking: (kind, seen_at, before_total, after_total)."""
    events, seen, previous = [], set(), None
    for version in booking["details"]:
        if not complete(version):
            continue
        kind = classify(previous, version) if previous is not None else None
        if kind and kind not in seen:
            seen.add(kind)
            events.append((kind, version["at"], previous["bond_total"], version["bond_total"]))
        previous = version
    return events


def release_after(booking, since, snapshot_date, zone):
    """(days, released) from a date to the listed release, censored like the stay analysis.

    Returns None when the release date precedes ``since`` (the change was seen afterward).
    """
    release = booking["release_date"]
    if release and date.fromisoformat(release) <= snapshot_date:
        end, released = date.fromisoformat(release), True
    elif booking["outcome"] == "disappeared":
        end, released = local_date(booking["last_seen_at"], zone), False
    else:
        end, released = snapshot_date, False
    if end < since:
        return None
    return (end - since).days, released


def held_at_snapshot(booking, snapshot_date):
    release = booking["release_date"]
    return booking["on_latest_roster"] and (not release or date.fromisoformat(release) > snapshot_date)


def latest_complete(booking):
    return next((v for v in reversed(booking["details"]) if complete(v)), None)


def analyze(bookings, coverage, zone):
    snapshot_date = local_date(coverage["last"], zone)
    followup = (snapshot_date - local_date(coverage["first"], zone)).days
    changes = {kind: [] for kind in EVENT_ORDER}
    change_counts, seen_after_release, reductions = Counter(), Counter(), []
    with_changes = 0
    for booking in bookings:
        events = bond_events(booking)
        with_changes += bool(events)
        for kind, at, before, after in events:
            change_counts[kind] += 1
            if kind == "Bond total reduced" and before and after:
                reductions.append(1 - after / before)
            outcome = release_after(booking, local_date(at, zone), snapshot_date, zone)
            if outcome is None:
                seen_after_release[kind] += 1
            else:
                changes[kind].append(outcome)
    # Everyone held on money bond alone at the latest roster, including long stays.
    stock = {limit: [] for limit in LOW_BONDS}
    for booking in bookings:
        version = latest_complete(booking)
        if version is None or not held_at_snapshot(booking, snapshot_date):
            continue
        if version["money_bond_only"] and version["commitment_date"]:
            held = (snapshot_date - date.fromisoformat(version["commitment_date"])).days
            for limit in LOW_BONDS:
                if version["bond_total"] <= limit:
                    stock[limit].append(held)
    # New bookings whose first bond decision was a low money bond alone.
    flow = {limit: [] for limit in LOW_BONDS}
    for booking in bookings:
        if booking["left_truncated"]:
            continue
        first = first_decided(booking)
        if first is None or not first["money_bond_only"] or not first["commitment_date"]:
            continue
        seen = local_date(booking["first_seen_at"], zone)
        if (seen - date.fromisoformat(first["commitment_date"])).days > MAX_ADMISSION_LAG_DAYS:
            continue
        outcome = release_after(booking, local_date(first["at"], zone), snapshot_date, zone)
        if outcome is None:
            continue
        for limit in LOW_BONDS:
            if first["bond_total"] <= limit:
                flow[limit].append(outcome)

    def stock_summary(days):
        ordered = sorted(days)
        return {"people": len(days),
                "median_days_held": ordered[len(ordered) // 2] if ordered else None,
                "held_over_30_days": sum(d > 30 for d in days),
                "held_over_90_days": sum(d > 90 for d in days)}

    reductions.sort()
    return {
        "coverage_start": coverage["first"],
        "snapshot": coverage["last"],
        "followup_days": followup,
        "readout_days": READOUT_DAYS,
        "readout_ready": followup >= READOUT_DAYS,
        "bookings_with_changes": with_changes,
        "changes": {kind: {"bookings": change_counts[kind],
                           "seen_after_release": seen_after_release[kind],
                           "time_to_release": summarize(changes[kind]) if changes[kind] else None}
                    for kind in EVENT_ORDER},
        "median_reduction_share": reductions[len(reductions) // 2] if reductions else None,
        "low_bond_held_now": {str(limit): stock_summary(days) for limit, days in stock.items()},
        "low_bond_new_bookings": {str(limit): summarize(obs) if obs else None
                                  for limit, obs in flow.items()},
    }
