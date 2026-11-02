---
type: Playbook
title: Exports and reconstruction
description: Export aggregate history as CSV, private case data as JSON lines, or one reconstructed observation, from the local archive or the active bucket.
resource: ../../scripts/export_cases.py
tags: [operations, privacy, storage]
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T01:54:59Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:06:36Z }
sources:
  - id: readme-l198
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/README.md?plain=1#L198-L208
    title: README.md lines 198-208, before the OKF migration
    last_modified: 2026-09-22T16:39:10Z
  - id: storage-l50
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/docs/STORAGE.md?plain=1#L50-L67
    title: docs/STORAGE.md lines 50-67, before the OKF migration
    last_modified: 2026-09-22T16:39:10Z
  - id: case-data-l103
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/docs/CASE_DATA.md?plain=1#L103-L143
    title: docs/CASE_DATA.md lines 103-143, before the OKF migration
    last_modified: 2026-09-23T03:04:09Z
---

# Selecting the archive

These commands use `SCJ_BUCKET` when set; otherwise they read `SCJ_DATA_DIR`
(default `data/`). Since September 22, the active archive is in Cloud Storage
and the local directory is the cutover backup. With `SCJ_BUCKET` unset, the commands read
the local archive, which stopped updating at cloud cutover. Complete the
[cloud authentication and export setup](active-cloud-archive.md)
to export current cloud observations; that setup also applies to private exports and
reconstruction commands.

# Aggregate history

The 90-day dashboard index is a view limit, not a deletion policy. Export all
aggregate history from the selected archive:

```powershell
.\.venv\Scripts\python.exe scripts\export_archive.py --output data\exports\history.csv
```

Aggregate history export is unchanged by the schema-2
[normalized history](../architecture/normalized-history.md) format.

# Reconstruct one observation

Use the exact successful quarter-hour slot, with a timezone. This works with
both original schema-1 manifests and schema-2 history:

```powershell
.\.venv\Scripts\python.exe scripts\reconstruct_observation.py --source xfer --slot 2026-09-19T09:00:00Z --output data\exports\xfer-0900.json
```

The JSON contains source, observation metadata, records, active IDs, and observed
IDs. It contains private person-level data; the example keeps it inside the
Git-ignored data directory. The dashboard never exposes this command or data.

# Private case exports

Exports are newline-delimited JSON, suitable for Python's json module or
`pandas.read_json(path, lines=True)`. Keep output under the ignored data directory.

All currently collected detail pages ([IML record pages](../sources/iml-record-pages.md)):

```powershell
.\.venv\Scripts\python.exe scripts\export_cases.py --source iml-details --output data\exports\iml-details.jsonl
```

Add `--booking EXACT_BOOKING` or `--case "EXACT CASE"` to filter. Add
`--slot 2026-09-19T18:30:00Z` to reconstruct that successful archived observation,
including its retrieval metadata. An unavailable detail page is absent from the
export; compare the dashboard's available/eligible counts.

Latest downloaded pending-hearing report ([XFER court reports](../sources/xfer-court-reports.md)):

```powershell
.\.venv\Scripts\python.exe scripts\export_cases.py --source xfer-courts --family pending_hearings --output data\exports\pending-hearings.jsonl
```

Without `--family`, exports use the latest downloaded report per family.
`--all-versions` includes every archived report version, including files no
longer listed by the county; when a newer parser version has read the same content, only the
newest parse is exported. `--slot` instead selects the latest downloaded
report per family from the catalog as of a successful collection, rather than
every file in that catalog. These two options are mutually exclusive. Rows include
the source filename, modification time, first capture time, content hash, and
revision key. An unsupported report produces an explicit inventory row with a
raw-file reference rather than disappearing silently.

`scripts/reconstruct_observation.py` also accepts sources `iml_details` and
`xfer_courts` for full normalized states. Population CSV exports remain limited
to the two population sources. No person-level export endpoint exists on the
public dashboard; `/api/coverage` exposes only aggregate collection status.
