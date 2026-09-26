"""Project the deployed project's monthly cost against a target (JSON and HTML).

    python scripts/usage_report.py --output DIR [--target 5] [--days 7]

Reads Cloud Monitoring (Cloud Run billable instance time and requests, Storage bytes and
operations), the Cloud Run service sizes, the Artifact Registry repository size, and the
Scheduler job list, using the signed-in gcloud account. It changes nothing and never
reads archive contents. The billing console remains the authority for actual charges.
"""

import argparse
import html
import json
import shutil
import statistics
import subprocess
import sys
import urllib.parse
import urllib.request
from datetime import datetime, time, timedelta, timezone
from pathlib import Path

from sc_jail.report_html import document, notes, notice, table, tiles
from sc_jail.usage import FREE, PRICES, project, usage

ROOT = Path(__file__).resolve().parents[1]
PROJECT = "sc-jail-research-20260922"
REGION = "us-central1"
SERVICES = ("sc-jail-collector", "sc-jail-dashboard")
LABELS = {
    "run_cpu_second": "Cloud Run CPU (vCPU-seconds)",
    "run_gib_second": "Cloud Run memory (GiB-seconds)",
    "run_request": "Cloud Run requests",
    "storage_gib_month": "Storage (GiB, incl. soft-deleted and backup)",
    "class_a": "Storage Class A operations",
    "class_b": "Storage Class B operations",
    "registry_gib_month": "Container images (GiB)",
    "scheduler_job": "Scheduler jobs",
}


def gcloud(*args):
    exe = shutil.which("gcloud") or str(ROOT / ".runtime" / "google-cloud-sdk" / "bin" / "gcloud.cmd")
    result = subprocess.run([exe, *args], capture_output=True, text=True, timeout=300)
    if result.returncode:
        raise RuntimeError(f"gcloud {' '.join(args[:3])} failed: {result.stderr.strip()[-300:]}")
    return result.stdout


def monitoring(token, project, metric_filter, start, end, group_by, aligner="ALIGN_SUM"):
    query = urllib.parse.urlencode([
        ("filter", metric_filter),
        ("interval.startTime", start.isoformat().replace("+00:00", "Z")),
        ("interval.endTime", end.isoformat().replace("+00:00", "Z")),
        ("aggregation.alignmentPeriod", "86400s"),
        ("aggregation.perSeriesAligner", aligner),
        ("aggregation.crossSeriesReducer", "REDUCE_SUM"),
    ] + [("aggregation.groupByFields", field) for field in group_by])
    request = urllib.request.Request(
        f"https://monitoring.googleapis.com/v3/projects/{project}/timeSeries?{query}",
        headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(request, timeout=120) as response:
        return json.loads(response.read()).get("timeSeries", [])


def value(point):
    v = point["value"]
    return float(v.get("doubleValue", v.get("int64Value", 0)))


def daily_median(series, label):
    """{label value: median per full day}; the median ignores a partial first day."""
    out = {}
    for s in series:
        key = s["resource"]["labels"].get(label) or s["metric"].get("labels", {}).get(label)
        points = [value(p) for p in s.get("points", [])]
        if points:
            out[key] = statistics.median(points)
    return out


def service_size(name, project):
    spec = json.loads(gcloud("run", "services", "describe", name, "--region", REGION,
                             "--project", project, "--format", "json"))
    limits = spec["spec"]["template"]["spec"]["containers"][0]["resources"]["limits"]
    cpu = limits.get("cpu", "1")
    vcpu = float(cpu[:-1]) / 1000 if cpu.endswith("m") else float(cpu)
    memory = limits.get("memory", "512Mi")
    units = {"Mi": 1 / 1024, "Gi": 1.0, "M": 1e6 / 1024 ** 3, "G": 1e9 / 1024 ** 3}
    suffix = next(s for s in sorted(units, key=len, reverse=True) if memory.endswith(s))
    return vcpu, float(memory[: -len(suffix)]) * units[suffix]


def measure(project, days):
    token = gcloud("auth", "print-access-token").strip()
    end = datetime.combine(datetime.now(timezone.utc).date(), time(), timezone.utc)
    start = end - timedelta(days=days)
    seconds = daily_median(monitoring(token, project, 'metric.type="run.googleapis.com/container/'
                                    'billable_instance_time"', start, end,
                                    ["resource.labels.service_name"]), "service_name")
    requests = daily_median(monitoring(token, project, 'metric.type="run.googleapis.com/'
                                     'request_count"', start, end,
                                     ["resource.labels.service_name"]), "service_name")
    services = {}
    for name in SERVICES:
        vcpu, gib = service_size(name, project)
        services[name] = {"instance_seconds_per_day": round(seconds.get(name, 0.0), 1),
                          "requests_per_day": round(requests.get(name, 0.0), 1),
                          "vcpu": vcpu, "gib": gib}
    stored = monitoring(token, project, 'metric.type="storage.googleapis.com/storage/v2/total_bytes"',
                        end - timedelta(days=2), end, ["resource.labels.bucket_name",
                                                       "metric.labels.type"], aligner="ALIGN_MAX")
    by_kind, live_history = {}, {}
    for s in stored:
        points = sorted(s.get("points", []), key=lambda p: p["interval"]["endTime"])
        if points:
            kind = s["metric"]["labels"].get("type", "unknown")
            by_kind[kind] = by_kind.get(kind, 0.0) + value(points[-1])
    growth_series = monitoring(token, project, 'metric.type="storage.googleapis.com/storage/v2/'
                               'total_bytes" AND metric.labels.type="live-object"',
                               start, end, ["project"], aligner="ALIGN_MAX")
    for s in growth_series:
        for p in s.get("points", []):
            live_history[p["interval"]["endTime"][:10]] = value(p)
    methods = daily_median(monitoring(token, project, 'metric.type="storage.googleapis.com/api/'
                                    'request_count"', start, end, ["metric.labels.method"]),
                         "method")
    # The list output carries sizeBytes; describe omits it.
    repositories = json.loads(gcloud("artifacts", "repositories", "list", "--location", REGION,
                                     "--project", project, "--format", "json(name,sizeBytes)"))
    jobs = [line for line in gcloud("scheduler", "jobs", "list", "--location", REGION, "--project",
                                    project, "--format", "value(name)").splitlines() if line]
    history = sorted(live_history.items())
    growth = ((history[-1][1] - history[0][1]) / (len(history) - 1)) if len(history) > 1 else None
    return {
        "measured_days": [start.date().isoformat(), (end - timedelta(days=1)).date().isoformat()],
        "services": services,
        "stored_bytes_by_type": {k: round(v) for k, v in by_kind.items()},
        "live_bytes_growth_per_day": round(growth) if growth is not None else None,
        "storage_operations_per_day": {k: round(v, 1) for k, v in methods.items()},
        "registry_bytes": sum(int(r.get("sizeBytes") or 0) for r in repositories),
        "scheduler_jobs": len(jobs),
    }


def render(result):
    p = result["projection"]
    m = result["measured"]
    within = p["within_target_either_way"]
    status = (notice(f"<strong>Within the ${p['target']:,.2f} target even without free allowances.</strong>")
              if within else notice(
        f"<strong>Check the billing console.</strong> Projected cost is ${p['total_with_free_allowances']:,.2f} "
        f"a month if this project receives the billing account's free allowances, but "
        f"${p['total_without_free_allowances']:,.2f} if other projects on the account have used them, "
        f"which is over the ${p['target']:,.2f} target."))
    rows = []
    for item, amount in p["quantities"].items():
        rows.append([LABELS[item], f"{amount:,.1f}", f"{FREE[item]:,}",
                     f"{p['free_allowance_used'][item]:.0%}",
                     f"${p['cost_with_free_allowances'][item]:,.2f}",
                     f"${p['cost_without_free_allowances'][item]:,.2f}"])
    service_rows = [[name, f"{s['instance_seconds_per_day']:,.0f}", f"{s['requests_per_day']:,.0f}",
                     f"{s['vcpu']:g}", f"{s['gib'] * 1024:,.0f} MiB"] for name, s in m["services"].items()]
    growth = m["live_bytes_growth_per_day"]
    outlook = result["storage_outlook"]
    body = f"""{status}
{tiles([("Projected monthly cost", f"${p['total_with_free_allowances']:,.2f}"),
        ("Without free allowances", f"${p['total_without_free_allowances']:,.2f}"),
        ("Target", f"${p['target']:,.2f}"),
        ("Cloud Run CPU allowance used", f"{p['free_allowance_used']['run_cpu_second']:.0%}")])}
<h2>Projected month</h2>
<div class="panel">{table(["Item", "Per month", "Free allowance", "Allowance used", "Cost with allowance",
                           "Cost without"], rows)}</div>
<h2>Measured</h2>
<p>Daily medians over {html.escape(m['measured_days'][0])} to {html.escape(m['measured_days'][1])} (UTC).</p>
<div class="panel">{table(["Cloud Run service", "Billable seconds a day", "Requests a day", "vCPU",
                           "Memory"], service_rows)}</div>
<p>Stored now: {', '.join(f'{k} {v / 1e6:,.0f} MB' for k, v in m['stored_bytes_by_type'].items())}.
{f'Live data grows about {growth / 1e6:,.0f} MB a day across both buckets.' if growth else ''}
{f"At that rate storage passes the 5 GiB free allowance in about {outlook['months_to_free_limit']:,.1f} months and would cost about ${outlook['cost_in_12_months']:,.2f} a month a year from now." if outlook else ''}</p>
<h2>Method and limits</h2>
{notes([
    "List prices for us-central1 from the Cloud Billing Catalog (checked 2026-09-26), before taxes, "
    "credits, or discounts. The billing console is the authority for actual charges.",
    "Free allowances belong to the billing account, not the project: other projects on the same "
    "account can use them first, which is why both projections are shown.",
    "Cloud Run is billed per request (CPU and memory only while handling requests), so cost follows "
    "collection time. Storage includes soft-deleted objects (kept 7 days) and the backup bucket.",
    "Small items not shown: Monitoring uptime checks and logs (within free limits), builds on deploy, "
    "and downloads by the weekly mirror (within the 100 GiB monthly free egress).",
])}"""
    return document("Cost Projection", "Monthly cost projection", "Measured use of the deployed "
                    "collector, dashboard, and storage, projected to a month at list prices.", body)


def alert(projection):
    """A short warning when either projection nears or passes the target, else None."""
    target = projection["target"]
    with_free = projection["total_with_free_allowances"]
    without = projection["total_without_free_allowances"]
    if with_free >= 0.8 * target:
        return f"Projected ${with_free:,.2f}/month is at least 80% of the ${target:,.2f} target"
    if without >= target:
        return (f"${without:,.2f}/month if other projects use the billing account's free "
                f"allowances; confirm this project's charges in the billing console")
    return None


def storage_outlook(quantities, growth_per_day):
    if not growth_per_day or growth_per_day <= 0:
        return None
    gib_per_month = growth_per_day * 30.44 / 1024 ** 3
    now = quantities["storage_gib_month"]
    months = max(0.0, (FREE["storage_gib_month"] - now) / gib_per_month)
    later = now + 12 * gib_per_month
    return {"gib_now": round(now, 2), "gib_per_month": round(gib_per_month, 2),
            "months_to_free_limit": round(months, 1),
            "cost_in_12_months": round(max(0.0, later - FREE["storage_gib_month"])
                                       * PRICES["storage_gib_month"], 2)}


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--project", default=PROJECT)
    parser.add_argument("--target", type=float, default=5.0, help="Monthly target in USD")
    parser.add_argument("--days", type=int, default=7, help="Full days of usage to average")
    args = parser.parse_args()
    measured = measure(args.project, args.days)
    stored = sum(measured["stored_bytes_by_type"].values())
    quantities = usage(measured["services"], stored, measured["storage_operations_per_day"],
                       measured["registry_bytes"], measured["scheduler_jobs"])
    projection = project(quantities, args.target)
    result = {"measured": measured, "projection": projection,
              "storage_outlook": storage_outlook(quantities, measured["live_bytes_growth_per_day"]),
              "alert": alert(projection)}
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "summary.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    (args.output / "report.html").write_text(render(result), encoding="utf-8")
    p = result["projection"]
    print(f"Projected ${p['total_with_free_allowances']:.2f}/month with free allowances, "
          f"${p['total_without_free_allowances']:.2f} without (target ${args.target:.2f}); "
          f"wrote {args.output}")
    if result["alert"]:
        print("ALERT: " + result["alert"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
