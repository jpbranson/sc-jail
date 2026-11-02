---
type: Source Quality Issue
title: Record pages fill in over the first day or two
description: Case entries appear a median 6.5 hours and a bond decision a median 20.5 hours after a booking is first listed, so new bookings are grouped by the filled-in page.
tags: [iml-details, bonds, analysis, data-quality]
affects: IML details
first_seen: 2026-09-25
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:10:00Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:10:00Z }
sources:
  - id: source-quality-l25
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/docs/SOURCE_QUALITY.md?plain=1#L25-L25
    title: docs/SOURCE_QUALITY.md lines 25-25, before the OKF migration
    last_modified: 2026-09-26T02:01:31Z
    author: claude-code/claude-opus-5-5
---

# Issue

Record pages fill in over the first day or two: case entries and charges appear a median of 6.5
hours after a booking is first listed (90% within 24 hours), charge case numbers later, and a bond
decision (any type other than "Not Assessed") a median of 20.5 hours after (90% within 40 hours).

# Latest evidence

881 bookings first listed Sept 19 to 30: case entries appeared a median of 7.8 hours after first
listing (90% within 20.5 hours) and a bond decision a median of 20.5 hours after (90% within 40.5
hours); 70 had no case entries and 153 no bond decision by the latest roster (Sept 30 length of
stay). For the 526 first listed Sept 19 to 25, 58 had no case entries and 109 no bond decision.

# Handling

Group new bookings by the first page with case entries (charge, detainer) and the first page with a
bond decision (bond), never by the first page fetched. See the
[decision](../decisions/2026-09-26-filled-in-record-page.md) and [length of
stay](../analysis/length-of-stay.md).
