"""Dashboard-only plotting; collectors never import Matplotlib."""

import io
import threading
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from matplotlib import dates as mdates
from matplotlib import rc_context
from matplotlib.backends.backend_svg import FigureCanvasSVG
from matplotlib.figure import Figure

CHICAGO = ZoneInfo("America/Chicago")
LABELS = {"iml": "IML roster: people", "xfer": "In-jail report: bookings"}
COLORS = {"iml": "#337ab7", "xfer": "#d17a22"}
_plot_lock = threading.Lock()


def change_bins(points, days):
    """Sum observed changes only; missing comparisons never become invented zeros."""
    seconds = 86400 if days >= 30 else 3600 if days >= 7 else 900
    bins = defaultdict(lambda: {"arrivals": 0, "departures": 0})
    for point in points:
        if point.get("arrivals") is None:
            continue
        stamp = datetime.fromisoformat(point["observed_at"])
        key = int(stamp.timestamp()) // seconds * seconds
        bins[key]["arrivals"] += point["arrivals"]
        bins[key]["departures"] += point["departures"]
    return [dict(observed_at=datetime.fromtimestamp(k, timezone.utc).isoformat(), **bins[k])
            for k in sorted(bins)], seconds


def make_chart(index, days, width, *, changes=False):
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    width = max(360, min(1800, width))
    with (
        _plot_lock,
        rc_context(
            {
                "font.family": "sans-serif",
                "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica", "sans-serif"],
                "font.size": 12,
                "axes.labelsize": 12,
                "xtick.labelsize": 12,
                "ytick.labelsize": 12,
                "legend.fontsize": 12,
                "svg.fonttype": "none",
                "axes.unicode_minus": False,
            }
        ),
    ):
        # 12 pt remains 16 CSS px by matching the SVG to its displayed width.
        fig = Figure(figsize=(width / 96, 370 / 96), dpi=96, facecolor="white")
        ax = fig.subplots()
        fig.subplots_adjust(
            left=min(0.22, 72 / width), right=0.97, bottom=0.36 if width < 650 else 0.27, top=0.94
        )
        any_data = False
        for name in ["iml"] if changes else ["iml", "xfer"]:
            points = [
                p
                for p in index["sources"].get(name, {}).get("history", [])
                if datetime.fromisoformat(p["observed_at"]) >= cutoff
            ]
            if changes:
                points, bin_seconds = change_bins(points, days)
                if points:
                    times = [datetime.fromisoformat(p["observed_at"]) for p in points]
                    ax.bar(
                        times,
                        [p["arrivals"] for p in points],
                        width=bin_seconds / 86400 * 0.4,
                        color=COLORS["iml"],
                        label="Appeared",
                        align="edge",
                    )
                    ax.bar(
                        times,
                        [-p["departures"] for p in points],
                        width=-bin_seconds / 86400 * 0.4,
                        color="#737373",
                        label="Disappeared",
                        align="edge",
                    )
                    any_data = True
            elif points:
                xs, ys, previous = [], [], None
                for p in points:
                    stamp = datetime.fromisoformat(p["observed_at"])
                    slot = datetime.fromisoformat(p["slot"])
                    if previous is not None and (slot - previous).total_seconds() > 900:
                        xs.append(stamp)
                        ys.append(float("nan"))
                    xs.append(stamp)
                    ys.append(p["population"])
                    previous = slot
                ax.plot(
                    xs,
                    ys,
                    color=COLORS[name],
                    linewidth=1.8,
                    marker="o",
                    markersize=5 if len(points) < 40 else 0,
                    label=LABELS[name],
                )
                any_data = True
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.set_axisbelow(True)
        ax.grid(axis="both", color="#e8e8e8", linewidth=0.7)
        ax.tick_params(length=0, pad=8)
        if any_data:
            locator = mdates.AutoDateLocator(
                tz=CHICAGO, minticks=2, maxticks=3 if width < 650 else 6
            )
            ax.xaxis.set_major_locator(locator)
            ax.xaxis.set_major_formatter(
                mdates.DateFormatter("%b %d\n%I:%M %p" if days <= 7 else "%b %d", tz=CHICAGO)
            )
            if not changes:
                low, high = ax.get_ylim()
                if high - low < 20:
                    middle = (high + low) / 2
                    ax.set_ylim(middle - 10, middle + 10)
            else:
                ax.axhline(0, color="#aaaaaa", linewidth=0.8)
                if ax.get_ylim()[1] - ax.get_ylim()[0] < 2:
                    ax.set_ylim(-1, 1)
            ax.yaxis.get_major_locator().set_params(integer=True)
            ax.legend(
                loc="upper left",
                bbox_to_anchor=(0, -0.24),
                frameon=False,
                ncol=1 if width < 650 else 2,
                borderaxespad=0,
            )
        else:
            ax.set_xticks([])
            ax.set_yticks([])
            ax.text(
                0.5,
                0.5,
                "Waiting for consecutive\nobservations"
                if changes
                else "History will appear after\nthe first collection",
                ha="center",
                va="center",
                transform=ax.transAxes,
                color="#666666",
            )
        out = io.StringIO()
        FigureCanvasSVG(fig).print_svg(out)
        return out.getvalue()


def make_repeat_chart(summary, width, *, intervals=False):
    width = max(360, min(1800, width))
    with (
        _plot_lock,
        rc_context({
            "font.family": "sans-serif",
            "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica", "sans-serif"],
            "font.size": 12,
            "svg.fonttype": "none",
            "axes.unicode_minus": False,
        }),
    ):
        fig = Figure(figsize=(width / 96, 370 / 96), dpi=96, facecolor="white")
        ax = fig.subplots()
        fig.subplots_adjust(left=125 / width, right=0.94, bottom=0.18, top=0.96)
        data = summary.get("interval_distribution" if intervals else "visit_distribution", [])
        if summary.get("available") and any(row["count"] for row in data):
            values = [row["count"] for row in data]
            positions = list(range(len(data)))
            ax.barh(positions, values, height=0.58, color="#d17a22" if intervals else "#337ab7")
            ax.set_yticks(positions, [row["label"] for row in data])
            ax.invert_yaxis()
            limit = max(values)
            ax.set_xlim(0, max(1.5, limit * 1.25))
            for position, value in enumerate(values):
                ax.text(value + limit * 0.025, position, f"{value:,}", va="center")
            from matplotlib.ticker import MaxNLocator

            ax.xaxis.set_major_locator(MaxNLocator(nbins=3 if width < 500 else 5, integer=True))
            ax.set_xlabel("Intervals" if intervals else "People", labelpad=10)
            ax.set_axisbelow(True)
            ax.grid(axis="x", color="#e8e8e8", linewidth=0.7)
        else:
            ax.set_xticks([])
            ax.set_yticks([])
            message = (
                "Repeat-visit history\nis being prepared"
                if not summary.get("available")
                else "No complete intervals\nwith usable dates yet"
                if intervals and summary.get("repeat_people")
                else "No repeat bookings\nobserved yet"
            )
            ax.text(0.5, 0.5, message, ha="center", va="center",
                    transform=ax.transAxes, color="#666666")
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.tick_params(length=0, pad=8)
        out = io.StringIO()
        FigureCanvasSVG(fig).print_svg(out)
        return out.getvalue()

