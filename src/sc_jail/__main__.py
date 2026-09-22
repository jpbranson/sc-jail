import argparse
import json
import logging
import os
import signal
import threading
import time
from datetime import datetime, timezone

from .config import Config
from .pipeline import collect_all
from .storage import Conflict, make_store, read_json

log = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Shelby County jail observations")
    parser.add_argument(
        "command", choices=["collect", "schedule", "dashboard", "collector", "status"]
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=int(os.getenv("PORT", "8050")))
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    config = Config.from_env()
    store = make_store(config)
    if args.command == "status":
        state, _ = read_json(store, "public/index.json", {})
        print(
            json.dumps(
                {
                    k: {p: v for p, v in s.items() if p not in {"history", "attempts"}}
                    for k, s in state.get("sources", {}).items()
                },
                indent=2,
            )
        )
    elif args.command == "collect":
        result = collect_all(config, store)
        print(json.dumps(result, indent=2))
        raise SystemExit(1 if result["status"] == "failed" else 0)
    elif args.command == "schedule":
        stop = threading.Event()
        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, lambda *_: stop.set())
        while not stop.is_set():
            try:
                result = collect_all(config, store)
                log.info("Collection result: %s", json.dumps(result))
                if result["status"] == "failed" and time.time() % 900 < 600:
                    if stop.wait(60):
                        break
                    log.info("Retry result: %s", json.dumps(collect_all(config, store)))
            except Conflict:
                log.info("Another collection owns the lock; skipping this tick")
            except Exception:
                log.exception("Collection cycle failed; the next quarter-hour will retry")
            delay = config.interval_seconds - (time.time() % config.interval_seconds)
            log.info(
                "Next collection at %s",
                datetime.fromtimestamp(time.time() + delay, timezone.utc).isoformat(),
            )
            stop.wait(delay)
    else:
        from waitress import serve

        from .web import create_app, create_collector_app

        app = (create_app if args.command == "dashboard" else create_collector_app)(config, store)
        serve(app, host=args.host, port=args.port, threads=4 if args.command == "dashboard" else 1)


if __name__ == "__main__":
    main()
