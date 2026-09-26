"""Weekly private analysis: refresh the local archive mirror and rebuild every product.

    python scripts/weekly_analysis.py
    python scripts/weekly_analysis.py --skip-sync --output-root SCRATCH_DIR

Syncs the cloud archive into a local mirror with `gcloud storage rsync` (only new or
changed objects are downloaded), checks that the newest roster observation is recent,
then runs each product script into data/analysis/weekly/<Central date>/. The booking
panel must reproduce every archived IML population, or the steps that depend on it are
skipped. Reads only the local mirror, never the live bucket through the Python client,
so analysis cannot touch collection state. Outputs are private; see docs/ANALYSIS.md.
"""

import argparse
import json
import shutil
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from filelock import FileLock, Timeout

from sc_jail.iml import CHICAGO
from sc_jail.weekly import (
    Step,
    central_date,
    finalize,
    latest_slot,
    readouts,
    run_steps,
    run_subprocess,
    work_folder,
    write_run,
)

ROOT = Path(__file__).resolve().parents[1]
BUCKET = "sc-jail-research-20260922-sc-jail-data"
PROJECT = "sc-jail-research-20260922"


def gcloud():
    found = shutil.which("gcloud")
    if found:
        return found
    for name in ("gcloud.cmd", "gcloud"):
        portable = ROOT / ".runtime" / "google-cloud-sdk" / "bin" / name
        if portable.exists():
            return str(portable)
    raise FileNotFoundError("gcloud CLI not found on PATH or in .runtime/google-cloud-sdk")


def build_steps(args, work, snapshot):
    py, scripts = sys.executable, ROOT / "scripts"
    mirror = str(args.mirror)

    def mirror_step(log_path):
        if not args.skip_sync:
            code = run_subprocess([gcloud(), "storage", "rsync", "-r", f"gs://{args.bucket}",
                                   mirror, "--project", args.project],
                                  log_path, cwd=ROOT, timeout=3600)
            if code:
                return code, "gcloud storage rsync failed; see the log (sign-in may have expired)"
            snapshot["synced"] = True
        newest = latest_slot(args.mirror, "iml")
        snapshot["latest_iml_slot"] = newest.isoformat() if newest else None
        if newest is None:
            return 1, "The mirror has no IML roster observations"
        age = datetime.now(timezone.utc) - newest
        if not args.skip_sync and age > timedelta(hours=args.max_age_hours):
            return 1, (f"Newest roster slot is {age.total_seconds() / 3600:,.1f} hours old; "
                       "collection or the mirror is stale")
        return 0, f"Newest roster slot {newest:%Y-%m-%d %H:%M} UTC"

    return [
        Step("mirror", "Archive mirror", call=mirror_step),
        Step("panel", "Booking panel (population check)", needs=("mirror",),
             argv=[py, scripts / "build_panel.py", "--data-dir", mirror,
                   "--output", work / "panel"]),
        Step("profile", "Population profile", needs=("mirror",), report="profile/report.html",
             argv=[py, scripts / "profile_population.py", "--data-dir", mirror,
                   "--output", work / "profile"]),
        Step("trends", "Week-over-week composition", needs=("profile",),
             report="trends/report.html",
             argv=[py, scripts / "analysis_trends.py", "--weekly-root", args.output_root,
                   "--current", work / "profile" / "summary.json", "--baseline", args.baseline,
                   "--output", work / "trends"]),
        Step("reconcile", "IML and XFER reconciliation", needs=("mirror",),
             report="reconcile/report.html",
             argv=[py, scripts / "reconcile_sources.py", "--data-dir", mirror,
                   "--output", work / "reconcile"]),
        Step("stays", "Length of stay for new bookings", needs=("panel",),
             report="length-of-stay/report.html",
             argv=[py, scripts / "length_of_stay.py", "--panel", work / "panel",
                   "--output", work / "length-of-stay"]),
        Step("bonds", "Money bond and pretrial detention", needs=("panel",),
             report="bonds/report.html",
             argv=[py, scripts / "bond_analysis.py", "--panel", work / "panel",
                   "--output", work / "bonds"]),
        Step("courts", "Court linkage", needs=("panel",), report="courts/report.html",
             argv=[py, scripts / "court_linkage.py", "--data-dir", mirror, "--panel",
                   work / "panel", "--output", work / "courts"]),
        Step("rebooking", "Re-booking after release", needs=("panel",),
             report="rebooking/report.html",
             argv=[py, scripts / "rebooking.py", "--panel", work / "panel",
                   "--output", work / "rebooking"]),
    ] + ([] if args.skip_usage else [
        Step("usage", "Monthly cost projection", report="usage/report.html",
             argv=[py, scripts / "usage_report.py", "--output", work / "usage",
                   "--project", args.project, "--target", str(args.cost_target)]),
    ])


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--mirror", type=Path, default=ROOT / "data" / "snapshots" / "current",
                        help="Local archive mirror to refresh and read")
    parser.add_argument("--output-root", type=Path, default=ROOT / "data" / "analysis" / "weekly",
                        help="Folder that receives one dated subfolder per run")
    parser.add_argument("--baseline", type=Path,
                        default=ROOT / "data" / "analysis" / "baseline" / "summary.json",
                        help="Earlier profile summary to include in trends, if present")
    parser.add_argument("--bucket", default=BUCKET)
    parser.add_argument("--project", default=PROJECT)
    parser.add_argument("--skip-sync", action="store_true",
                        help="Use the mirror as it is (no download, no staleness limit)")
    parser.add_argument("--max-age-hours", type=float, default=3.0,
                        help="Fail when the newest synced roster slot is older than this")
    parser.add_argument("--cost-target", type=float, default=5.0,
                        help="Monthly cost target in USD for the usage report")
    parser.add_argument("--skip-usage", action="store_true",
                        help="Skip the cost projection (it reads Cloud Monitoring)")
    args = parser.parse_args()

    runtime = ROOT / ".runtime"
    runtime.mkdir(exist_ok=True)
    lock = FileLock(runtime / "weekly-analysis.lock")
    try:
        lock.acquire(timeout=0)
    except Timeout:
        print("Another weekly analysis run is in progress.", file=sys.stderr)
        return 2
    try:
        args.output_root.mkdir(parents=True, exist_ok=True)
        args.mirror.mkdir(parents=True, exist_ok=True)
        work = work_folder(args.output_root)
        work.mkdir()
        snapshot = {"mirror": str(args.mirror), "synced": False, "latest_iml_slot": None}
        steps = build_steps(args, work, snapshot)
        started = datetime.now(timezone.utc)
        results = run_steps(steps, work / "logs", cwd=ROOT)
        readouts(work, steps, results)
        newest = snapshot["latest_iml_slot"]
        day = central_date(datetime.fromisoformat(newest) if newest else None, CHICAGO)
        failed = [name for name, result in results.items() if result["status"] != "ok"]
        run = {
            "date": day.isoformat(),
            "status": "complete" if not failed else "incomplete",
            "started_at": started.isoformat(),
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "snapshot": snapshot,
            "steps": results,
            "not_ok": failed,
        }
        write_run(work, run, steps)
        final = finalize(work, args.output_root / day.isoformat())
        for name, result in results.items():
            note = result.get("reason") or result.get("message") or ""
            if "readout" in result:
                readout = result["readout"]
                note = ("readout ready" if readout["ready"] else
                        f"preliminary: {readout['followup_days']} of {readout['needs_days']} days")
            if result.get("alert"):
                note = "ALERT: " + result["alert"]
            print(f"{name:16} {result['status']:8} {result.get('seconds', 0):>7,.1f}s  {note}")
        print(f"{run['status'].upper()}: {final}")
        print(json.dumps({"date": run["date"], "status": run["status"], "not_ok": failed}))
        return 0 if not failed else 1
    finally:
        lock.release()


if __name__ == "__main__":
    sys.exit(main())
