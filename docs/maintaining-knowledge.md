---
type: Playbook
title: Maintaining the knowledge bundle
description: How to add and update concepts in this OKF v0.2 bundle, including decisions, source-quality issues, deployments, trust, and lifecycle fields.
resource: ../scripts/check_knowledge.py
tags: [provenance]
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:06:36Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:06:36Z }
sources:
  - id: okf-spec
    resource: https://github.com/GoogleCloudPlatform/open-knowledge-format/blob/main/SPEC.md
    title: Open Knowledge Format (OKF) specification, version 0.2
  - id: decisions-l1
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/DECISIONS.md?plain=1#L1-L4
    title: DECISIONS.md lines 1-4, before the OKF migration
    last_modified: 2026-09-23T03:04:09Z
  - id: source-quality-l1
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/docs/SOURCE_QUALITY.md?plain=1#L1-L7
    title: docs/SOURCE_QUALITY.md lines 1-7, before the OKF migration
    last_modified: 2026-09-26T02:01:31Z
    author: claude-code/claude-opus-5-5
  - id: plan-l99
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/PLAN.md?plain=1#L99-L100
    title: PLAN.md lines 99-100, before the OKF migration
    last_modified: 2026-09-22T16:39:10Z
---

# Layout

`docs/` is an Open Knowledge Format v0.2 bundle:[^okf-spec] one markdown concept per unit of
knowledge, each with YAML frontmatter, an `index.md` in every directory, and the bundle's
[update log](log.md). Start at the [index](index.md).

| Directory | Holds | `type` values |
| --- | --- | --- |
| `sources/` | The county sources and how each is collected | Data Source, Reference |
| `measures/` | Definitions of the published counts | Metric |
| `source-quality/` | One concept per source behavior that affects analysis | Source Quality Issue |
| `architecture/` | System design, storage formats, configuration | Architecture, Storage Format, Pipeline, Reference |
| `operations/` | Running, deploying, backing up, restoring, exporting, maintaining | Cloud Deployment, Playbook, Reference, Drill Record |
| `deployments/` | One record per cloud deployment | Deployment, Reference |
| `cost/` | The original estimate and measured usage | Cost Estimate, Cost Measurement |
| `analysis/` | Private analysis products and the staged plan | Analysis, Pipeline, Plan |
| `decisions/` | One concept per decision | Decision |
| `questions/` | Questions waiting on the owner | Open Question |
| `history/` | The original plan, milestones, the 0.2.0 audit, run logs | Plan, Milestone, Technical Audit, Run Log |
| `development/` | Development notes | Reference |

The bundle is published with the public repository. Keep person-level data out of it,
consistent with [keeping person-level source files private](decisions/2026-09-19-private-person-level-files.md).

# Frontmatter

- **Required here:** `type`, `title`, and `description`. The description is one sentence; the
  directory's `index.md` repeats it word for word.
- **Recommended:** `tags`, and `resource` when the concept describes one concrete asset (a URL,
  or a relative path such as `../../scripts/weekly_analysis.py`).
- **Extension keys:** `decided` (Decision), `affects` and `first_seen` (Source Quality Issue),
  `deployed`, `image`, `cloud_build`, `commit`, `source_revision`, `revisions` (Deployment),
  `raised` (Open Question), and `date` (other dated records).
- **`generated: { by, at }`:** update it on every meaningful content change. Agents use
  `<producer>/<version>` (for example `claude-code/claude-opus-5-5`); people use `human:<id>`.
- **`verified`:** add an entry only when someone actually confirmed the content: the owner as
  `human:jpbranson` (an approval on record, or merging the pull request that carries it), a
  `process:<id>`, or an agent such as `claude-code/claude-opus-5-5` that checked the concept's
  current-state claims against the code or the live system (machine-confirmed). An agent
  re-reading its own writing does not count. Without `verified`, a concept is unverified.
- **`sources`:** what the concept was built from: repository paths, external pages, or the
  pre-migration lines (GitHub permalinks at commit `61a6e3a`). Cite a specific claim with a
  footnote whose label is the source `id`.
- **`status`:** `deprecated` when superseded (keep the file; its first body line links the
  replacement), `draft` when incomplete. Omit it for current content.
- **`stale_after`:** only when the content names a date that will supersede it, such as
  preliminary results before a readout date. Update the concept when that date passes.

# Recurring updates

- **Decisions:** add `decisions/YYYY-MM-DD-<slug>.md` for decisions that affect data quality,
  cost, operation, or user-visible behavior, as a brief plain-English record.[^plan-l99] Each
  describes the decision at its date; when a later decision or the cloud cutover supersedes
  one, mark the older one deprecated and link its replacement.[^decisions-l1]
- **Source quality:** add `source-quality/<slug>.md` when a weekly run or an investigation finds
  something new about how the public sources behave, so analysis can account for it. Update an
  issue's latest evidence rather than adding a duplicate. Counts are aggregates from the
  private archive; see [analysis](analysis/index.md) for definitions and the weekly run that
  produces the evidence.[^source-quality-l1]
- **Deployments:** add `deployments/YYYY-MM-DD.md` (with `-HHMM` when a day has several), mark
  the previous record deprecated with a "Superseded by" line, and update
  [cloud deployment](operations/cloud-deployment.md) and
  [retained images](deployments/retained-images.md).
- **Open questions:** add `questions/<slug>.md` for anything that needs the owner. When it is
  answered, record the outcome in `decisions/` and mark the question deprecated with a link.
- **Every change:** add a dated entry to [the log](log.md) (newest first), keep the directory's
  `index.md` entry in step, and run the check below.

# Check

```powershell
.\.venv\Scripts\python.exe scripts\check_knowledge.py
.\.venv\Scripts\python.exe scripts\check_knowledge.py --entries docs\decisions
```

The first command checks OKF conformance, field formats, index entries, footnotes, and
relative links. The second prints the index entries for one directory from its concepts'
frontmatter. `tests/test_knowledge.py` runs the same check with the test suite; Cloud Build
does not upload `docs/`, so there only the checker's own tests run.

[^okf-spec]: Open Knowledge Format specification, version 0.2
[^plan-l99]: PLAN.md, verification and handoff
[^decisions-l1]: DECISIONS.md introduction
[^source-quality-l1]: docs/SOURCE_QUALITY.md introduction
