import pytest

from sc_jail.usage import GIB, cost, project, usage

SERVICES = {
    "collector": {"instance_seconds_per_day": 21_000, "requests_per_day": 115, "vcpu": 0.25, "gib": 0.5},
    "dashboard": {"instance_seconds_per_day": 500, "requests_per_day": 3_550, "vcpu": 0.25, "gib": 0.5},
}
OPERATIONS = {"WriteObject": 2_300, "ListObjects": 600, "ReadObject": 2_850, "GetObjectMetadata": 4_800}


def test_monthly_quantities_scale_daily_use_by_size():
    q = usage(SERVICES, 2 * GIB, OPERATIONS, 0.4 * GIB)
    assert q["run_cpu_second"] == pytest.approx(21_500 * 30.44 * 0.25)
    assert q["run_gib_second"] == pytest.approx(21_500 * 30.44 * 0.5)
    assert q["class_a"] == pytest.approx(2_900 * 30.44)
    assert q["class_b"] == pytest.approx(7_650 * 30.44)
    assert q["storage_gib_month"] == pytest.approx(2.0)


def test_free_allowances_are_subtracted_only_when_available():
    q = usage(SERVICES, 2 * GIB, OPERATIONS, 0.4 * GIB)
    with_free, without = cost(q, free=True), cost(q, free=False)
    assert with_free["run_cpu_second"] == 0 and with_free["storage_gib_month"] == 0
    assert without["run_cpu_second"] == pytest.approx(q["run_cpu_second"] * 0.000024, abs=1e-4)
    assert with_free["class_a"] == pytest.approx((q["class_a"] - 5_000) * 0.000005, abs=1e-4)


def test_projection_flags_the_no_allowance_case_against_the_target():
    result = project(usage(SERVICES, 2 * GIB, OPERATIONS, 0.4 * GIB), 5.0)
    assert result["total_with_free_allowances"] < 1
    assert result["total_without_free_allowances"] > 5
    assert result["within_target_with_free_allowances"]
    assert not result["within_target_either_way"]
    assert result["free_allowance_used"]["run_cpu_second"] == pytest.approx(0.909, abs=0.001)
