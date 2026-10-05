---
okf_version: "0.2"
---

# Start here

* [Shelby County jail](project.md) - Two Python source collectors, case detail archives, and a small Flask dashboard that measure the Shelby County jail population from two county sources.
* [Maintaining the knowledge bundle](maintaining-knowledge.md) - How to add and update concepts in this OKF v0.2 bundle, including decisions, source-quality issues, deployments, trust, and lifecycle fields.
* [Update log](log.md) - Dated history of changes to this bundle, newest first.

# What is measured

* [Sources](sources/index.md) - The IML roster and record pages, the XFER jail workbook and court reports, and how each is collected.
* [Measures](measures/index.md) - Definitions of the IML population, XFER bookings, arrivals and departures, and repeat visits.
* [Source quality](source-quality/index.md) - Source behaviors that affect collection and analysis, each with first-seen date, latest evidence, and handling.

# How it works

* [Architecture](architecture/index.md) - Cloud architecture, normalized history and archive storage, case-data and repeat-visit pipelines, and configuration.
* [Operations](operations/index.md) - The live deployment and how to deploy, monitor, back up, restore, export, maintain, and run locally.
* [Deployments](deployments/index.md) - One record per cloud deployment since the September 22 cutover, plus the images kept for rollback.
* [Cost](cost/index.md) - The original cost estimate and the measured usage and cost against the under-$5-a-month target.

# What it shows

* [Analysis](analysis/index.md) - Private analysis products built from local archive copies, the weekly run that rebuilds them, and the staged plan.

# Why and what next

* [Decisions](decisions/index.md) - One record per decision that affects data quality, cost, operation, or user-visible behavior, newest first.
* [Open questions](questions/index.md) - Questions waiting on the owner, with the evidence behind each.
* [History](history/index.md) - The original plan, dated milestones, the 0.2.0 technical audit, and run logs.
* [Development](development/index.md) - Notes for working on the code, such as the synthetic test fixtures.
