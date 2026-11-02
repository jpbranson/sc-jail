# Cloud

* [Google Cloud deployment](cloud-deployment.md) - The live sc-jail deployment in sc-jail-research-20260922 (us-central1), with its services, archive, backup, Scheduler, monitoring, budget, and identities.
* [Owner setup and deployment](deploy.md) - How to deploy or update sc-jail with scripts/deploy_gcp.py, including dry runs, deferred Scheduler activation, image rollback, and post-deploy checks.
* [Monitoring and limits](monitoring-and-limits.md) - Health and freshness endpoints, uptime alerts, the tracker health object, retry behavior, collector time limits, and known alert patterns.
* [Work with the active cloud archive](active-cloud-archive.md) - Authenticate with Application Default Credentials and set SCJ_BUCKET to export from or maintain the live cloud archive, pausing Scheduler for maintenance.

# Backup and recovery

* [Backup and restoration](backup-and-restore.md) - Daily Storage Transfer backup of the archive, how to monitor it, and how to restore into a separate location and rebuild projections.
* [Restore drill, 2026-09-26](restore-drill-2026-09-26.md) - A rehearsal restored the daily backup into a separate local folder, verified history, and rebuilt identical projections in about 35 minutes.
* [Rebuild derived state](rebuild-derived-state.md) - Rebuild all four source checkpoints and the public index from committed history during paused maintenance; repeat analytics rebuild separately.

# Data

* [Exports and reconstruction](exports.md) - Export aggregate history as CSV, private case data as JSON lines, or one reconstructed observation, from the local archive or the active bucket.
* [History migration and verification](history-migration.md) - Convert an archive to schema-2 history under the collector lease and verify every observation by chronological checksum replay.
* [Repeated XFER heading correction](repair-xfer-headings.md) - The parser skips the jail workbook's repeated column headings; a resumable repair command fixed historical observations and backs up every manifest first.
* [Move existing local history to Cloud Storage](migrate-local-history.md) - Maintenance-window procedure for copying a local archive into an empty cloud archive and activating collection; the deployed project's cutover is complete.

# Development

* [Local setup](local-setup.md) - Install the locked dependencies and start a local collector and dashboard against a separate development archive, with optional tunnel and restart task.
* [Tests, lint, and dependency refresh](verification.md) - Run pytest and ruff with the locked dev dependencies, refresh pinned dependencies deliberately, and the recorded heading-repair and live-check results.
