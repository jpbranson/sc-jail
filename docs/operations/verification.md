---
type: Playbook
title: Tests, lint, and dependency refresh
description: Run pytest and ruff with the locked dev dependencies, refresh pinned dependencies deliberately, and the recorded heading-repair and live-check results.
tags: [testing, operations]
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T01:54:59Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:06:36Z }
sources:
  - id: readme-l217
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/README.md?plain=1#L217-L255
    title: README.md lines 217-255, before the OKF migration
    last_modified: 2026-09-23T03:04:09Z
---

# Run the checks

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.lock
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check src tests scripts
```

Tests cover checkpoint/change-log reconstruction, migration, corruption,
retry recovery, parsers, synthetic Excel data, pagination and shifted results,
time zones, duplicates, interrupted writes, failure isolation, cloud generation
checks/leases, and dashboard empty/stale/error states. The checked-in Excel
[fixtures](../development/test-fixtures.md) contain only invented records.

# Builds and dependencies

Cloud Build runs the same tests and lint checks before building a deployable
image. Runtime, development, build-tool, and container-base versions are pinned.
To refresh runtime dependencies, first update the direct pins in `pyproject.toml`
as needed, then run `python scripts/lock_dependencies.py`, review `requirements.lock`,
and repeat the checks above on Python 3.13 and Linux before deployment. That script
does not regenerate `requirements-dev.lock` or `requirements-build.lock`; update
those pins explicitly when changing test or build tools. See the
[technical audit and refactoring decisions](../history/2026-09-23-technical-audit.md) for the
recovery, backup, performance, and failure-mode changes.

# Recorded results

The [repeated-heading correction](repair-xfer-headings.md) repaired 39 historical XFER
observations, removing 20,168 heading rows across those observations. The latest repaired report
contained 3,128 bookings and 22,754 charge rows. All 77 observations then in the
archive passed reconstruction checks. Older reported counts included the heading
error; corrected manifests and dashboard history are authoritative. Counts will
change with later observations.

Desktop (1440 px) and mobile (390 px) browser checks passed: no page overflow,
charts loaded, range filtering worked, and visible UI text was at least 16 px.
The locked dependencies were built successfully in the Linux/Python 3.13 container.
The container passed endpoint checks at 0.25 CPU and 512 MiB, and both services
were deployed to Google Cloud. Live checks covered dashboard endpoints, all
four SVG charts, the aggregate CSV, the private collector's authentication, and
archive access policies. Deployment staging and service-account propagation
retries have regression checks.
