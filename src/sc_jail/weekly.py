"""Weekly private analysis run: refresh a local archive mirror, then build each product.

Each product runs as its own script in a subprocess, so one failure cannot corrupt
another product's output, and every step's log, exit status, and duration are recorded
in ``run.json``. Steps that need the booking panel are skipped when the panel fails its
population check, because later analysis must not use an unvalidated panel. Outputs are
written to a temporary folder and moved into place at the end; an earlier folder for
the same date is kept under a ``.previous-`` name rather than deleted.
"""

import html
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Callable

from .storage import LocalStore

DATED = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@dataclass
class Step:
    name: str
    title: str
    argv: list | None = None
    call: Callable[[Path], tuple[int, str]] | None = None
    needs: tuple = ()
    report: str | None = None
    timeout: float = 3 * 3600
    notes: list = field(default_factory=list)


def latest_slot(data_dir, source):
    """The newest committed observation slot for a source in a local archive copy."""
    prefix = f"private/observations/{source}/"
    newest = None
    for key in LocalStore(data_dir).keys(prefix):
        match = re.search(r"/(\d{4})/(\d{2})/(\d{2})/(\d{2})(\d{2})\.json\.gz$", key)
        if match:
            slot = datetime(*map(int, match.groups()), tzinfo=timezone.utc)
            newest = slot if newest is None or slot > newest else newest
    return newest


def run_subprocess(argv, log_path, *, cwd, timeout):
    """Run one product script with its output captured to a log; returns the exit code."""
    flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    with open(log_path, "w", encoding="utf-8", errors="replace") as log:
        log.write("$ " + subprocess.list2cmdline([str(a) for a in argv]) + "\n\n")
        log.flush()
        try:
            return subprocess.run([str(a) for a in argv], cwd=cwd, stdout=log,
                                  stderr=subprocess.STDOUT, timeout=timeout,
                                  creationflags=flags).returncode
        except subprocess.TimeoutExpired:
            log.write(f"\nTimed out after {timeout:,.0f} seconds\n")
            return 124
        except OSError as error:
            log.write(f"\nCould not start: {error}\n")
            return 127


def run_steps(steps, log_dir, *, cwd, runner=run_subprocess, clock=time.monotonic):
    """Run steps in order; a step whose prerequisite did not succeed is skipped."""
    results = {}
    log_dir.mkdir(parents=True, exist_ok=True)
    for step in steps:
        blocked = [name for name in step.needs if results.get(name, {}).get("status") != "ok"]
        if blocked:
            results[step.name] = {"status": "skipped", "reason": "needs " + ", ".join(blocked)}
            continue
        log_path = log_dir / f"{step.name}.log"
        started = clock()
        message = ""
        try:
            if step.call is not None:
                code, message = step.call(log_path)
            else:
                code = runner(step.argv, log_path, cwd=cwd, timeout=step.timeout)
        except Exception as error:  # a failed step is recorded; later steps still run
            code, message = 1, f"{type(error).__name__}: {error}"
            with open(log_path, "a", encoding="utf-8") as log:
                log.write(f"\n{message}\n")
        results[step.name] = {
            "status": "ok" if code == 0 else "failed",
            "exit_code": code,
            "seconds": round(clock() - started, 1),
            "log": f"logs/{log_path.name}",
        }
        if message:
            results[step.name]["message"] = message
    return results


def readouts(work_dir, steps, results):
    """Attach each analysis's readiness, read from its summary.json, to the run results."""
    for step in steps:
        result = results.get(step.name, {})
        if result.get("status") != "ok" or not step.report:
            continue
        try:
            summary = json.loads((work_dir / Path(step.report).parent / "summary.json")
                                 .read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if isinstance(summary, dict) and "readout_ready" in summary:
            result["readout"] = {"ready": summary["readout_ready"],
                                 "followup_days": summary.get("followup_days"),
                                 "needs_days": summary.get("readout_days")}
        if isinstance(summary, dict) and summary.get("alert"):
            result["alert"] = summary["alert"]
    return results


def finalize(work_dir, final_dir):
    """Move a finished run into place, keeping any earlier run for the same date."""
    if final_dir.exists():
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        final_dir.rename(final_dir.with_name(f"{final_dir.name}.previous-{stamp}"))
    work_dir.rename(final_dir)
    return final_dir


def dated_runs(root):
    """Completed weekly folders (exactly YYYY-MM-DD), oldest first."""
    if not root.is_dir():
        return []
    return sorted(p for p in root.iterdir() if p.is_dir() and DATED.match(p.name))


def render_index(run, steps):
    """A small private index for one run: status, timing, and links to each report."""
    rows = []
    for step in steps:
        result = run["steps"].get(step.name, {})
        status = result.get("status", "not run")
        detail = result.get("reason") or result.get("message") or ""
        if "readout" in result:
            readout = result["readout"]
            detail = ("Readout ready" if readout["ready"] else
                      f"Preliminary: {readout['followup_days']} of {readout['needs_days']} days "
                      "of collection needed for the first readout")
        if result.get("alert"):
            detail = "Alert: " + result["alert"]
        link = (f'<a href="{html.escape(step.report)}">{html.escape(step.title)}</a>'
                if step.report and status == "ok" else html.escape(step.title))
        seconds = f"{result['seconds']:,.0f} s" if "seconds" in result else "–"
        log = (f'<a href="{html.escape(result["log"])}">log</a>' if "log" in result else "")
        rows.append(f"<tr><td>{link}</td><td class=\"{'ok' if status == 'ok' else 'fail'}\">"
                    f"{html.escape(status)}</td><td>{seconds}</td><td>{log}</td>"
                    f"<td>{html.escape(detail)}</td></tr>")
    snapshot = run.get("snapshot", {})
    facts = [
        f"Run {html.escape(run['status'])} · started {html.escape(run['started_at'][:16])} UTC",
        f"Archive mirror through {html.escape(str(snapshot.get('latest_iml_slot') or 'unknown'))}",
        f"Synced from the cloud archive: {'yes' if snapshot.get('synced') else 'no'}",
    ]
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Weekly Analysis Run</title>
<style>body{{margin:0;font:16px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif;background:#fcfcfb;color:#0b0b0b}}
@media (prefers-color-scheme:dark){{body{{background:#1a1a19;color:#fff}}a{{color:#8ab8f0}}}}
main{{max-width:1040px;margin:0 auto;padding:32px 16px}}table{{border-collapse:collapse;width:100%}}
th,td{{text-align:left;padding:6px 12px 6px 0;border-bottom:1px solid #e4e3df;vertical-align:top}}
.fail{{font-weight:600}}.wrap{{overflow-x:auto}}</style></head><body><main>
<h1>Weekly analysis run, {html.escape(run['date'])}</h1>
<p>{'<br>'.join(facts)}</p>
<div class="wrap"><table><thead><tr><th>Product</th><th>Status</th><th>Time</th><th>Log</th>
<th>Note</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>
<p>Private outputs from a local archive copy. Reports show aggregates only; JSON files and
the booking panel contain person-level records and must stay under the ignored data folder.</p>
</main></body></html>
"""


def write_run(work_dir, run, steps):
    (work_dir / "run.json").write_text(json.dumps(run, indent=2), encoding="utf-8")
    (work_dir / "index.html").write_text(render_index(run, steps), encoding="utf-8")


def central_date(moment, zone) -> date:
    return moment.astimezone(zone).date() if moment else datetime.now(zone).date()


def work_folder(root):
    """A private in-progress folder; its date is known only after the mirror is checked."""
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return root / f".partial-{stamp}-{os.getpid()}"
