import pytest

from sc_jail.survival import at_risk_at, kaplan_meier, quantile, summarize, survival_at

# Hand-worked example: events at 1, 2, 3, 5; censored at 2 and 4.
DATA = [(1, True), (2, True), (2, False), (3, True), (4, False), (5, True)]


def test_estimates_match_the_hand_calculation():
    rows = kaplan_meier(DATA)
    assert [r["time"] for r in rows] == [1, 2, 3, 4, 5]
    assert [r["at_risk"] for r in rows] == [6, 5, 3, 2, 1]
    assert [r["survival"] for r in rows] == pytest.approx([5 / 6, 2 / 3, 4 / 9, 4 / 9, 0])
    assert quantile(rows, 0.5) == 3
    assert quantile(rows, 0.25) == 2


def test_log_log_limits_stay_inside_zero_and_one():
    first = kaplan_meier(DATA)[0]
    # S = 5/6 with Greenwood variance term 1/30; limits from S**exp(±1.96 se/|log S|).
    assert first["lower"] == pytest.approx(0.2731, abs=5e-4)
    assert first["upper"] == pytest.approx(0.9747, abs=5e-4)
    assert kaplan_meier(DATA)[-1]["lower"] is None  # survival 0 has no log-log limits


def test_events_are_counted_before_censoring_at_the_same_time():
    rows = kaplan_meier([(2, True), (2, False)])
    assert rows[0]["at_risk"] == 2 and rows[0]["survival"] == 0.5


def test_lookups_before_the_first_event_and_after_follow_up():
    rows = kaplan_meier(DATA)
    assert survival_at(rows, 0) == 1.0
    assert survival_at(rows, 2) == pytest.approx(2 / 3)
    assert survival_at(rows, 6) is None
    assert at_risk_at(rows, 3) == 3


def test_median_not_reached_when_most_are_censored():
    summary = summarize([(1, True), (3, False), (4, False), (5, False)], days=(1, 7))
    assert summary["median"] is None
    assert summary["at"]["1"]["still_held"] == pytest.approx(0.75)
    assert summary["at"]["7"]["still_held"] is None
    assert (summary["n"], summary["events"], summary["censored"]) == (4, 1, 3)


def test_negative_durations_are_rejected():
    with pytest.raises(ValueError):
        kaplan_meier([(-1, True)])
