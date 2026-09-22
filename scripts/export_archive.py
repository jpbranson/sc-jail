"""Export aggregate history from all private manifests, including beyond 90 days."""

import argparse
import csv
import gzip
import json
from pathlib import Path

from sc_jail.config import Config
from sc_jail.storage import make_store


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    config = Config.from_env()
    store = make_store(config)
    if config.bucket:
        keys = sorted(b.name for b in store.bucket.list_blobs(prefix="private/observations/"))
    else:
        keys = sorted(
            p.relative_to(store.root).as_posix()
            for p in (store.root / "private/observations").rglob("*.json.gz")
        )
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
    exported = 0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for key in keys:
            raw, _ = store.read(key)
            manifest = json.loads(gzip.decompress(raw))
            if manifest["source"] in {"iml", "xfer"}:
                writer.writerow({"source": manifest["source"], **manifest["point"]})
                exported += 1
    print(f"Exported {exported} observations to {args.output}")


if __name__ == "__main__":
    main()
