import json
from datetime import datetime, timezone

from sc_jail.weekly import (
    Step,
    dated_runs,
    finalize,
    latest_slot,
    readouts,
    render_index,
    run_steps,
)


def fake_runner(codes):
    def runner(argv, log_path, *, cwd, timeout):
        log_path.write_text("ran " + argv[0], encoding="utf-8")
        return codes[argv[0]]
    return runner


def test_failed_prerequisite_skips_only_its_dependents(tmp_path):
    steps = [
        Step("mirror", "Mirror", argv=["mirror"]),
        Step("panel", "Panel", argv=["panel"], needs=("mirror",)),
        Step("stays", "Stays", argv=["stays"], needs=("panel",)),
        Step("profile", "Profile", argv=["profile"], needs=("mirror",)),
    ]
    results = run_steps(steps, tmp_path / "logs", cwd=tmp_path,
                        runner=fake_runner({"mirror": 0, "panel": 1, "stays": 0, "profile": 0}))
    assert results["panel"]["status"] == "failed" and results["panel"]["exit_code"] == 1
    assert results["stays"] == {"status": "skipped", "reason": "needs panel"}
    assert results["profile"]["status"] == "ok"
    assert (tmp_path / "logs" / "profile.log").read_text(encoding="utf-8") == "ran profile"


def test_python_step_exception_is_recorded_and_later_steps_run(tmp_path):
    def broken(log_path):
        raise ValueError("synthetic failure")

    steps = [Step("mirror", "Mirror", call=broken), Step("other", "Other", argv=["other"])]
    results = run_steps(steps, tmp_path / "logs", cwd=tmp_path, runner=fake_runner({"other": 0}))
    assert results["mirror"]["status"] == "failed"
    assert results["mirror"]["message"] == "ValueError: synthetic failure"
    assert "synthetic failure" in (tmp_path / "logs" / "mirror.log").read_text(encoding="utf-8")
    assert results["other"]["status"] == "ok"


def test_call_step_message_is_kept(tmp_path):
    steps = [Step("mirror", "Mirror", call=lambda log: (0, "Newest roster slot 00:00"))]
    results = run_steps(steps, tmp_path / "logs", cwd=tmp_path)
    assert results["mirror"]["status"] == "ok"
    assert results["mirror"]["message"] == "Newest roster slot 00:00"


def test_latest_slot_reads_committed_observation_keys(tmp_path):
    for key in ("2026/09/25/2345", "2026/09/26/0000", "2026/09/19/0830"):
        path = tmp_path / "private" / "observations" / "iml" / f"{key}.json.gz"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"")
    (tmp_path / "private" / "observations" / "iml" / "2026" / "09" / "26" / "0015.tmp").write_bytes(b"")
    assert latest_slot(tmp_path, "iml") == datetime(2026, 9, 26, 0, 0, tzinfo=timezone.utc)
    assert latest_slot(tmp_path, "xfer") is None


def test_finalize_keeps_an_earlier_run_for_the_same_date(tmp_path):
    earlier = tmp_path / "2026-09-30"
    earlier.mkdir()
    (earlier / "run.json").write_text("{}", encoding="utf-8")
    work = tmp_path / ".partial-x"
    work.mkdir()
    (work / "run.json").write_text(json.dumps({"new": True}), encoding="utf-8")
    final = finalize(work, tmp_path / "2026-09-30")
    assert json.loads((final / "run.json").read_text(encoding="utf-8")) == {"new": True}
    kept = [p.name for p in tmp_path.iterdir() if p.name.startswith("2026-09-30.previous-")]
    assert len(kept) == 1 and not work.exists()
    assert [p.name for p in dated_runs(tmp_path)] == ["2026-09-30"]


def test_index_links_only_successful_reports_and_escapes_text(tmp_path):
    steps = [Step("profile", "Profile <html>", report="profile/report.html"),
             Step("stays", "Length of stay", report="stays/report.html")]
    run = {"date": "2026-09-30", "status": "incomplete", "started_at": "2026-09-30T14:00:00+00:00",
           "snapshot": {"latest_iml_slot": "2026-09-30T13:45:00+00:00", "synced": True},
           "steps": {"profile": {"status": "ok", "seconds": 5, "log": "logs/profile.log"},
                     "stays": {"status": "skipped", "reason": "needs panel"}}}
    page = render_index(run, steps)
    assert '<a href="profile/report.html">Profile &lt;html&gt;</a>' in page
    assert 'href="stays/report.html"' not in page and "needs panel" in page


def test_readouts_come_from_each_step_summary(tmp_path):
    (tmp_path / "stays").mkdir()
    (tmp_path / "stays" / "summary.json").write_text(
        json.dumps({"readout_ready": False, "followup_days": 6, "readout_days": 30}), encoding="utf-8")
    (tmp_path / "profile").mkdir()
    (tmp_path / "profile" / "summary.json").write_text(json.dumps({"people": 3}), encoding="utf-8")
    steps = [Step("stays", "Stays", report="stays/report.html"),
             Step("profile", "Profile", report="profile/report.html"),
             Step("courts", "Courts", report="courts/report.html")]
    results = {"stays": {"status": "ok"}, "profile": {"status": "ok"}, "courts": {"status": "failed"}}
    readouts(tmp_path, steps, results)
    assert results["stays"]["readout"] == {"ready": False, "followup_days": 6, "needs_days": 30}
    assert "readout" not in results["profile"] and "readout" not in results["courts"]
    run = {"date": "2026-09-25", "status": "complete", "started_at": "2026-09-26T00:00:00+00:00",
           "snapshot": {}, "steps": results}
    assert "Preliminary: 6 of 30 days" in render_index(run, steps)


def test_alerts_from_a_summary_are_shown_on_the_index(tmp_path):
    (tmp_path / "usage").mkdir()
    (tmp_path / "usage" / "summary.json").write_text(
        json.dumps({"alert": "Projected $4.20/month is at least 80% of the $5.00 target"}),
        encoding="utf-8")
    steps = [Step("usage", "Cost", report="usage/report.html")]
    results = readouts(tmp_path, steps, {"usage": {"status": "ok"}})
    run = {"date": "2026-09-25", "status": "complete", "started_at": "2026-09-26T00:00:00+00:00",
           "snapshot": {}, "steps": results}
    assert "Alert: Projected $4.20/month" in render_index(run, steps)
