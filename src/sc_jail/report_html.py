"""Shared markup for the private analysis reports (self-contained HTML, aggregates only).

Every report uses the same tokens, 16 px minimum text, and single-series marks so the
reports read as one set. Counts from 1 to 9 are suppressed by the callers with
``profile.suppress`` before they reach these helpers.
"""

import html
from datetime import datetime, timezone

from .profile import suppress

CSS = """
:root{color-scheme:light;--surface:#fcfcfb;--panel:#ffffff;--border:#e4e3df;--text:#0b0b0b;
--text-2:#52514e;--muted:#6b6a66;--s1:#2a78d6;--s2:#eb6834;--track:#f0efec;--grid:#e8e7e3}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){color-scheme:dark;--surface:#1a1a19;
--panel:#222220;--border:#383835;--text:#ffffff;--text-2:#c3c2b7;--muted:#a3a29a;--s1:#3987e5;--s2:#d95926;
--track:#2c2c2a;--grid:#333331}}
:root[data-theme="dark"]{color-scheme:dark;--surface:#1a1a19;--panel:#222220;--border:#383835;--text:#ffffff;
--text-2:#c3c2b7;--muted:#a3a29a;--s1:#3987e5;--s2:#d95926;--track:#2c2c2a;--grid:#333331}
*{box-sizing:border-box}
body{margin:0;background:var(--surface);color:var(--text);font:16px/1.5 Inter,system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:1040px;margin:0 auto;padding:32px 16px 64px}
h1{font-size:28px;line-height:1.25;margin:0 0 4px}h2{font-size:20px;margin:40px 0 8px}
p{max-width:72ch}.lede,.muted{color:var(--text-2)}.muted{font-weight:400}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin:24px 0}
.tile{background:var(--panel);border:1px solid var(--border);border-radius:8px;padding:16px}
.tile .label{color:var(--text-2)}.tile .value{font-size:32px;font-weight:600;line-height:1.2}
.panel{background:var(--panel);border:1px solid var(--border);border-radius:8px;padding:16px;margin:12px 0}
.bars{display:grid;gap:6px}
.bar-row{display:grid;grid-template-columns:minmax(120px,240px) 1fr auto;gap:12px;align-items:center}
.bar-label{color:var(--text-2)}.bar-track{height:20px;display:block}
.bar{display:block;height:20px;background:var(--s1);border-radius:0 4px 4px 0;min-width:0}
.bar-value{font-variant-numeric:tabular-nums;white-space:nowrap;text-align:right;min-width:88px}
.table-wrap{overflow-x:auto}table{border-collapse:collapse;width:100%}
th,td{text-align:left;padding:6px 12px 6px 0;border-bottom:1px solid var(--border);vertical-align:top}
th{color:var(--text-2);font-weight:600}td{font-variant-numeric:tabular-nums}
.legend{display:flex;gap:20px;flex-wrap:wrap;color:var(--text-2);margin-bottom:8px}
.key{display:inline-block;width:16px;height:2px;vertical-align:middle;margin-right:6px}
svg{width:100%;height:auto;display:block}
.chart-scroll{overflow-x:auto}.chart-scroll svg{min-width:960px}.grid{stroke:var(--grid);stroke-width:1}
.tick{fill:var(--muted);font-size:16px}.series{fill:none;stroke-width:2;stroke-linejoin:round;stroke-linecap:round}
.series.s1{stroke:var(--s1)}.series.s2{stroke:var(--s2)}.dot{stroke:var(--panel);stroke-width:2}
.dot.s1{fill:var(--s1)}.dot.s2{fill:var(--s2)}.hit{fill:transparent}.hit:hover{fill:var(--grid);fill-opacity:.5}
ul.notes li{margin:6px 0;max-width:72ch}
@media (max-width:600px){.bar-row{grid-template-columns:1fr auto}.bar-track{grid-column:1/-1;order:3}}
"""
# Additions for the analysis reports; kept separate so the profile report stays unchanged.
EXTRA_CSS = """
.notice{background:var(--panel);border:1px solid var(--border);border-left:4px solid var(--s2);
border-radius:8px;padding:12px 16px;margin:16px 0;max-width:72ch}
.ok{color:var(--text-2)}.fail{font-weight:600}
.chart-scroll svg.compact{min-width:640px}
"""


def fmt(value):
    return f"{value:,}" if isinstance(value, int) else html.escape(str(value))


def pct(part, whole):
    return f"{part / whole:.0%}" if whole else "–"


def bars(rows, *, total=None):
    """Single-series horizontal bars; identity is the row label, not color."""
    peak = max((r["count"] for r in rows), default=0) or 1
    out = ['<div class="bars" role="list">']
    for row in rows:
        count, shown = row["count"], suppress(row["count"])
        width = 0 if isinstance(shown, str) else 100 * count / peak
        share = f" · {pct(count, total)}" if total and not isinstance(shown, str) else ""
        label = html.escape(row["label"])
        out.append(
            f'<div class="bar-row" role="listitem" title="{label}: {fmt(shown)}{share}">'
            f'<span class="bar-label">{label}</span>'
            f'<span class="bar-track"><span class="bar" style="width:{width:.2f}%"></span></span>'
            f'<span class="bar-value">{fmt(shown)}<span class="muted">{share}</span></span></div>'
        )
    out.append("</div>")
    return "".join(out)


def table(headers, rows):
    head = "".join(f"<th>{html.escape(h)}</th>" for h in headers)
    body = "".join(
        "<tr>" + "".join(f"<td>{fmt(v)}</td>" for v in row) + "</tr>" for row in rows
    )
    return f'<div class="table-wrap"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def tiles(items):
    cells = "".join(
        f'<div class="tile"><div class="label">{html.escape(label)}</div>'
        f'<div class="value">{html.escape(value)}</div></div>'
        for label, value in items
    )
    return f'<div class="tiles">{cells}</div>'


def notes(items):
    return '<ul class="notes">' + "".join(f"<li>{item}</li>" for item in items) + "</ul>"


def notice(text):
    return f'<div class="notice" role="note">{text}</div>'


def share_text(value):
    """A probability or share as a whole percentage, or a dash when unavailable."""
    return "–" if value is None else f"{value:.0%}"


def days_text(value):
    return "not reached" if value is None else f"{value:,.0f} days"


def step_chart(curves, *, horizon, label="Share still held"):
    """Kaplan-Meier style step curves (value 1 → 0) against days, one line per curve.

    ``curves`` is a list of (name, [(day, value), ...]) with at most two entries so each
    line keeps a distinct, labelled color; more strata belong in a table instead.
    """
    w, h, left, right, top, bottom = 960, 320, 64, 16, 16, 44
    horizon = max(horizon, 1)

    def x(day):
        return left + (w - left - right) * min(day, horizon) / horizon

    def y(value):
        return top + (h - top - bottom) * (1 - value)

    parts = [f'<svg class="compact" viewBox="0 0 {w} {h}" role="img" aria-label="{html.escape(label)}">']
    for tick in (0, 0.25, 0.5, 0.75, 1):
        parts.append(f'<line class="grid" x1="{left}" x2="{w - right}" y1="{y(tick):.1f}" y2="{y(tick):.1f}"/>')
        parts.append(f'<text class="tick" x="{left - 8}" y="{y(tick) + 5:.1f}" text-anchor="end">{tick:.0%}</text>')
    step = max(1, round(horizon / 8))
    for day in range(0, int(horizon) + 1, step):
        parts.append(f'<text class="tick" x="{x(day):.1f}" y="{h - 14}" text-anchor="middle">{day}</text>')
    parts.append(f'<text class="tick" x="{w - right}" y="{h - 14}" text-anchor="end">days</text>')
    for index, (_, points) in enumerate(curves[:2], start=1):
        path, previous = [], 1.0
        for day, value in points:
            if day > horizon:
                break
            path += [f"{x(day):.1f},{y(previous):.1f}", f"{x(day):.1f},{y(value):.1f}"]
            previous = value
        path.append(f"{x(horizon):.1f},{y(previous):.1f}")
        parts.append(f'<polyline class="series s{index}" points="{x(0):.1f},{y(1):.1f} {" ".join(path)}"/>')
    parts.append("</svg>")
    legend = "".join(
        f'<span><span class="key" style="background:var(--s{i})"></span>{html.escape(name)}</span>'
        for i, (name, _) in enumerate(curves[:2], start=1)
    )
    return f'<div class="legend">{legend}</div><div class="chart-scroll">{"".join(parts)}</div>'


def document(title, heading, lede, body, *, generated=None):
    generated = generated or datetime.now(timezone.utc)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap" rel="stylesheet">
<style>{CSS}{EXTRA_CSS}</style></head><body><main>
<h1>{html.escape(heading)}</h1>
<p class="lede">{lede}</p>
{body}
<p class="muted">Generated {generated.strftime('%Y-%m-%d %H:%M')} UTC from a private local archive copy.
Aggregate counts only; counts from 1 to 9 are shown as “&lt;10”.</p>
</main></body></html>
"""
