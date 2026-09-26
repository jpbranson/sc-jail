"""Private booking-level panel replayed from committed roster and detail history.

One row per IML booking: when it was on the roster, what the roster said about its
release, and dated changes in the detail-page facts later analysis needs. Names and
dates of birth are deliberately omitted. The panel must reproduce every archived
IML population before it is used.
"""

from datetime import datetime, timedelta, timezone

from .history import HistoryError, observation_key, reconstruct_state, replay_history
from .profile import VIOLATION_GRADES, legal_status, money, money_bond_only, most_serious
from .profile import parse_date as detail_date
from .storage import read_json

FACTS = ("commitment_date", "status", "grade", "bond_total", "money_bond_only",
         "no_bond_set", "bond_types", "detainers", "violation", "next_court", "cases")


def replay(store, source):
    """Yield (key, manifest, state, changed_rows) for each committed observation, in order.

    changed_rows lists the rows added by a change log, or every row for a checkpoint,
    so callers can process only records whose content changed.
    """
    prefix = f"private/observations/{source}/"
    state = previous_key = digest = None
    for key in sorted(k for k in store.keys(prefix) if k.endswith(".json.gz")):
        manifest, _ = read_json(store, key)
        if not manifest or key != observation_key(source, manifest["point"]["slot"]):
            raise HistoryError("Panel observation identity is invalid")
        history = manifest.get("history", {})
        linked = state is not None and history.get("previous") == previous_key
        if linked and history.get("kind") == "unchanged":
            # Identical verified state; skip re-sorting and rehashing thousands of rows.
            if not history["before_sha256"] == history["state_sha256"] == digest:
                raise HistoryError("Panel history checksum does not match")
            changed = []
        elif linked and history.get("kind") == "delta":
            state = replay_history(store, history, state)
            changed = [entry["row"] for entry in history["changes"]["records"]["add"]]
        else:
            state = reconstruct_state(store, key, manifest=manifest)
            changed = state["records"]
        digest = history.get("state_sha256")
        previous_key = key
        yield key, manifest, state, changed


def detail_facts(record):
    """Analysis fields from one detail-page version; values are JSON-serializable."""
    hearings = sorted(filter(None, (detail_date(h["Next Court Date"]) for h in record["hearings"])))
    start = detail_date(record["incarceration"].get("Commitment Date", ""))
    total = money(record["bond_totals"].get("Grand Total", ""))
    return {
        "commitment_date": start.isoformat() if start else None,
        "status": legal_status(record["bonds"]),
        "grade": most_serious(record["charges"]),
        "bond_total": total,
        "money_bond_only": money_bond_only(record) is not None,
        "no_bond_set": any(b["Bond Type"] == "No Bond Set" for b in record["bonds"]),
        # Distinguishes a bond not yet assessed from other reasons a money bond is absent.
        "bond_types": sorted({b["Bond Type"] for b in record["bonds"] if b["Bond Type"]}),
        "detainers": len(record["detainers"]),
        "violation": any(c["Grade"] in VIOLATION_GRADES for c in record["charges"]),
        "next_court": hearings[0].isoformat() if hearings else None,
        "cases": sorted({c["Case #"] for c in record["charges"] if c["Case #"]}),
    }


def _new_booking(booking):
    return {
        "booking_number": booking,
        "permanent_ids": [],
        "permanent_id_history": [],
        "first_seen_at": None,
        "last_seen_at": None,
        "spans": [],
        "release_date": None,
        "release_listed_at": None,
        "release_history": [],
        "details": [],
    }


def build_panel(store, zone):
    """Return (bookings by number, roster observations with slot, time, and population)."""
    bookings, observations = {}, []
    previous_present = set()
    for _, manifest, state, _ in replay(store, "iml"):
        at = manifest["point"]["observed_at"]
        present = set()
        for row in state["records"]:
            booking = bookings.setdefault(row["booking_number"], _new_booking(row["booking_number"]))
            present.add(row["booking_number"])
            # IML occasionally reassigns a booking's permanent ID; keep when it changed.
            history = booking["permanent_id_history"]
            if not history or history[-1][1] != row["permanent_id"]:
                history.append([at, row["permanent_id"]])
                booking["permanent_ids"] = sorted({*booking["permanent_ids"], row["permanent_id"]})
            booking["first_seen_at"] = booking["first_seen_at"] or at
            booking["last_seen_at"] = at
            # A booking absent from any complete roster starts a new presence span.
            if row["booking_number"] in previous_present:
                booking["spans"][-1][1] = at
            else:
                booking["spans"].append([at, at])
            # The roster can list, withdraw, and relist a release date; keep each change.
            release = row["release_date"] or None
            if release != booking["release_date"]:
                booking["release_history"].append([at, release])
                booking["release_date"] = release
                booking["release_listed_at"] = at if release else None
        previous_present = present
        observations.append({"slot": manifest["point"]["slot"], "observed_at": at,
                             "population": manifest["point"]["population"]})
    if not observations:
        raise HistoryError("The archive has no IML roster observations")
    first_at, last_at = observations[0]["observed_at"], observations[-1]["observed_at"]
    for booking in bookings.values():
        booking["left_truncated"] = booking["first_seen_at"] == first_at
        booking["on_latest_roster"] = booking["last_seen_at"] == last_at
        booking["reappearances"] = len(booking["spans"]) - 1
        if booking["release_date"]:
            booking["outcome"] = "released"
        elif booking["on_latest_roster"]:
            booking["outcome"] = "held"
        else:
            booking["outcome"] = "disappeared"
    for _, manifest, _, changed in replay(store, "iml_details"):
        at = manifest["point"]["observed_at"]
        for record in changed:
            booking = bookings.get(record["booking_number"])
            if booking is None:
                continue
            facts = detail_facts(record)
            last = booking["details"][-1] if booking["details"] else None
            if last is None or any(last[k] != facts[k] for k in FACTS):
                booking["details"].append({"at": at, **facts})
    return bookings, observations


def value_at(history, at):
    """The value from a [[changed_at, value], ...] history in effect at a time."""
    current = None
    for since, value in history:
        if since > at:
            break
        current = value
    return current


def held_at(booking, at, zone):
    """Mirror the collector: present, with a blank or future release date at that time."""
    if not any(start <= at <= end for start, end in booking["spans"]):
        return False
    release = value_at(booking["release_history"], at)
    return not release or release > datetime.fromisoformat(at).astimezone(zone).date().isoformat()


def check_populations(bookings, observations, zone):
    """Compare the panel's population with every archived one; returns the mismatches."""
    mismatches = []
    rows = list(bookings.values())
    for point in observations:
        at, expected = point["observed_at"], point["population"]
        people = {value_at(b["permanent_id_history"], at) for b in rows if held_at(b, at, zone)}
        if len(people) != expected:
            mismatches.append({"observed_at": at, "archived": expected, "panel": len(people)})
    return mismatches


def missing_slots(observations):
    """Quarter-hour slots between the first and last observation without a roster."""
    slots = {datetime.fromisoformat(point["slot"]) for point in observations}
    slot, end = min(slots), max(slots)
    missing = []
    while slot <= end:
        if slot not in slots:
            missing.append(slot.astimezone(timezone.utc).isoformat())
        slot += timedelta(minutes=15)
    return missing
