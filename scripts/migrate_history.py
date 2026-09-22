"""Convert normalized history to daily checkpoints and change logs, retaining backups."""

import argparse
import json

from sc_jail.config import Config
from sc_jail.migration import migrate_archive
from sc_jail.storage import make_store


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--verify-only", action="store_true", help="Check history without converting it"
    )
    args = parser.parse_args()
    report = migrate_archive(make_store(Config.from_env()), verify_only=args.verify_only)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
