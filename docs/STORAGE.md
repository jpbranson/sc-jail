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
read instead of replaying cloud history. Before collecting, `archive.reconcile_source`
finds committed manifests after either projection cursor, including previous slots,
and finishes checkpoint/index writes without downloading those observations again.
A malformed cache is rebuilt by checksum-verified replay inside that source's
failure boundary. A storage access failure is reported, not treated as an empty
archive. Recovery saves its cursor before the collection deadline and resumes.

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
Maintenance leases renew with generation preconditions while work progresses;
losing the lease stops further writes safely. Completed conversions remain
readable. Migration of a large archive requires a planned maintenance window and
an administrative identity; the collector cannot replace historical manifests.

Original manifests are retained under `private/legacy/observations/`, and their
original normalized blobs remain available. This is a one-time migration backup:
conversion does not immediately reclaim those bytes. Future observations use
only the new format. Daily cloud backup is configured separately; no live
raw-archive deletion is configured. See [backup and restoration](CLOUD.md#backup-and-restoration).

Verification replays every observation in chronological order. Missing data or
checksum failures stop verification rather than silently replacing history.
`--verify-only` leaves observations and projections unchanged but still acquires
the collector lease, so a cloud identity needs read access plus write access to
`private/collector-lease.json`. Run it against a separate recovery copy or during
paused maintenance. After migration, verify a real collection and the public
status endpoint.

## Rebuild derived state

If the public index is missing or malformed, normal collection repairs its
population projections from committed observations. For a complete rebuild of
all four source checkpoints and the public index during paused maintenance:

```powershell
.\.venv\Scripts\python.exe scripts\rebuild_index.py
```

This validates retained normalized history, preserves original manifests/blobs,
and keeps only the latest 90 days in the public population view. It preserves an
existing repeat summary; rebuild repeat analytics separately if that projection
was lost. Missing or corrupt immutable history is an error requiring restoration,
not a reason to fabricate a collection or silently skip data.

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
