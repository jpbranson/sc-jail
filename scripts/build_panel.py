"""Build the private booking panel (JSON lines) from a local archive copy.

Replays every committed IML roster and detail observation, then rebuilds each
archived IML population from the panel. Any mismatch fails the build, so later
analysis never runs on a panel that disagrees with the collector.

    python scripts/build_panel.py --data-dir data/snapshots/YYYY-MM-DD --output data/analysis/panel
"""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

from sc_jail.iml import CHICAGO
from sc_jail.panel import FACTS, build_panel, check_populations, missing_slots
from sc_jail.storage import LocalStore


def summarize(bookings, observations, mismatches, missing):
    rows = list(bookings.values())
    changes = Counter()
    for booking in rows:
        for before, after in zip(booking["details"], booking["details"][1:]):
            changes.update(field for field in FACTS if before[field] != after[field])
    return {
        "coverage": {"first": observations[0]["observed_at"], "last": observations[-1]["observed_at"],
                     "roster_observations": len(observations)},
        "bookings": len(rows),
        "outcomes": dict(Counter(b["outcome"] for b in rows)),
        "left_truncated": sum(b["left_truncated"] for b in rows),
        "permanent_id_changes": sum(len(b["permanent_id_history"]) > 1 for b in rows),
        "release_withdrawn_or_changed": sum(len(b["release_history"]) > 1 for b in rows),
        "reappeared_after_absence": sum(b["reappearances"] > 0 for b in rows),
        "with_detail_versions": sum(bool(b["details"]) for b in rows),
        "detail_field_changes": dict(changes.most_common()),
        "missing_roster_slots": len(missing),
        "missing_roster_slots_by_utc_time": dict(Counter(m[11:16] for m in missing).most_common()),
        "population_mismatches": mismatches,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data-dir", type=Path, required=True, help="Local archive copy")
    parser.add_argument("--output", type=Path, required=True, help="Output directory")
    args = parser.parse_args()
    if not (args.data_dir / "private").is_dir():
        parser.error(f"{args.data_dir} does not look like an archive copy")
    bookings, observations = build_panel(LocalStore(args.data_dir), CHICAGO)
    mismatches = check_populations(bookings, observations, CHICAGO)
    missing = missing_slots(observations)
    summary = summarize(bookings, observations, mismatches, missing)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (args.output / "missing-slots.json").write_text(json.dumps(missing, indent=2), encoding="utf-8")
    with (args.output / "bookings.jsonl").open("w", encoding="utf-8") as stream:
        for number in sorted(bookings):
            stream.write(json.dumps(bookings[number]) + "\n")
    print(f"Wrote {len(bookings):,} bookings from {len(observations):,} roster observations "
          f"to {args.output}")
    if mismatches:
        print(f"FAILED: {len(mismatches)} archived populations differ from the panel",
              file=sys.stderr)
        sys.exit(1)
    print("All archived IML populations match the panel.")


if __name__ == "__main__":
    main()
