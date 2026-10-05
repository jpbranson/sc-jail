# Current

* [October 4, 16:24 UTC deployment](2026-10-04-1624.md) - Image from commit 5ced56f that accepts IML roster rows with a blank permanent ID; the current deployment as of October 4, 2026.
* [Retained images and rollback](retained-images.md) - Which container images remain available for rollback under the image cleanup policy, as recorded after the October 4 deployments.

# Superseded

* [October 4, 16:06 UTC deployment](2026-10-04-1606.md) - First October 4 fix that restored the IML roster and record pages while repeat-visit refresh still rejected the blank permanent ID.
* [September 28 deployment](2026-09-28.md) - Image from main at b79b987 that removed dead code, duplicated helpers, and unneeded archive reads without changing collected data or outputs.
* [September 27 deployment](2026-09-27.md) - Image from main at 40394b1 that added a health object to /api/freshness for the project tracker.
* [September 26 deployment](2026-09-26.md) - Image from main at 94dd8c1 that loads dashboard charts once at their displayed width and refreshes an open page in place.
* [September 23 detail-refresh fix](2026-09-23-detail-refresh-fix.md) - Collector-only update at 04:55 UTC on September 23 that queues IML record pages for refresh at 20 hours, ahead of the 24-hour freshness limit.
* [Release 0.2.0 (September 23)](2026-09-23-release-0-2-0.md) - Reliability release adding recovery from committed observations, resumable analytics, narrower permissions, daily backups, and freshness alerts.
* [September 22 cloud cutover](2026-09-22-cutover.md) - Initial Google Cloud deployment and archive migration; 5,858 files were verified before collection started and the local processes were stopped.
