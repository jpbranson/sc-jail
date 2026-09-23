# 0.2.0 release verification

Release date: September 23, 2026 UTC. See [the audit](AUDIT.md) for findings,
implemented changes, and tradeoffs; [cloud operations](CLOUD.md) covers recovery.

## Artifact and validation

- Cloud Build: `1d6835cd-03dc-4214-b18a-d0793630f749` in `us-central1`.
- Source-content revision: `source-bc063a9a8dee19e68b6d`.
- Image digest: `sha256:fb1770426d17589c05249d02715dd81be14cd595ec61dc0a59344b0b15cc8d61`.
- Linux/Python 3.13: **132 tests passed**, Ruff clean. Windows regression checks
  and targeted deployment checks also passed.
- An isolated copy of the local cutover archive verified **1,057 observations**:
  16 checkpoints, 606 unchanged states, and 435 changes. Rebuilding population
  checkpoints/history reproduced the original public projections. Manifest bytes
  were unchanged; the original local archive was never modified.
- Live desktop (1440 px) and mobile (390 px) checks loaded four responsive charts,
  exercised the range control, and found no horizontal page overflow, small
  interface text, or JavaScript exceptions.
- Process/status/coverage/repeat/freshness endpoints, 90-day CSV, and all four SVG
  endpoints returned 200. An unauthenticated collector health request returned 403.

## Recovery and operations

- The release backup matched **6,444 objects / 171,279,424 bytes** by object name,
  size, and CRC32C while scheduling was paused and the collector lease was clear.
  The transient lease was excluded.
- Inventory SHA-256: `503b9be87dfa5a4d5366aaf14dba114837962e3a698bdbb4d36dae6b028e8b7e`.
- Backup job: `transferJobs/11494809231256598429`, scheduled daily at 05:10 UTC.
  The verified copy operation was
  `transferOperations/transferJobs-11494809231256598429-3243216192447443310`.
- Five operational alert policies are enabled with an email notification channel:
  population freshness, IML detail coverage, court-report coverage, repeat-analysis
  freshness, and backup errors.
- Collector IAM has no unconditional historical object-administrator grant and
  no backup-bucket grant. The dashboard retains aggregate-only archive access.
- Both services serve the image above; Scheduler was resumed after cutover.
- A fresh authenticated collection committed the 02:30 UTC slot for all four
  sources with application version `0.2.0` and the source-content revision above.

This records a successful release check, not a continuing availability or backup
guarantee. Check alert incidents and the last successful backup operation during
normal operations; periodically rehearse restoration into a separate archive.
