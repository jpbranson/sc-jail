# Repeat visits

The dashboard uses the complete archived IML roster history to count distinct
booking numbers for each permanent person ID. A booking is counted once even if
it appears in hundreds of polls, disappears, or reappears after a collection gap.
Released bookings remain part of the observed history. Visits never captured by
this archive are unknown; these counts are not a lifetime history or a recidivism
rate. XFER does not provide a permanent person ID, so it is not used to link people.

The repeat section uses all archived observations, independently of the population
time-range selector. It shows people with at least two distinct bookings, the
number of bookings for those people, the number beyond their first booking, and
the distribution of visits per returning person. Single-booking people and the
total number of observed bookings are also shown.

Time between visits is the number of calendar days from the earlier booking's
IML release date to the next booking's IML commitment date. Commitment dates come
from archived individual detail pages. They are dates, not precise admission or
release times. A same-day interval is zero calendar days.

Bookings are ordered by commitment date. If any commitment date for a person's
observed bookings is missing, that person's intervals remain unmeasured rather
than bridging an unknown visit. Intervals with a missing prior release date are
also unmeasured. Overlapping dates, a release before commitment, or equal
commitment dates with ambiguous booking order are excluded from the histogram.
The dashboard separately reports measured, missing-date, and invalid/ambiguous
interval counts. Conflicting permanent IDs exclude the affected people's bookings.

## Updating

After population and detail collection, the collector incrementally consumes new
committed IML and IML-detail observations. The initial run backfills all archived
observations, including those older than the 90-day population-chart window.
Changes and checkpoints are reconstructed with the archive's checksum validation;
unchanged states are verified against the previous processed checksum.

The compact registry at `private/analytics/repeat-visits.json.gz` retains only
booking identifiers, permanent IDs, first-seen timestamps, and the dates needed
for the calculation. Person-level data stays private. The public index and
`/api/repeat-visits` expose aggregate counts, date coverage, and histogram bins.
A failed calculation preserves the last completed public result and displays
a delayed-refresh notice.

Long calculations save a private staging registry every 20 observations and
before their time budget expires. Each calculation captures fixed source targets;
later arrivals wait for the next calculation. Subsequent runs resume that work,
while the published registry and public summary remain at their last complete
watermark. A calculation-version change requires `--rebuild`. Administrative rebuilds
renew their storage lease while progressing; a lost lease prevents publication.

Commands below use `SCJ_BUCKET` when set, otherwise the local `SCJ_DATA_DIR`
(default `data/`). The local archive stopped updating at cloud cutover; use the
[cloud archive setup](CLOUD.md#work-with-the-active-cloud-archive) to update the
active dashboard. Normal scheduled collection already refreshes these summaries.

Recalculate from the selected archive without contacting county sources:

```powershell
.\.venv\Scripts\python.exe scripts\update_repeat_visits.py
```

After repairing historical source data, rebuild the registry:

```powershell
.\.venv\Scripts\python.exe scripts\update_repeat_visits.py --rebuild
```

Both commands acquire the collector lease. For cloud maintenance, pause the
Scheduler job and let active collection finish before running them, then resume
the job after verification. An active collection leaves the archive and existing
summaries unchanged. Original observations are never modified by this calculation.
