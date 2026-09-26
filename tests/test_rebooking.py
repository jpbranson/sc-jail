from zoneinfo import ZoneInfo

from sc_jail.rebooking import analyze

CHICAGO = ZoneInfo("America/Chicago")
COVERAGE = {"first": "2026-09-19T08:44:00+00:00", "last": "2026-09-26T00:15:00+00:00"}


def booking(number, person, first, *, release=None, ids=None):
    return {"booking_number": number, "permanent_ids": ids or [person], "first_seen_at": first,
            "release_date": release}


def test_release_followed_by_a_later_booking_of_the_same_person():
    bookings = [
        booking("B1", "P1", "2026-09-19T08:44:00+00:00", release="2026-09-20"),
        booking("B2", "P1", "2026-09-23T15:00:00+00:00"),                     # 3 days later
        booking("B3", "P2", "2026-09-19T08:44:00+00:00", release="2026-09-21"),  # not rebooked
        booking("B4", "P3", "2026-09-19T08:44:00+00:00", release="2026-09-10"),  # before coverage
        booking("B5", "P4", "2026-09-19T08:44:00+00:00", release="2026-09-22"),
        booking("B6", "P4", "2026-09-22T20:00:00+00:00"),                     # same day
    ]
    result = analyze(bookings, COVERAGE, CHICAGO)
    followed = result["rebooking"]
    assert result["releases_during_collection"] == 3
    assert (followed["n"], followed["events"]) == (3, 2)
    assert result["same_day"] == 1
    assert followed["at"]["7"]["still_held"] is None  # only 6 days of follow-up so far
    assert not result["readout_ready"]


def test_people_with_reassigned_ids_are_not_linked():
    bookings = [
        booking("B1", "P1", "2026-09-19T08:44:00+00:00", release="2026-09-20", ids=["P1", "P9"]),
        booking("B2", "P9", "2026-09-23T15:00:00+00:00"),
        booking("B3", "P2", "2026-09-19T08:44:00+00:00", release="2026-09-21"),
    ]
    result = analyze(bookings, COVERAGE, CHICAGO)
    assert result["excluded_reassigned_ids"] == 1
    assert (result["rebooking"]["n"], result["rebooking"]["events"]) == (1, 0)


def test_concurrent_booking_seen_before_release_is_not_a_rebooking():
    bookings = [
        booking("B1", "P1", "2026-09-19T08:44:00+00:00", release="2026-09-22"),
        booking("B2", "P1", "2026-09-20T15:00:00+00:00"),
    ]
    assert analyze(bookings, COVERAGE, CHICAGO)["rebooking"]["events"] == 0
