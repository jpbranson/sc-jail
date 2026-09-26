"""Write an aggregate population profile (JSON and HTML) from a local archive copy.

Reads the archive selected by --data-dir, never the live bucket, so analysis cannot
modify collection state. Copy the cloud archive first, for example:

    gcloud storage rsync -r gs://BUCKET data/snapshots/YYYY-MM-DD

Counts from 1 to 9 are shown as "<10" in the HTML report; summary.json is private.
"""

import argparse
import gzip
import html
import json
from datetime import datetime, time, timedelta
from pathlib import Path

from sc_jail.exporters import export_details
from sc_jail.iml import CHICAGO
from sc_jail.profile import movement, profile, suppress
from sc_jail.report_html import CSS, bars, fmt, pct, table
from sc_jail.storage import LocalStore, read_json


def population_points(store):
    points = {"iml": [], "xfer": []}
    for key in store.keys("private/observations/"):
        if not key.endswith(".json.gz"):
            continue
        raw, _ = store.read(key)
        manifest = json.loads(gzip.decompress(raw))
        if manifest["source"] in points:
            points[manifest["source"]].append(manifest["point"])
    for series in points.values():
        series.sort(key=lambda p: p["slot"])
    return points


def line_chart(points):
    """IML people and XFER bookings on one count axis, with hourly hover targets."""
    series = {
        name: [(datetime.fromisoformat(p["slot"]), p["population"]) for p in rows]
        for name, rows in points.items()
    }
    everything = [v for rows in series.values() for v in rows]
    if not everything:
        return "<p>No population observations.</p>"
    start = min(t for t, _ in everything)
    end = max(t for t, _ in everything)
    low = min(v for _, v in everything)
    high = max(v for _, v in everything)
    low, high = (low // 100) * 100 - 100, (high // 100 + 1) * 100 + 100
    w, h, left, right, top, bottom = 960, 320, 64, 16, 16, 40
    span = (end - start).total_seconds() or 1

    def x(t):
        return left + (w - left - right) * (t - start).total_seconds() / span

    def y(v):
        return top + (h - top - bottom) * (high - v) / (high - low)

    parts = [f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="Population by collection time">']
    step = 100 if high - low <= 800 else 200
    for tick in range(int(low), int(high) + 1, step):
        parts.append(f'<line class="grid" x1="{left}" x2="{w - right}" y1="{y(tick):.1f}" y2="{y(tick):.1f}"/>')
        parts.append(f'<text class="tick" x="{left - 8}" y="{y(tick) + 5:.1f}" text-anchor="end">{tick:,}</text>')
    day = start.astimezone(CHICAGO).date() + timedelta(days=1)
    while (midnight := datetime.combine(day, time(), CHICAGO)) <= end:
        parts.append(f'<text class="tick" x="{x(midnight):.1f}" y="{h - 12}" '
                     f'text-anchor="middle">{day.strftime("%b")} {day.day}</text>')
        day += timedelta(days=1)
    for index, (name, rows) in enumerate(series.items(), start=1):
        path = " ".join(f"{x(t):.1f},{y(v):.1f}" for t, v in rows)
        parts.append(f'<polyline class="series s{index}" points="{path}"/>')
        if rows:
            t, v = rows[-1]
            parts.append(f'<circle class="dot s{index}" cx="{x(t):.1f}" cy="{y(v):.1f}" r="4"/>')
    # One hover target per hour, reporting the nearest observation from each source.
    hours = sorted({t.replace(minute=0) for t, _ in everything})
    lookup = {name: dict((t.replace(minute=0), v) for t, v in rows) for name, rows in series.items()}
    width = (w - left - right) / max(len(hours), 1)
    for hour in hours:
        local = hour.astimezone(CHICAGO)
        label = f"{local.strftime('%b')} {local.day}, {local.strftime('%I %p').lstrip('0')} Central"
        names = {"iml": "IML people", "xfer": "XFER bookings"}
        values = " · ".join(
            f"{names[n]} {lookup[n][hour]:,}" if hour in lookup[n] else f"{names[n]} –"
            for n in series
        )
        parts.append(f'<rect class="hit" x="{x(hour) - width / 2:.1f}" y="{top}" width="{width:.1f}" '
                     f'height="{h - top - bottom}"><title>{html.escape(label)}: {values}</title></rect>')
    parts.append("</svg>")
    return "".join(parts)


def render(summary, points, daily):
    p = summary
    n = p["people"]
    held_by = p["held_by_status"]
    pretrial = held_by.get("No case marked sentenced", {})
    bond = p["money_bond_only"]
    flags = p["flags"]
    status_rows = [
        [label, suppress(count), pct(count, n) if count >= 10 else "–",
         f"{held_by[label]['median_days']:,.0f}" if label in held_by else "–",
         suppress(held_by[label]["over_year"]) if label in held_by else "–"]
        for label, count in p["status"]
    ]
    offenses = [[label.title(), suppress(count), pct(count, n)] for label, count in p["top_offenses"]]
    demo = [[f"Sex: {k}", suppress(v)] for k, v in p["sex"]] + \
           [[f"Race: {k}", suppress(v)] for k, v in p["race"]] + \
           [[f"Ethnicity: {k}", suppress(v)] for k, v in p["ethnicity"]]
    flow_rows = [[d["day"], d["first_seen"], d["released"], d["first_seen"] - d["released"]]
                 for d in daily]
    tiles = [
        ("People listed as held", f"{n:,}"),
        ("Median time held so far", f"{p['held_median_days']:,.0f} days"),
        ("Held more than a year", f"{p['held_over_year_share']:.0%}"),
        ("No case marked sentenced", pct(pretrial.get("people", 0), n)),
    ]
    tile_html = "".join(
        f'<div class="tile"><div class="label">{html.escape(a)}</div><div class="value">{html.escape(b)}</div></div>'
        for a, b in tiles
    )
    avg = (f"Across {len(daily)} complete Central-time days, the roster averaged "
           f"{sum(d['first_seen'] for d in daily) / len(daily):,.0f} new bookings and "
           f"{sum(d['released'] for d in daily) / len(daily):,.0f} releases a day."
           if daily else "No complete day of collection is available yet.")
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Jail Population Profile</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap" rel="stylesheet">
<style>{CSS}</style></head><body><main>
<h1>Shelby County jail population profile</h1>
<p class="lede">People listed as held on {p['as_of']} (Central time), from the Sheriff's public
jail roster and individual record pages. Aggregate counts only; counts from 1 to 9 are shown as “&lt;10”.</p>
<div class="tiles">{tile_html}</div>

<h2>Time held so far</h2>
<p>Days from the listed commitment date to {p['as_of']}. This is a snapshot of who is held
today, so it over-represents long stays; most people booked in a given week leave far sooner.
{pct(flags.get('commitment_missing_or_future', 0), n) if flags.get('commitment_missing_or_future') else 'No'}
records lacked a usable commitment date.</p>
<div class="panel">{bars(p['held'], total=n)}</div>

<h2>Case status</h2>
<p>Based on the status the Sheriff lists on each case's bond entry. “Sentenced” marks a case
with a sentence; the rest are open, have no bond, or have no status listed. Someone can be sentenced on
one case and awaiting trial on another.</p>
<div class="panel">{table(["Status", "People", "Share", "Median days held", "Held over a year"], status_rows)}</div>

<h2>Most serious charge</h2>
<p>Each person is counted once, under the highest grade among their listed charges.
{fmt(suppress(flags.get('violation_charge', 0)))} people have at least one probation, parole, or diversion
violation charge, and {fmt(suppress(flags.get('detainer', 0)))} have a detainer (a hold for another agency).</p>
<div class="panel">{bars(p['grade'], total=n)}</div>

<h2>Most common charges</h2>
<p>People with at least one charge with this description. One person can have several.</p>
<div class="panel">{table(["Charge", "People", "Share of people held"], offenses)}</div>

<h2>People held on money bond alone</h2>
<p>{bond['people']:,} people have only open cases with a court-assessed money bond, no detainer,
and no violation charge. Nothing else in their records says why they're held, so for this group
the bond amount is the visible barrier to release. Their median total bond is ${bond['median']:,.0f};
{fmt(suppress(bond['at_most_5000']))} owe $5,000 or less and {fmt(suppress(bond['at_most_10000']))}
owe $10,000 or less. Totals are the Sheriff's listed grand total, which matched the sum of their case bonds.</p>
<div class="panel">{bars(bond['bands'], total=bond['people'])}</div>

<h2>Next court date</h2>
<p>The earliest court date listed on each person's record. Record pages are refreshed about once a day,
so a date shown as “before today” may already have been replaced.</p>
<div class="panel">{bars(p['court'], total=n)}</div>

<h2>Who is held</h2>
<div class="panel">{bars(p['age'], total=n)}</div>
<div class="panel">{table(["Group", "People"], demo)}</div>

<h2>Population over time</h2>
<p>The two public sources count different things: IML counts people without a release date;
XFER counts bookings in the Sheriff's jail spreadsheet. {avg}</p>
<div class="panel"><div class="legend"><span><span class="key" style="background:var(--s1)"></span>IML people</span>
<span><span class="key" style="background:var(--s2)"></span>XFER bookings</span></div>
<div class="chart-scroll">{line_chart(points)}</div></div>
<div class="panel">{table(["Central date", "New bookings seen", "Releases listed", "Net"], flow_rows)}</div>

<h2>Method and limits</h2>
<ul class="notes">
<li>Source: the archived IML roster at {html.escape(summary['roster_observed_at'])} UTC and the latest archived
record page for each person ({p['roster_current']:,} listed without a release date; {p['missing_details']:,}
without a record page yet).</li>
<li>New bookings are booking numbers first seen on the roster that day; releases use the release date the
roster lists. Both count bookings, not people, and exclude the partial first and last days. Some
15-minute collections were missed before September 22, which delays when a booking is seen but does not
lose it; very short stays between collections can be missed entirely.</li>
<li>Charge grades, bond types, and statuses are published by the Sheriff and may lag court records.
“FM” is treated as the most serious grade because every charge carrying it is a murder charge.</li>
<li>Race, sex, and ethnicity are as recorded by the jail, not self-reported.</li>
<li>The archive began on September 19, 2026, so trends and repeat bookings need more time to be meaningful.</li>
</ul>
</main></body></html>
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data-dir", type=Path, required=True, help="Local archive copy")
    parser.add_argument("--output", type=Path, required=True, help="Output directory")
    args = parser.parse_args()
    if not (args.data_dir / "private").is_dir():
        parser.error(f"{args.data_dir} does not look like an archive copy")
    store = LocalStore(args.data_dir)
    roster, _ = read_json(store, "private/checkpoints/iml.json.gz", {})
    if not roster:
        parser.error("The archive has no IML roster checkpoint")
    observed = datetime.fromisoformat(roster["observed_at"])
    details = list(export_details(store))
    summary = profile(details, roster["state"]["records"], observed.astimezone(CHICAGO).date())
    summary["roster_observed_at"] = observed.strftime("%Y-%m-%d %H:%M")
    points = population_points(store)
    registry, _ = read_json(store, "private/analytics/repeat-visits.json.gz", {})
    daily = movement(registry, CHICAGO) if registry else []
    summary["daily_flows"] = daily
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    (args.output / "report.html").write_text(render(summary, points, daily), encoding="utf-8")
    print(f"Profiled {summary['people']:,} people as of {summary['as_of']}; wrote {args.output}")


if __name__ == "__main__":
    main()
