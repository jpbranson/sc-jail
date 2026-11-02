from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

from sc_jail import forecast

CHICAGO = ZoneInfo("America/Chicago")
# Monday first; sums to zero so centered-week deviations recover it exactly.
PATTERN = [30, 27, 0, -8, -19, -22, -8]
MONDAY = date(2026, 9, 21)


def history(days, *, start=MONDAY, base=3000, slots=96, shift=None):
    """Quarter-hour points for consecutive Central days following the weekday pattern."""
    points = []
    for n in range(days):
        day = start + timedelta(days=n)
        value = base + PATTERN[day.weekday()] + (shift or {}).get(day, 0)
        midnight = datetime.combine(day, datetime.min.time(), CHICAGO)
        for slot in range(slots if isinstance(slots, int) else slots.get(day, 96)):
            moment = (midnight + timedelta(minutes=15 * slot)).astimezone(timezone.utc)
            points.append({"observed_at": moment.isoformat(), "population": value})
    return points


def test_daily_means_keep_complete_days_only():
    thin = MONDAY + timedelta(days=3)
    series = forecast.daily_means(history(10, slots={thin: 10}), CHICAGO)
    assert min(series) == MONDAY + timedelta(days=1) and max(series) == MONDAY + timedelta(days=8)
    assert thin not in series and len(series) == 7
    assert series[MONDAY + timedelta(days=1)] == {"mean": 3027, "observations": 96}
    assert forecast.daily_means(history(2), CHICAGO) == {}


def test_weekday_offsets_recover_the_weekly_pattern_once_every_weekday_has_a_window():
    assert forecast.weekday_offsets(forecast.daily_means(history(14), CHICAGO)) is None
    offsets = forecast.weekday_offsets(forecast.daily_means(history(16), CHICAGO))
    assert offsets == {weekday: pytest.approx(PATTERN[weekday]) for weekday in range(7)}


def test_weekday_rule_shifts_the_latest_level_by_the_weekday_difference():
    origin = MONDAY + timedelta(days=21)  # a Monday, +30 in the pattern
    series = forecast.daily_means(history(23, shift={origin: 100}), CHICAGO)
    ahead = forecast.weekday_rule(series, origin)
    assert [day for day, _ in ahead] == [origin + timedelta(days=h) for h in range(1, 8)]
    # Level is 3100 after removing Monday's +30; Tuesday adds +27, Saturday -22.
    assert ahead[0][1] == pytest.approx(3100 + 27)
    assert ahead[4][1] == pytest.approx(3100 - 22)
    assert forecast.weekday_rule(series, origin + timedelta(days=1)) == []


def test_backtest_pairs_each_past_forecast_with_what_happened():
    bump = MONDAY + timedelta(days=20)
    series = forecast.daily_means(history(30, shift={bump: 50}), CHICAGO)
    records = forecast.backtest(series)
    one_day = {r["target"]: r["forecast"] - r["actual"] for r in records if r["ahead"] == 1}
    assert len(one_day) == 28 - 13  # offsets exist from the 13th of 28 complete days
    # A flat weekly pattern forecasts itself exactly until the bump, which is missed by 50
    # and then carried forward (less the small dent it leaves in the weekday pattern).
    assert all(abs(miss) < 1e-6 for day, miss in one_day.items() if day < bump)
    assert one_day[bump] == pytest.approx(-50)
    assert one_day[bump + timedelta(days=1)] == pytest.approx(50, abs=10)
    errors = forecast.errors_by_horizon(records)
    assert len(errors[7]) == 28 - 13 - 6
    assert forecast.band(errors[1]) == pytest.approx(max(abs(one_day[bump]), 0), abs=50)
    assert forecast.band([1, -2, 3, -4]) is None
    assert forecast.band([1, -2, 3, -4, 5]) == 4


def test_hour_of_day_measures_deviation_from_the_daily_average():
    points = history(5, slots=96)
    for point in points:
        if datetime.fromisoformat(point["observed_at"]).astimezone(CHICAGO).hour == 16:
            point["population"] += 24  # four slots of +24 raise the daily mean by one
    series = forecast.daily_means(points, CHICAGO)
    hours = forecast.hour_of_day(points, CHICAGO, series)
    assert hours[16] == pytest.approx(23) and hours[3] == pytest.approx(-1)


def test_summarize_reports_days_ahead_and_misses():
    index = {"sources": {"iml": {"history": history(10)}}}
    short = forecast.summarize(index, "iml", CHICAGO)
    assert short["available"] is False and short["note"] == forecast.NOT_YET
    assert short["days"] == [] and short["ahead"] == []

    bump = MONDAY + timedelta(days=25)
    index = {"sources": {"iml": {"history": history(30, shift={bump: 40})}}}
    summary = forecast.summarize(index, "iml", CHICAGO)
    assert summary["available"] and summary["origin"] == (MONDAY + timedelta(days=28)).isoformat()
    assert len(summary["days"]) == 28 and len(summary["ahead"]) == 7
    assert summary["offsets"]["Monday"] == pytest.approx(30, abs=0.5)
    bumped = next(d for d in summary["days"] if d["date"] == bump.isoformat())
    assert (bumped["actual"], bumped["forecast"], bumped["miss"]) == (3000 + PATTERN[bump.weekday()] + 40,
                                                                      3000 + PATTERN[bump.weekday()], -40)
    following = next(d for d in summary["days"] if d["date"] == (bump + timedelta(days=1)).isoformat())
    assert following["miss"] == 40
    assert summary["ahead"][0]["date"] == (MONDAY + timedelta(days=29)).isoformat()
    assert summary["ahead"][0]["low"] <= summary["ahead"][0]["forecast"] <= summary["ahead"][0]["high"]
    assert summary["errors"] == 15
