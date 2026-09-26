"""Week-over-week composition of the held population, from saved profile summaries.

Each weekly run saves a profile summary; this module lines them up by roster date and
reports the same measures side by side with the change since the previous run. Only
aggregate counts from the summaries are used, so no person-level data is read here.
"""

import json
import statistics
from datetime import date, timedelta

UNSENTENCED = "No case marked sentenced"
PARTLY = "Sentenced on some cases, others open"
ALL_SENTENCED = "Sentenced on every listed case"
FELONY_PREFIXES = ("First-degree murder", "Class A felony", "Class B felony", "Class C felony",
                   "Class D felony", "Class E felony")


def _status(summary, label):
    return dict(summary["status"]).get(label, 0)


def _grade_total(summary, predicate):
    return sum(row["count"] for row in summary["grade"] if predicate(row["label"]))


def _court(summary, label):
    return next((row["count"] for row in summary["court"] if row["label"] == label), 0)


def _recent_flows(summary, days=7):
    """Mean daily new bookings and releases over the last complete days before the roster date."""
    as_of = date.fromisoformat(summary["as_of"])
    window = [d for d in summary.get("daily_flows", [])
              if as_of - timedelta(days=days) <= date.fromisoformat(d["day"]) < as_of]
    if not window:
        return None, None, 0
    return (statistics.mean(d["first_seen"] for d in window),
            statistics.mean(d["released"] for d in window), len(window))


# (key, label, kind); kinds control formatting, suppression, and how change is expressed.
METRICS = [
    ("people", "People listed as held", "count"),
    ("held_median_days", "Median days held so far", "days"),
    ("held_over_year_share", "Held more than a year", "share"),
    ("held_over_two_years_share", "Held more than two years", "share"),
    ("unsentenced", "No case marked sentenced", "count"),
    ("unsentenced_share", "No case marked sentenced (share)", "share"),
    ("unsentenced_median_days", "Median days held, no case sentenced", "days"),
    ("partly_sentenced", "Sentenced on some cases, others open", "count"),
    ("all_sentenced", "Sentenced on every listed case", "count"),
    ("felony_share", "Most serious charge is a felony (share)", "share"),
    ("violation_only", "Violation charges only", "count"),
    ("money_bond_only", "Held on money bond alone", "count"),
    ("money_bond_median", "Median money bond (money bond alone)", "money"),
    ("money_bond_at_most_5000", "Money bond alone, $5,000 or less", "count"),
    ("money_bond_at_most_10000", "Money bond alone, $10,000 or less", "count"),
    ("detainer", "With a detainer", "count"),
    ("violation_charge", "With a violation charge", "count"),
    ("no_bond_set", "With a case with no bond set", "count"),
    ("court_date_passed", "Earliest listed court date already passed", "count"),
    ("court_date_missing", "No court date listed", "count"),
    ("missing_details", "Listed without a record page", "count"),
    ("new_per_day", "New bookings per day (prior 7 days)", "rate"),
    ("released_per_day", "Releases listed per day (prior 7 days)", "rate"),
]


def metrics(summary):
    people = summary["people"]
    unsentenced = summary["held_by_status"].get(UNSENTENCED, {})
    bond = summary["money_bond_only"]
    flags = summary["flags"]
    new, released, flow_days = _recent_flows(summary)
    felonies = _grade_total(summary, lambda label: label.startswith(FELONY_PREFIXES))
    return {
        "people": people,
        "held_median_days": summary["held_median_days"],
        "held_over_year_share": summary["held_over_year_share"],
        "held_over_two_years_share": summary["held_over_two_years_share"],
        "unsentenced": _status(summary, UNSENTENCED),
        "unsentenced_share": _status(summary, UNSENTENCED) / people if people else None,
        "unsentenced_median_days": unsentenced.get("median_days"),
        "partly_sentenced": _status(summary, PARTLY),
        "all_sentenced": _status(summary, ALL_SENTENCED),
        "felony_share": felonies / people if people else None,
        "violation_only": _grade_total(summary, lambda label: label.startswith("Probation")),
        "money_bond_only": bond["people"],
        "money_bond_median": bond["median"],
        "money_bond_at_most_5000": bond["at_most_5000"],
        "money_bond_at_most_10000": bond["at_most_10000"],
        "detainer": flags.get("detainer", 0),
        "violation_charge": flags.get("violation_charge", 0),
        "no_bond_set": flags.get("no_bond_set", 0),
        "court_date_passed": _court(summary, "Listed date before today"),
        "court_date_missing": _court(summary, "No date listed"),
        "missing_details": summary["missing_details"],
        "new_per_day": new,
        "released_per_day": released,
        "flow_days": flow_days,
    }


def load(paths):
    """Profile summaries by roster date; a later roster for the same date replaces an earlier one."""
    by_day = {}
    for path in paths:
        summary = json.loads(path.read_text(encoding="utf-8"))
        day = summary["as_of"]
        kept = by_day.get(day)
        if kept is None or summary.get("roster_observed_at", "") >= kept[0].get("roster_observed_at", ""):
            by_day[day] = (summary, str(path))
    return [by_day[day] for day in sorted(by_day)]


def compare(loaded):
    # The roster time identifies each summary; file paths are not kept because the current
    # run's folder is renamed when it finishes.
    points = [{"as_of": s["as_of"], "roster_observed_at": s.get("roster_observed_at"),
               "metrics": metrics(s)} for s, _ in loaded]
    changes = {}
    if len(points) >= 2:
        before, after = points[-2]["metrics"], points[-1]["metrics"]
        for key, _, _ in METRICS:
            if before.get(key) is not None and after.get(key) is not None:
                changes[key] = after[key] - before[key]
    return {
        "points": points,
        "metrics": [{"key": k, "label": label, "kind": kind} for k, label, kind in METRICS],
        "change_since_previous": changes,
        "compared": [p["as_of"] for p in points[-2:]] if len(points) >= 2 else [],
    }
