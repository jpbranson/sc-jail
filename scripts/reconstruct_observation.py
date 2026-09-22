"""Reconstruct private records and ID sets for a successful quarter-hour observation."""

import argparse
import json
from pathlib import Path

from sc_jail.config import Config
from sc_jail.history import observation_key, reconstruct_state
from sc_jail.storage import make_store, read_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=["iml", "xfer", "iml_details", "xfer_courts"], required=True)
    parser.add_argument(
        "--slot", required=True, help="ISO timestamp with timezone, on a quarter hour"
    )
    parser.add_argument("--output", type=Path, required=True, help="Private JSON export path")
    args = parser.parse_args()
    store = make_store(Config.from_env())
    key = observation_key(args.source, args.slot)
    manifest, _ = read_json(store, key)
    state = reconstruct_state(store, key, manifest=manifest)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(
            {"source": args.source, "point": manifest["point"], **state}, ensure_ascii=False
        ),
        encoding="utf-8",
    )
    print(f"Reconstructed {len(state['records'])} records to {args.output}")


if __name__ == "__main__":
    main()
