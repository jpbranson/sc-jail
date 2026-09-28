"""Export aggregate history from all private manifests, including beyond 90 days."""

import argparse
import csv
from pathlib import Path

from sc_jail.config import Config
from sc_jail.storage import make_store, read_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    config = Config.from_env()
    store = make_store(config)
    keys = [k for source in ("iml", "xfer") for k in store.keys(f"private/observations/{source}/")
            if k.endswith(".json.gz")]
    fields = [
        "source",
        "slot",
        "observed_at",
        "finished_at",
        "source_updated_at",
        "population",
        "arrivals",
        "departures",
        "listed_people",
        "listed_records",
        "charge_rows",
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for key in keys:
            manifest, _ = read_json(store, key)
            writer.writerow({"source": manifest["source"], **manifest["point"]})
    print(f"Exported {len(keys)} observations to {args.output}")


if __name__ == "__main__":
    main()
