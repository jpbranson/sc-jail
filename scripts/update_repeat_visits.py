"""Backfill/update aggregate repeat visits without contacting county sources."""

import argparse
import json

from sc_jail.config import Config
from sc_jail.repeats import refresh_repeat_visits
from sc_jail.storage import make_store, read_json, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rebuild", action="store_true", help="Rebuild from all archived observations")
    args = parser.parse_args()
    store = make_store(Config.from_env())
    with store.lease(renewable=True):
        index, version = read_json(store, "public/index.json", {"sources": {}})
        summary = refresh_repeat_visits(store, rebuild=args.rebuild)
        index["repeat_visits"] = summary
        write_json(store, "public/index.json", index, expected=version)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
