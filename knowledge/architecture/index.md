# System

* [Cloud architecture](system.md) - One private Cloud Run collector, one public read-only dashboard, one Scheduler job, a private Storage archive, and a daily backup, all scaling to zero.
* [Configuration](configuration.md) - Environment variables for the archive location, HTTP identity, IML scan budget, build provenance, and case-data batch, budget, and refresh settings.

# Storage

* [Normalized history storage](normalized-history.md) - Schema 2 stores each source's normalized data as a daily full checkpoint plus checksummed quarter-hour change logs inside immutable observation manifests.
* [Archive layout and meaning](archive-layout.md) - The data/ (or bucket) layout of public index, private checkpoints, observations, blobs, court reports, analytics, repairs, and failure records, and what it retains.
* [Case-data storage](case-data-storage.md) - IML detail HTML is kept only on semantic changes and court reports once per content version, both with daily checkpoints and change logs.
* [Retention and storage growth](storage-growth.md) - All raw roster HTML and jail XLS stay archived with deduplication; raw originals remain the largest part of archive growth.

# Pipelines

* [Case-data collection](case-data-collection.md) - After the population sources commit, the same collector request spends bounded time on court reports and then IML record pages, with no extra service.
* [Repeat-visit registry](repeat-visit-registry.md) - The collector incrementally replays committed IML and detail observations into a private registry and publishes aggregate repeat-visit results.
