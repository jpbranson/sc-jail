import csv
import hashlib
import io
import os
import threading
import time
from collections import OrderedDict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from flask import Flask, Response, jsonify, render_template, request

from .pipeline import collect_all, empty_index
from .storage import Conflict, read_json

CHICAGO = ZoneInfo("America/Chicago")
LABELS = {"iml": "IML roster: people", "xfer": "In-jail report: bookings"}


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
    current = source.get("current", {})
    if current.get("pending", 0):
        return "Coverage incomplete", "warning"
    return "Collecting normally", "ok"


def make_chart(*args, **kwargs):
    from .charts import make_chart as render

    return render(*args, **kwargs)


def make_repeat_chart(*args, **kwargs):
    from .charts import make_repeat_chart as render

    return render(*args, **kwargs)


def create_app(config, store):
    app = Flask(__name__)
    # Ship the small, trusted display assets with the HTML so a missed asset
    # request cannot leave the dashboard unstyled or prevent chart loading.
    asset_root = Path(app.static_folder)
    assets = {kind: (asset_root / f"dashboard.{kind}").read_text(encoding="utf-8")
              for kind in ("css", "js")}
    # An open page reloads once when a deployment changes these assets.
    assets["version"] = hashlib.sha256((assets["css"] + assets["js"]).encode()).hexdigest()[:12]
    app.jinja_env.globals["dashboard_assets"] = assets
    app.jinja_env.filters["localtime"] = local_time
    app.jinja_env.filters["number"] = lambda v: f"{v:,}" if v is not None else "\u2014"
    cache = {"next_attempt": 0, "data": None, "version": None, "error": None,
             "loaded_at": None, "failures": 0}
    cache_lock = threading.Lock()
    chart_cache, chart_lock = OrderedDict(), threading.Lock()

    def state():
        with cache_lock:
            if time.monotonic() >= cache["next_attempt"]:
                try:
                    data, version = read_json(store, "public/index.json")
                    if data is None:
                        if cache["data"] is not None:
                            raise ValueError("Previously available index is missing")
                        data = empty_index()
                    if not isinstance(data, dict) or not isinstance(data.get("sources"), dict):
                        raise ValueError("Invalid dashboard index")
                    if cache["data"] is None or version != cache["version"]:
                        cache["data"] = {**data, "_revision": str(version)}
                        cache["version"] = version
                        with chart_lock:
                            chart_cache.clear()
                    cache.update(error=None, failures=0,
                                 loaded_at=datetime.now(timezone.utc).isoformat())
                    cache["next_attempt"] = time.monotonic() + 30
                except Exception:
                    cache["failures"] += 1
                    cache["error"] = "Storage refresh failed; showing the last saved observations"
                    cache["next_attempt"] = time.monotonic() + min(
                        300, 30 * 2 ** min(cache["failures"] - 1, 4)
                    )
                    app.logger.exception("Dashboard index refresh failed")
                    if cache["data"] is None:
                        raise
            if cache["data"] is None:
                raise RuntimeError("No validated dashboard index is available")
            return cache["data"]

    def chart_version(data):
        """Changes whenever a chart can: new index data or the next 5-minute render window."""
        return f"{data['_revision']}.{int(time.time()) // 300}"

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
            "no-store" if response.status_code >= 400 or cache["error"] else "public, max-age=30"
        )
        if cache["error"]:
            response.headers["X-Data-Stale"] = "true"
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
            chart_version=chart_version(data),
            storage_error=cache["error"],
            storage_loaded_at=cache["loaded_at"],
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
        width = max(360, min(1800, width // 60 * 60))
        data = state()
        days = days_arg()
        key = (chart_version(data), kind, days, width)
        with chart_lock:
            svg = chart_cache.get(key)
            if svg is None:
                svg = (
                    make_repeat_chart(
                        data.get("repeat_visits", {}), width, intervals=kind == "visit-intervals"
                    )
                    if kind in ("repeat-visits", "visit-intervals")
                    else make_chart(data, days, width, changes=kind == "changes")
                )
                chart_cache[key] = svg
                while len(chart_cache) > 32:
                    chart_cache.popitem(last=False)
            chart_cache.move_to_end(key)
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

    @app.get("/api/freshness")
    @app.get("/api/freshness/<product>")
    def freshness(product=None):
        data = state()
        now = datetime.now(timezone.utc)
        products = {}
        for name in ("iml", "xfer", "iml_details", "xfer_courts"):
            source = data.get("sources" if name in LABELS else "supplements", {}).get(name, {})
            products[name] = {
                "status": source_health(source, now)[0],
                "last_success": source.get("last_success"),
                **{k: source.get("current", {}).get(k) for k in
                   ("slot", "fresh", "eligible", "pending", "oldest_checked_at")},
            }
        repeat = data.get("repeat_visits", {})
        through = repeat.get("through")
        repeat_ok = bool(through) and not repeat.get("error") and (
            now - datetime.fromisoformat(through)
        ).total_seconds() <= 3600
        products["repeat_visits"] = {"status": "Current" if repeat_ok else "Delayed",
                                    "through": through}
        if product is not None:
            if product not in products:
                return jsonify(error="Unknown data product"), 404
            healthy = products[product]["status"] in ("Current", "Collecting normally")
            return jsonify(products[product]), 200 if healthy and not cache["error"] else 503
        population_ok = all(products[n]["status"] == "Collecting normally" for n in LABELS)
        return jsonify(storage_error=cache["error"], loaded_at=cache["loaded_at"],
                       products=products), 200 if population_ok and not cache["error"] else 503

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
