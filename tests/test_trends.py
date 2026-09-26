import json

import pytest

from sc_jail.trends import compare, load, metrics


def summary(as_of, *, people=100, unsentenced=40, observed="2026-09-23 06:48", flows=()):
    return {
        "as_of": as_of,
        "roster_observed_at": observed,
        "people": people,
        "missing_details": 2,
        "held_median_days": 180,
        "held_over_year_share": 0.34,
        "held_over_two_years_share": 0.15,
        "status": [["No case marked sentenced", unsentenced],
                   ["Sentenced on some cases, others open", 35],
                   ["Sentenced on every listed case", people - unsentenced - 35]],
        "held_by_status": {"No case marked sentenced": {"people": unsentenced, "median_days": 66,
                                                        "over_year": 5}},
        "grade": [{"label": "Class A felony", "count": 30}, {"label": "Class C felony", "count": 30},
                  {"label": "Class A misdemeanor", "count": 20},
                  {"label": "Probation, parole, or diversion violation only", "count": 15},
                  {"label": "Other or none listed", "count": 5}],
        "flags": {"detainer": 20, "violation_charge": 18, "no_bond_set": 12},
        "money_bond_only": {"people": 25, "median": 100000.0, "at_most_5000": 3, "at_most_10000": 4},
        "court": [{"label": "Listed date before today", "count": 7},
                  {"label": "No date listed", "count": 11}],
        "daily_flows": list(flows),
    }


def write(tmp_path, name, value):
    path = tmp_path / name
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def test_metrics_combine_status_grade_bond_and_court_counts():
    m = metrics(summary("2026-09-23"))
    assert m["unsentenced"] == 40 and m["unsentenced_share"] == pytest.approx(0.4)
    assert m["all_sentenced"] == 25 and m["partly_sentenced"] == 35
    assert m["felony_share"] == pytest.approx(0.6)
    assert m["violation_only"] == 15
    assert (m["money_bond_only"], m["money_bond_median"]) == (25, 100000.0)
    assert (m["court_date_passed"], m["court_date_missing"]) == (7, 11)


def test_flow_rates_use_only_complete_days_in_the_prior_week():
    flows = [{"day": "2026-09-19", "first_seen": 999, "released": 999},  # more than 7 days before
             {"day": "2026-09-27", "first_seen": 80, "released": 60},
             {"day": "2026-09-29", "first_seen": 70, "released": 80},
             {"day": "2026-09-30", "first_seen": 999, "released": 999}]  # the roster day itself
    m = metrics(summary("2026-09-30", flows=flows))
    assert (m["new_per_day"], m["released_per_day"], m["flow_days"]) == (75, 70, 2)
    assert metrics(summary("2026-09-30"))["new_per_day"] is None


def test_load_orders_by_date_and_keeps_the_latest_roster_for_a_date(tmp_path):
    paths = [write(tmp_path, "b.json", summary("2026-09-30", people=120, observed="2026-09-30 14:00")),
             write(tmp_path, "a.json", summary("2026-09-23")),
             write(tmp_path, "c.json", summary("2026-09-30", people=125, observed="2026-09-30 20:00"))]
    loaded = load(paths)
    assert [s["as_of"] for s, _ in loaded] == ["2026-09-23", "2026-09-30"]
    assert loaded[-1][0]["people"] == 125


def test_compare_reports_change_between_the_last_two_dates(tmp_path):
    loaded = load([write(tmp_path, "a.json", summary("2026-09-23", people=100, unsentenced=40)),
                   write(tmp_path, "b.json", summary("2026-09-30", people=110, unsentenced=50))])
    result = compare(loaded)
    assert result["compared"] == ["2026-09-23", "2026-09-30"]
    assert result["change_since_previous"]["people"] == 10
    assert result["change_since_previous"]["unsentenced_share"] == pytest.approx(50 / 110 - 0.4)
    assert "new_per_day" not in result["change_since_previous"]


def test_single_summary_has_no_change():
    assert compare([(summary("2026-09-23"), "x")])["change_since_previous"] == {}
