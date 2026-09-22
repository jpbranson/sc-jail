# Normalized history storage

Each successful quarter-hour collection has an immutable private observation
manifest. Schema 2 stores normalized data as a daily checkpoint plus change logs.
The population download schedule is unchanged. Supplemental detail and court
report policies are described in [CASE_DATA.md](CASE_DATA.md).

Since September 22, 2026, Cloud Storage holds the active archive. The local
`data/` directory is the cutover backup and does not receive cloud observations.
All commands below use `SCJ_BUCKET` when set, otherwise `SCJ_DATA_DIR` (default
`data/`). Use the [cloud archive setup](CLOUD.md#work-with-the-active-cloud-archive)
for current exports, reconstruction, or maintenance.

## Representation

- The first successful collection of each **UTC day** is a full checkpoint.
  It contains normalized records, active IDs, and the IDs present in that report.
  A new day's checkpoint does not depend on any earlier observation.
- Later collections contain additions and removals relative to the previous
  successful collection. A corrected row is a removal plus an addition.
- Duplicate rows retain their multiplicity, including identical XFER charge
  rows. Normalized row order is canonical, not the source's display order.
  The original HTML/XLS preserves the source's ordering and exact bytes.
- Active IDs and observed IDs also use additions/removals, so the manifests
  do not repeat thousands of IDs every 15 minutes.
- Unchanged data needs only an unchanged-state reference and checksums.
  Each poll still records its own times, metrics, and source artifact references.
- If a compressed change log would be larger than a checkpoint, a new
  checkpoint is saved early.
- SHA-256 checks cover the checkpoint, the state before a change, and the state
  after it. Missing, damaged, forward, or cross-day links raise an error.
  A single observation requires at most 96 manifests to reconstruct.
- Collection gaps remain gaps. Changes are relative to the last successful
  observation; they do not assert when an event happened during an outage.

The mutable file at `private/checkpoints/{source}.json.gz` contains the current
normalized state, active IDs, and cumulative seen IDs. This working cache is
overwritten, not appended, and lets collection calculate changes with one state
read instead of replaying cloud history. A retry can reuse a committed manifest
and finish the cache/index writes without downloading the source again.

Full normalized checkpoints use the existing compressed, content-addressed
`private/blobs/` objects. Change logs live inside their observation manifests;
they do not require an extra cloud object per poll.

## Reconstruct one observation

Use the exact successful quarter-hour slot, with a timezone. This works with
both original schema-1 manifests and schema-2 history:

```powershell
.\.venv\Scripts\python.exe scripts\reconstruct_observation.py --source xfer --slot 2026-09-19T09:00:00Z --output data\exports\xfer-0900.json
```

The JSON contains source, observation metadata, records, active IDs, and observed
IDs. It contains private person-level data; the example keeps it inside the
Git-ignored data directory. The dashboard never exposes this command or data.

Aggregate history export is unchanged:

```powershell
.\.venv\Scripts\python.exe scripts\export_archive.py --output data\exports\history.csv
```

## Migration and verification

New collectors can start against an old archive without migration: the first
new-format collection becomes a checkpoint. Old observations remain readable.

The deployed archive already includes the September 19 migration; these are
maintenance commands, not required deployment steps. To convert another archive,
pause its scheduler, let any active collection finish, and run:

```powershell
.\.venv\Scripts\python.exe scripts\migrate_history.py
.\.venv\Scripts\python.exe scripts\migrate_history.py --verify-only
```

These commands use `SCJ_DATA_DIR` or `SCJ_BUCKET` like the collector. Migration
holds the collector lease, verifies the reconstructed normalized state, and uses
atomic/generation-checked manifest replacement. It resumes safely if interrupted.
A cloud lease expiry stops further writes safely; completed conversions remain
readable. Migration of a large archive requires a planned maintenance window.

Original manifests are retained under `private/legacy/observations/`, and their
original normalized blobs remain available. This is a one-time migration backup:
conversion does not immediately reclaim those bytes. Future observations use
only the new format. No automatic backup or raw-archive deletion is configured.

Verification replays every observation in chronological order. Missing data or
checksum failures stop verification rather than silently replacing history.
After migration, verify a real collection and the public status endpoint.

## Retention and storage growth

All original roster HTML and jail XLS files remain archived with content
deduplication and are still fetched every 15 minutes. New individual-detail HTML
is retained on semantic changes; new court reports use selective downloads and
daily verification. Both expansions reuse the checkpoint/change-log format.
See [case data storage](CASE_DATA.md#storage-choices) for the precise policies.

The optimization reduces normalized-history and manifest growth. Raw originals
remain the largest component, so it does not promise a comparable reduction in
total archive size. Daily checkpoints add roughly one compressed normalized
state per source per day; change-log size depends on actual record changes.
The current-state cache has a roughly fixed size, apart from cumulative seen IDs.
