"""Export private detail records or court reports as newline-delimited JSON."""

import argparse
import json
from pathlib import Path

from sc_jail.config import Config
from sc_jail.exporters import export_courts, export_details
from sc_jail.storage import make_store


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=["iml-details", "xfer-courts"], required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--slot", help="Optional successful quarter-hour timestamp with timezone")
    parser.add_argument("--booking", help="Exact booking number, where the source provides it")
    parser.add_argument("--case", help="Exact case number as published")
    parser.add_argument(
        "--family",
        choices=[
            "gs_calendar",
            "criminal_calendar",
            "indictments",
            "pending_hearings",
            "gs_dispositions",
            "unrecognized",
        ],
    )
    parser.add_argument(
        "--all-versions",
        action="store_true",
        help="Export every archived court report version, instead of latest per family",
    )
    args = parser.parse_args()
    if args.source == "iml-details" and (args.family or args.all_versions):
        parser.error("--family and --all-versions apply to court reports")
    if args.slot and args.all_versions:
        parser.error("--slot cannot be combined with --all-versions")
    store = make_store(Config.from_env())
    common = {"slot": args.slot, "booking": args.booking, "case": args.case}
    records = (
        export_details(store, **common)
        if args.source == "iml-details"
        else export_courts(store, family=args.family, all_versions=args.all_versions, **common)
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with args.output.open("w", encoding="utf-8") as stream:
        for record in records:
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")
            count += 1
    print(f"Exported {count} private records to {args.output}")


if __name__ == "__main__":
    main()
