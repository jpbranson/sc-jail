---
type: Source Quality Issue
title: 'Meaning of "Sentenced" on General Sessions entries'
description: 'Most General Sessions entries are marked "Sentenced", which may mean disposed rather than serving a sentence; unverified, so the profile may understate pretrial detention.'
tags: [iml-details, courts, analysis, data-quality]
affects: IML details
first_seen: 2026-09-25
generated: { by: codex/agent, at: 2026-10-07T18:03:26Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:10:00Z }
sources:
  - id: source-quality-l26
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/docs/SOURCE_QUALITY.md?plain=1#L26-L26
    title: docs/SOURCE_QUALITY.md lines 26-26, before the OKF migration
    last_modified: 2026-09-26T02:01:31Z
    author: claude-code/claude-opus-5-5
  - id: da-process
    resource: https://www.scdag.com/victim-witness-services
    title: District Attorney justice process guidance, accessed October 7, 2026
  - id: comptroller
    resource: https://comptroller.tn.gov/content/dam/cot/orea/advanced-search/2025/ShelbyCofullreport.pdf
    title: Shelby County Criminal Justice System, March 2025, printed pages 5, 26-27, and 34
  - id: da-portal
    resource: https://www.scdag.com/case-info
    title: District Attorney portal access instructions, accessed October 7, 2026
  - id: portal
    resource: https://cjs.shelbycountytn.gov/CJS/
    title: Court portal browser access attempt, October 7, 2026
  - id: code
    resource: ../../src/sc_jail/profile.py
    title: Profile classification from bond-entry status
  - id: template
    resource: ../../scripts/profile_population.py
    title: Population profile report template
  - id: results
    resource: ../analysis/population-profile.md
    title: Recorded September 30 profile results
  - id: question
    resource: ../questions/sentenced-meaning.md
    title: Original September 25 cohort and baseline
  - id: run-log
    resource: ../history/next-steps-run-2026-09.md
    title: September 25 held population recorded in the next-steps run
  - id: fixtures
    resource: ../development/test-fixtures.md
    title: Synthetic test fixtures
---

# Issue

Most General Sessions case entries are marked "Sentenced", including for people with an open, newly
indicted Criminal Court case. "Sentenced" may mean disposed in General Sessions (for example bound
over) rather than serving a sentence. **Unverified; see the [human review
item](../questions/sentenced-meaning.md).**

# Latest evidence

Record pages on Sept 25: 2,396 General Sessions entries "Sentenced" and 650 "Open". Of 1,345 people
held and counted as sentenced on some cases, 438 have only General Sessions entries marked sentenced
plus an open Criminal Court case. 32 of 35 bookings matched to an indictment list have that indicted
case open, but only 1 has no case marked sentenced. Sept 30 weekly run (General Sessions split
not recomputed): 1,346 held people sentenced on some cases with others open; 55 bookings matched
to an indictment list, 52 with that indicted case open and 2 with no case marked sentenced.

# Handling

Until checked, the [profile's](../analysis/population-profile.md) "no case marked sentenced" count
may understate pretrial detention. [Court linkage](../analysis/court-linkage.md) uses the status of
the indicted case itself. See the [decision](../decisions/2026-09-26-keep-sentenced-definition.md).

# October 7 investigation

**Unresolved: no individual case was traced and no mapping was established.** This review
checked the public repository at `dad628b478ae580c067290c19500e1f98e60869e`, official process
guidance, and court-portal access. No classification logic, report template, historical result,
or published definition changed.

## Evidence and limits

| Evidence | Establishes | Does not establish |
| --- | --- | --- |
| District Attorney process guidance | Felony guilty pleas cannot be entered in General Sessions unless reduced to misdemeanors; probable cause or waiver can send a case to the grand jury; criminal information can bypass the grand jury. | How IML encodes these events. |
| Comptroller, printed page 5 and Exhibit 17 on printed page 34 | Held to state means bound over to the grand jury; held-to-state cases and guilty pleas are separate categories. | A mapping from IML `Sentenced` to a court outcome. |
| September 25 repository cohort | 438 held people had only GS entries marked sentenced plus an open Criminal Court case. | Whether their GS and Criminal Court cases are the same prosecution, or whether a GS entry is a genuine misdemeanor sentence. |
| `legal_status()` implementation | Groups the exact bond-entry label `Sentenced`, without reading judgments or sentences. | A verified legal or custodial status. |

The official sources provide context, not matched-case observations.[^da-process] [^comptroller]
The repository supplies the cohort and code behavior.[^question] [^code]

The [record-page documentation](../sources/iml-record-pages.md) says bond status is not a
court disposition, but the report template says the label marks a case with a sentence.
That sentence exceeds the reviewed evidence. It is a flagged wording inconsistency, not
proof that the label means bind-over; it was not changed in this investigation.[^template]

## Access and sample availability

The current public question, source-quality entry, run log, and repository files contain
aggregate cohorts but no original real-case sample list for this investigation. All four
checked-in court/jail workbooks are synthetic and cannot supply real sample cases.[^fixtures]
The private archive and weekly outputs are absent from this checkout. The
[weekly-run documentation](../analysis/weekly-run.md) locates them in the owner's local
`data/` tree. Available-file and prior-work searches did not recover a real sample.

On October 7 the research browser received a Cloudflare security block before court search
was available.[^portal] This does not mean the portal is unavailable to everyone, or that
any case is absent. The District Attorney also says an account is required for case histories
and hearing schedules; no authenticated case history was accessed.[^da-portal]

## Dated sensitivity calculation

These are calculations from documented aggregates, not an archive rerun or corrected results.

| Snapshot and calculation | People | Share of held population |
| --- | ---: | ---: |
| September 25: no case marked sentenced, recorded | 1,416 | 46.8% of 3,027 |
| September 25: potentially affected subgroup | 438 | 14.5% of 3,027 |
| September 25: scenario if all 438 qualified for reclassification | 1,854 | 61.2% of 3,027 |
| September 30: no case marked sentenced, recorded | 1,471 | 48.0% of 3,066 |
| September 30: sentenced on some cases, others open, recorded | 1,346 | 43.9% of 3,066 |

The September 25 denominator comes from the dated run log, the baseline and subgroup from
the question, and September 30 totals from the profile documentation.[^run-log] [^question]
[^results] The maximum September 25 scenario would reduce the mixed category from 1,345
to 907, leaving total held unchanged at 3,027.

Let `k` count people in the 438-person group for whom **all** GS `Sentenced` entries are
verified non-sentence events and whose remaining cases satisfy a reviewed replacement rule
at the snapshot date. The revised label-based count would be `1,416 + k`, with `0 <= k <= 438`.
No value of `k` is established. The maximum adds 14.5 percentage points (30.9% relative
to 1,416). This is not a misclassification-rate estimate, confidence interval, or upper
bound on all pretrial detention. Other sentences, holds, and custody reasons remain separate.

Do not add September 25's 438 to September 30's 1,471 or treat all 1,346 mixed cases as
pretrial. The September 30 GS-only subgroup was not recomputed. Time-held distributions,
money-bond counts, and today's profile cannot be adjusted from these aggregates alone.

## Case review needed to finish

Use the original private sample if recovered; otherwise explicitly label a newly selected,
dated archive sample. A six-booking comparison set should include:

| Category | Target bookings | Question tested |
| --- | ---: | --- |
| GS `Sentenced`, recently indicted open Criminal Court case | 2 | Does an explicit cross-reference link the GS entry to bind-over? |
| GS `Sentenced`, older open Criminal Court case | 1 | Does the label persist beyond an update delay? |
| GS `Sentenced`, documented misdemeanor or reduced-charge judgment | 1 | Does a genuine sentence receive the same label? |
| Open GS case followed through preliminary hearing or waiver | 1 | When does the label change relative to bind-over? |
| GS `Sentenced`, related disposed Criminal Court case | 1 | Does the label predate the later conviction or sentence? |

This is a purposive comparison, not a statistically representative sample. For each booking,
keep the identity crosswalk and records private under the
[privacy decision](../decisions/2026-09-19-private-person-level-files.md), and capture:

1. Exact booking and case identifiers, dated IML bond entries, all other entries marked
   sentenced, and retrieval timestamps. Preserve case strings and source labels.
2. GS docket/orders: hearing or waiver, bind-over/held-to-state date, disposition code and
   text, reduced charges, plea, judgment, and sentence details when present.
3. An explicit court cross-reference to the Criminal Court case or indictment. Shared
   name, booking, charge wording, or timing alone does not prove the same prosecution.
4. Indictment or criminal-information date, Criminal Court outcome at the snapshot,
   and any later disposition/judgment separately. A scheduled disposition hearing is
   not a completed disposition; later conviction cannot be backdated.
5. IML observations before/after each event where available. Daily refresh brackets a
   label change; it does not date the underlying court event precisely.
6. A conclusion per bond entry and separate eligibility assessment per booking, checking
   all other genuine sentences and holds. Keep missing cross-references unresolved.

A matched counterexample could disprove that the label always denotes a sentence. A few
bind-over examples would not prove every GS `Sentenced` entry means bind-over or justify
ignoring every GS label. A replacement rule needs explicit scope, treatment of unknowns,
and checks against genuine sentences and other outcomes. Retain raw labels and recompute
each dated cohort only after that mapping is established. The Comptroller's own difficulty
linking the courts reinforces the need for explicit cross-references.[^comptroller]

[^da-process]: District Attorney, Victim/Witness Services, General Sessions and Criminal Court sections.
[^comptroller]: Tennessee Comptroller, Shelby County Criminal Justice System (March 2025), printed pages 5, 26-27, and 34.
[^da-portal]: District Attorney, Case Info, Odyssey access instructions.
[^portal]: October 7 browser observation of the official court portal's security block; no case record retrieved.
[^code]: `src/sc_jail/profile.py`, `legal_status()`.
[^template]: `scripts/profile_population.py`, Case status explanatory text.
[^results]: Population profile, September 30 results.
[^question]: Open question, September 25 counts and cohort definition.
[^run-log]: Next-steps run, September 25 population comparison.
[^fixtures]: Synthetic test fixtures; all checked-in workbooks contain invented records.
