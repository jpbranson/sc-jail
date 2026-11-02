# Shelby County jail

Two Python source collectors, case detail archives, and a small Flask dashboard that measure
the Shelby County jail population from two county sources: the IML roster (distinct people)
and the XFER jail workbook (distinct bookings). The public dashboard shows aggregates; names,
dates of birth, and source records stay in private storage.

- Dashboard: https://sc-jail-dashboard-xcucxqzc2q-uc.a.run.app
- Runs on Google Cloud in `sc-jail-research-20260922` (`us-central1`); see the
  [cloud deployment](knowledge/operations/cloud-deployment.md).

## Knowledge base

Everything known about the project is kept in [`knowledge/`](knowledge/index.md) as an
[Open Knowledge Format](https://github.com/GoogleCloudPlatform/open-knowledge-format) v0.2
bundle: one markdown concept per topic, with frontmatter recording its type, where it came
from, and whether it is still current. Start at [knowledge/index.md](knowledge/index.md).

| To | Read |
| --- | --- |
| Understand what is measured | [Project overview](knowledge/project.md), [measures](knowledge/measures/index.md), [sources](knowledge/sources/index.md) |
| Run it locally or run the tests | [Local setup](knowledge/operations/local-setup.md), [tests, lint, and dependency refresh](knowledge/operations/verification.md) |
| Deploy or operate the cloud services | [Deployment](knowledge/operations/deploy.md), [monitoring and limits](knowledge/operations/monitoring-and-limits.md), [backup and restoration](knowledge/operations/backup-and-restore.md) |
| Analyze the archive | [Analysis](knowledge/analysis/index.md) |
| See why things are the way they are | [Decisions](knowledge/decisions/index.md), [source quality](knowledge/source-quality/index.md) |
| See what is waiting on the owner | [Open questions](knowledge/questions/index.md) |
| Add or change knowledge | [Maintaining the knowledge bundle](knowledge/maintaining-knowledge.md) |

Original references: [jpbranson/shelby.county](https://github.com/jpbranson/shelby.county) and
[jpbranson/memphis.xfer](https://github.com/jpbranson/memphis.xfer).
