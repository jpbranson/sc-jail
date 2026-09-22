import csv
import io
import os
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from flask import Flask, Response, jsonify, render_template, request
from matplotlib import dates as mdates
from matplotlib import rc_context
from matplotlib.backends.backend_svg import FigureCanvasSVG
from matplotlib.figure import Figure

from .pipeline import collect_all, empty_index
from .storage import Conflict, read_json

CHICAGO = ZoneInfo("America/Chicago")
LABELS = {"iml": "IML roster: people", "xfer": "In-jail report: bookings"}
COLORS = {"iml": "#337ab7", "xfer": "#d17a22"}
_plot_lock = threading.Lock()


def local_time(value):
    if not value:
        return "Not yet collected"
    return datetime.fromisoformat(value).astimezone(CHICAGO).strftime("%b %d, %I:%M %p %Z")


def source_health(source, now):
    last = source.get("last_success")
    if not last:
        return "No data", "warning"
    if source.get("error"):
        return "Collection failed", "warning"
    if (now - datetime.fromisoformat(last)).total_seconds() > 1800:
        return "Collection overdue", "warning"
    return "Collecting normally", "ok"


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
                points = [p for p in points if p.get("arrivals") is not None]
                if points:
                    times = [datetime.fromisoformat(p["observed_at"]) for p in points]
                    ax.bar(
                        times,
                        [p["arrivals"] for p in points],
                        width=5 / 1440,
                        color=COLORS["iml"],
                        label="Appeared",
                        align="edge",
                    )
                    ax.bar(
                        times,
                        [-p["departures"] for p in points],
                        width=-5 / 1440,
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


def create_app(config, store):
    app = Flask(__name__)
    # Ship the small, trusted display assets with the HTML so a missed asset
    # request cannot leave the dashboard unstyled or prevent chart loading.
    asset_root = Path(app.static_folder)
    app.jinja_env.globals["dashboard_assets"] = {
        kind: (asset_root / f"dashboard.{kind}").read_text(encoding="utf-8")
        for kind in ("css", "js")
    }
    app.jinja_env.filters["localtime"] = local_time
    app.jinja_env.filters["number"] = lambda v: f"{v:,}" if v is not None else "â€”"
    cache, cache_lock = {"at": 0, "data": empty_index()}, threading.Lock()

    def state():
        with cache_lock:
            if time.monotonic() - cache["at"] > 30:
                cache["data"], _ = read_json(store, "public/index.json", empty_index())
                cache["at"] = time.monotonic()
            return cache["data"]

    def days_arg():
        try:
            days = int(request.args.get("days", "7"))
        except ValueError:
            days = 7
        return days if days in (1, 7, 30, 90) else 7

    @app.after_request
    def headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Cache-Control"] = (
            "no-store" if response.status_code >= 400 else "public, max-age=30"
        )
        return response

    @app.get("/")
    def dashboard():
        data = state()
        now = datetime.now(timezone.utc)
        sources = data["sources"]
        health = {name: source_health(sources.get(name, {}), now) for name in LABELS}
        return render_template(
            "dashboard.html",
            index=data,
            sources=sources,
            health=health,
            days=days_arg(),
            labels=LABELS,
            supplements=data.get("supplements", {}),
            repeats=data.get("repeat_visits", {}),
            supplemental_health={name: source_health(data.get("supplements", {}).get(name, {}), now)
                                 for name in ("iml_details", "xfer_courts")},
        )

    @app.get("/chart/<kind>.svg")
    def chart(kind):
        if kind not in ("population", "changes", "repeat-visits", "visit-intervals"):
            return "Not found", 404
        try:
            width = int(request.args.get("width", "1000"))
        except ValueError:
            width = 1000
        data = state()
        svg = (
            make_repeat_chart(
                data.get("repeat_visits", {}), width, intervals=kind == "visit-intervals"
            )
            if kind in ("repeat-visits", "visit-intervals")
            else make_chart(data, days_arg(), width, changes=kind == "changes")
        )
        return Response(svg, mimetype="image/svg+xml")

    @app.get("/history.csv")
    def history():
        cutoff = datetime.now(timezone.utc) - timedelta(days=days_arg())
        out = io.StringIO(newline="")
        fields = [
            "source",
            "unit",
            "slot",
            "observed_at",
            "finished_at",
            "source_updated_at",
            "population",
            "arrivals",
            "departures",
            "comparison_minutes",
            "listed_people",
            "listed_records",
            "charge_rows",
            "people_or_bookings_seen",
        ]
        writer = csv.DictWriter(out, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for name, source in state()["sources"].items():
            for point in source.get("history", []):
                if datetime.fromisoformat(point["observed_at"]) >= cutoff:
                    writer.writerow(
                        {"source": name, "unit": "people" if name == "iml" else "bookings", **point}
                    )
        return Response(
            out.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": 'attachment; filename="jail-history.csv"'},
        )

    @app.get("/api/status")
    def status():
        data = state()
        now = datetime.now(timezone.utc)
        return jsonify(
            {
                name: {
                    "status": source_health(data["sources"].get(name, {}), now)[0],
                    "last_success": data["sources"].get(name, {}).get("last_success"),
                    "current": data["sources"].get(name, {}).get("current"),
                }
                for name in LABELS
            }
        )

    @app.get("/api/repeat-visits")
    def repeat_visits():
        return jsonify(state().get("repeat_visits", {}))

    @app.get("/api/coverage")
    def coverage():
        return jsonify(state().get("supplements", {}))

    @app.get("/health")
    @app.get("/healthz")
    def health():
        return jsonify(status="ok")

    @app.errorhandler(Exception)
    def failure(exc):
        from werkzeug.exceptions import HTTPException

        if isinstance(exc, HTTPException):
            return exc
        app.logger.exception("Dashboard request failed")
        return render_template("unavailable.html"), 503

    return app


def create_collector_app(config, store):
    app = Flask(__name__)

    @app.get("/health")
    @app.get("/healthz")
    def health():
        return jsonify(status="ok")

    @app.post("/collect")
    def collect():
        # Cloud Run IAM protects this separate service; no collection route
        # exists on the public dashboard. Local collection uses the CLI.
        if not os.getenv("K_SERVICE"):
            return jsonify(error="Use the local collect command"), 403
        scheduled = request.headers.get("X-CloudScheduler-ScheduleTime")
        try:
            scheduled_at = (
                datetime.fromisoformat(scheduled.replace("Z", "+00:00")) if scheduled else None
            )
            if scheduled_at is not None and scheduled_at.tzinfo is None:
                raise ValueError("Missing timezone")
        except ValueError:
            return jsonify(error="Invalid schedule time"), 400
        try:
            result = collect_all(config, store, scheduled_at=scheduled_at)
            return jsonify(result), 503 if result["status"] == "failed" else 200
        except Conflict:
            return jsonify(status="busy"), 409

    return app
