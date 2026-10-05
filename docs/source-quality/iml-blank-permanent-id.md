---
type: Source Quality Issue
title: Booking listed with a blank permanent ID
description: IML can list a booking before assigning its permanent ID; the row is archived and counted as a booking but as no person.
tags: [iml, population, data-quality]
affects: IML roster
first_seen: 2026-10-04
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:10:00Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:10:00Z }
sources:
  - id: source-quality-l13
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/docs/SOURCE_QUALITY.md?plain=1#L13-L13
    title: docs/SOURCE_QUALITY.md lines 13-13, before the OKF migration
    last_modified: 2026-10-04T16:36:20Z
    author: claude-code/claude-opus-5-5
---

# Issue

A booking can be listed with a blank permanent ID.

# Latest evidence

Booking 26116828 appeared about 05:15 UTC with no permanent ID and a same-day release date; the
strict parser rejected every IML scan from 05:22 UTC until [the fix
deployed](../deployments/2026-10-04-1606.md); the 16:15 UTC slot succeeded.
[Record-page](../sources/iml-record-pages.md) collection was stopped for the same period.
After the fix, the collector logged one booking without a permanent ID in each of 40 IML scans
from Oct 4 16:16 to Oct 5 02:01 UTC while collection stayed healthy.

# Handling

Booking number and result ID are still required. The row is archived and counted as a booking but
counts no one in person-based counts; the collector logs a warning with the number of such rows.
See the [decision](../decisions/2026-10-04-blank-permanent-id.md).
