"""Re-booking after release: how soon a released person is booked into the jail again.

Each listed release during collection starts a clock; the event is the first later
booking with the same IML permanent person ID, dated by the day the roster first listed
it. People whose permanent ID was ever reassigned between bookings are left out, because
their bookings cannot be linked safely. Only this jail's roster is observed, so this is
re-booking here while collection runs, not a recidivism rate.
"""

from datetime import date

from .stays import local_date
from .survival import summarize

READOUT_DAYS = 90
DAYS = (7, 30, 60, 90)


def conflicted_people(bookings):
    """Permanent IDs involved in any reassignment; none of their bookings can be linked."""
    return {person for b in bookings if len(b["permanent_ids"]) > 1 for person in b["permanent_ids"]}


def analyze(bookings, coverage, zone):
    snapshot_date = local_date(coverage["last"], zone)
    start_date = local_date(coverage["first"], zone)
    conflicted = conflicted_people(bookings)
    by_person = {}
    for booking in bookings:
        if booking["permanent_ids"] and booking["permanent_ids"][0] not in conflicted:
            by_person.setdefault(booking["permanent_ids"][0], []).append(booking)
    observations, excluded_conflicted, released = [], 0, 0
    for booking in bookings:
        release = booking["release_date"]
        if not release:
            continue
        released_on = date.fromisoformat(release)
        if not start_date <= released_on <= snapshot_date:
            continue  # released before collection or listed for a future date
        released += 1
        person = booking["permanent_ids"][0] if booking["permanent_ids"] else None
        if person is None or person in conflicted:
            excluded_conflicted += 1
            continue
        later = [local_date(other["first_seen_at"], zone) for other in by_person[person]
                 if other["booking_number"] != booking["booking_number"]
                 and local_date(other["first_seen_at"], zone) >= released_on
                 and other["first_seen_at"] > booking["first_seen_at"]]
        if later:
            observations.append(((min(later) - released_on).days, True))
        else:
            observations.append(((snapshot_date - released_on).days, False))
    followup = (snapshot_date - start_date).days
    return {
        "coverage_start": coverage["first"],
        "snapshot": coverage["last"],
        "followup_days": followup,
        "readout_days": READOUT_DAYS,
        "readout_ready": followup >= READOUT_DAYS,
        "releases_during_collection": released,
        "excluded_reassigned_ids": excluded_conflicted,
        # A new booking number on the release day can be administrative rather than a new arrest.
        "same_day": sum(1 for days, event in observations if event and days == 0),
        "rebooking": summarize(observations, days=DAYS) if observations else None,
    }
