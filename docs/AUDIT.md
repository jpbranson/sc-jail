# Technical audit and release decisions

Reviewed against baseline commit `4c0b2f5`. The recommendations below informed the
0.2.0 changes. Findings distinguish a demonstrated failure path from a possible
operational failure; they do not imply that production data was already lost.

## Problem and current architecture

The project preserves evidence of the jail population reported by two county
systems over time, supplements it with booking/court information, and publishes
aggregate counts and observed repeat-booking statistics. It cannot reconstruct
unobserved admissions or establish a lifetime recidivism rate. IML permanent
person IDs and XFER booking IDs are different measurement units.

Cloud Scheduler invokes a private Flask collector every 15 minutes.
`pipeline.collect_all` acquires a storage lease, runs independent population
adapters, archives compressed original responses, commits normalized observation
manifests, and updates working checkpoints and an aggregate index. It then runs
bounded supplemental work and repeat analytics. `history.py` reconstructs daily
checkpoints plus checksummed changes. Local disk and GCS implement the same small
object interface. A separate public Flask service reads only the aggregate index
and renders HTML, SVG, JSON, and CSV. Cloud Run scales both services to zero.

For the current single-writer, modest-traffic workload, this is a reasonable
architecture. Immutable evidence plus rebuildable projections is more useful
here than introducing an application database solely for dashboard counts.

## Significant findings

### Critical: a committed observation could be omitted after an interrupted write

**Before:** `pipeline.collect_all` repaired a manifest when retrying its exact
slot. If the manifest succeeded but checkpoint/index publication failed and the
retry arrived in a later slot, the next collection could use stale working state
and omit the committed point from the public view. Supplemental collectors had
related checkpoint publication paths.

**Principle:** a multi-object update needs an explicit commit record and replay
rule; request retries alone are not a transaction.

**Change:** `archive.reconcile_source` advances each lagging projection from
committed observations before new collection. `advance_checkpoint` and
`publish_point` centralize the shared rules. Identity and normalized checksums are
validated. `scripts/rebuild_index.py` provides explicit recovery.

**Benefit and cost:** recovery works across slot boundaries without refetching
old observations. Routine runs add a bounded daily-prefix listing; damaged caches
can require an expensive full replay. `tests/test_recovery.py` injects failures
between manifest, checkpoint, and index writes and checks the next slot.

### Critical: the online writer could destroy the entire research archive

**Before:** deployment granted the collector unconditional object-administrator
access. Soft deletion was disabled and the local cutover copy did not include
new cloud observations. An erroneous deletion or compromised collector could
remove irreplaceable evidence.

**Principle:** reduce a component's destructive authority and provide recovery
independent of the component that writes production data.

**Change:** `Deployment.protect_archive` grants read/create access to history and
limits overwrite/delete access to checkpoints, analytics, the public index area,
and the lease. `configure_backup` creates a separately permissioned daily backup
without source-delete propagation. Archive soft deletion and backup versioning
provide additional recovery windows.

**Benefit and cost:** routine collection cannot replace/delete committed history,
and deletion can be recovered. Administrative historical repairs now require a
different identity. Backup/version storage and object requests cost money. A
same-project backup does not defend against a compromised project owner, and a
scheduled copy is not an atomic snapshot; restoration requires verification and
projection rebuilding. See [operations](CLOUD.md#backup-and-restoration).

### Important: a corrupt working cache crossed source failure boundaries

**Before:** checkpoint decoding happened outside parts of the per-source error
handling. A bad derived file could abort collection before another healthy source
ran. Public-index corruption lacked a supported rebuild path.

**Principle:** disposable state must not become the sole authority, and failure
isolation must surround the actual operations that can fail.

**Change:** `read_projection` distinguishes decode failures from storage access
failures; `reconcile_source` validates/rebuilds checkpoints inside source handling.
Storage outages and corrupt immutable evidence still fail visibly.

**Benefit and cost:** independent collection continues and cached state can be
recovered. The recovery path is additional code, justified by failure-injection
tests rather than a generic persistence framework.

### Important: long analytics and maintenance could restart without progressing

**Before:** `refresh_repeat_visits` published only after replaying all pending
history. A growing backlog could repeatedly exhaust the same collection budget.
Long administrative work was bounded by the original nonrenewing lease.

**Principle:** bounded jobs need durable progress and an ownership check before
publication.

**Change:** repeat analysis stages private progress every 20 observations and
before its deadline, captures fixed target manifests, and publishes only a
complete calculation. Published-generation and calculation-version checks reject
obsolete staging. Administrative storage leases renew using generation checks;
the normal collector retains its hard execution boundary.

**Benefit and cost:** retries make progress while readers retain a complete
result. A second private registry and extra writes are required. Tests cover
multiple interrupted runs, completed rebuilds followed by new observations, and
lease renewal/loss. A very large registry could eventually require partitioning;
the current archive does not justify that migration.

### Important: long-range charts spent work on marks the screen cannot display

**Before:** change charts rendered individual 15-minute bars over 90 days and
regenerated on repeated requests. Rendering code also imported plotting libraries
into processes that only collect data.

**Principle:** presentation work should scale with visible resolution and cache
identity should include all data/rendering inputs.

**Change:** `charts.change_bins` uses hourly/daily totals for longer windows,
retaining missing comparisons as missing. The `web.create_app` chart handler caches a maximum
of 32 SVGs using index revision, range, width bucket, chart kind, and time bucket.
Plotting imports are lazy and rendering lives in `charts.py`.

**Benefit and cost:** fewer SVG marks, less CPU, and a smaller collector import
footprint. Long-range charts trade interval detail for readable totals; the
one-day view and exports retain detail. Cache memory is bounded per instance;
there is intentionally no shared cache service.

### Important: storage failure unnecessarily took down a warm dashboard

**Before:** failure while refreshing the aggregate cache propagated even when a
previous valid index was already in memory.

**Principle:** stale but clearly labeled research data is preferable to an
unavailable read-only view, while health reporting must still reveal the outage.

**Change:** `web.create_app` retains validated data, marks stale responses, shows
the last successful storage refresh, and backs off failed reads. A cold instance
without valid data returns 503. Freshness checks remain unhealthy during failure.

**Benefit and cost:** a transient storage outage does not erase an available
view. This is per-instance resilience, not guaranteed availability across a cold
start. Tests exercise failure, retry suppression, and recovery.

### Important: spreadsheet cell types could split a single identifier

**Before:** generic string conversion could turn numeric IDs into `123.0` while
equivalent text cells remained `123`; formatted leading zeroes could disappear.

**Principle:** identity is a domain value, not a spreadsheet display conversion.

**Change:** `excel.identifier` handles integral numeric IDs, text, and explicit
zero-padding formats; `xfer.parse_workbook` and court parsing share it. Invalid ID
types fail rather than silently joining unrelated data.

**Benefit and cost:** parser outputs are consistent across supported cell forms.
Historical reprocessing is deliberately separate: raw files remain unchanged,
parser versions are recorded, and old observations are not silently rewritten.
Synthetic XLS tests cover mixed numeric/text and padded identifiers.

### Important: process health was not collection health

**Before:** a healthy web process could coexist with stale population data,
incomplete supplemental coverage, or delayed analytics. Operators had to inspect
the dashboard and logs manually.

**Principle:** monitor the user-visible data product, including its watermark and
coverage, instead of only process liveness.

**Change:** `/api/freshness` and product-specific routes return meaningful HTTP
failure status. Deployment creates four uptime checks and sustained-failure
policies, plus a backup-error log alert. Structured collection summaries include
duration, product outcomes, and analytics watermark.

**Benefit and cost:** failures are actionable without exposing person records.
Incomplete supplemental coverage can legitimately persist; thresholds and batch
budgets need adjustment against observed county latency, not optimistic targets.
Notification channels are explicit deployment configuration. A disabled backup
job still requires inspection of its last successful operation.

### Important: a redeploy could erase tuning and publish an untested image

**Before:** deployment replaced service environment variables, potentially losing
source budgets/worker settings. Dependency/base/build-tool inputs were not all
fixed, and the production build lacked a regression gate.

**Principle:** deployment should preserve intentional configuration and validate
the artifact in its target environment.

**Change:** `deploy_gcp.py` updates its owned environment variable; `cloudbuild.yaml`
runs tests/lint before building. Container base and tooling versions are pinned;
lock regeneration is explicit. New manifests record application/parser/build
provenance; repeat summaries record calculation version.

**Benefit and cost:** repeated releases are easier to reproduce and investigate.
Builds take longer and pinned dependencies still require deliberate updates.
The source-content revision identifies code deployed before its Git commit; it
does not claim to encode every external configuration or county response.

### Minor: repeated plumbing obscured the domain rules

**Before:** source modules repeated checkpoint advancement, exporters knew backend
internals, and compact styling made small interface edits harder to inspect.

**Principle:** consolidate rules that must agree; avoid abstractions based only
on superficial similarity.

**Change:** introduce the small `Store` protocol, shared archive/identifier
helpers, a public `keys` interface for exports, and readable CSS. Keep source
fetching/parsing policies separate.

**Benefit and cost:** fewer independent implementations of the same invariant,
with a few small additional modules. No inheritance tree, ORM, plugin framework,
frontend rewrite, or generic job engine is introduced.

## Strong decisions

- Separate source identities/counts, immutable originals, checksum reconstruction,
  and explicit missing intervals preserve the meaning of research observations.
- Separate collector/dashboard identities and aggregate-only publication reduce
  exposure of person-level data. Authentication remains mandatory for collection.
- Bounded source requests, TLS certificate validation, and completeness checks
  avoid silently accepting a shifting/incomplete roster as a population change.
- Daily normalized checkpoints limit reconstruction chains while raw-content
  deduplication reduces repeated storage. The format remains backward compatible.
- Synthetic fixtures, injected clocks/stores, and source-specific parser tests
  make failure paths testable without depending on a live county appliance.

## Highest priorities and practical refactoring order

1. Establish backup recovery and narrow online-writer permissions.
2. Make committed-history replay authoritative for projections, with injected
   write-failure and source-isolation checks.
3. Add resumable analytics and renewable maintenance ownership.
4. Fix identifier normalization and retain explicit parser provenance.
5. Bound chart rendering and preserve validated dashboard data during outages.
6. Gate releases on tests/lint, preserve tuning, and configure product alerts.
7. Verify a real collection, a checksum-matched backup, live endpoints, and
   deployed identity permissions before considering the release complete.

No historical schema migration or rewrite of retained raw evidence is required
for these changes. Old cache/manifests remain readable; deployments and restores
must still preserve the single-writer lease invariant.

## Recommended architecture and things not worth changing

Building today, retain one scheduled collector, one read-only Flask dashboard,
private object storage, immutable commit manifests, and bounded materialized
projections. Place source HTTP/parsing in adapters, normalized reconstruction and
reconciliation in the archive layer, repeat analytics in its own resumable job
function, and visualization behind the aggregate interface. This release moves
toward that structure without replacing the application.

Keep Flask, Matplotlib, xlrd, the two storage backends, and the simple synchronous
control flow. The current workload does not justify Kubernetes, a queue per
source, a browser scraper, a JavaScript application framework, or a database
introduced only to remove object-store bookkeeping. Revisit partitioned analytics
or a query database when measured archive size, concurrent analysis, or new query
requirements make the migration worthwhile. Do not guess person identity from
XFER booking data, treat missing dates as zero, or backfill live-roster outages
with invented historical observations.
