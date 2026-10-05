---
type: Decision
title: Accept IML roster rows with a blank permanent ID
description: A roster row with a blank permanent ID is archived and counted as a booking but counts no one until IML assigns an ID.
tags: [iml, population, data-quality]
decided: 2026-10-04
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T01:54:59Z }
verified:
  - { by: human:jpbranson, at: 2026-10-04T16:39:05Z }
  - { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:06:36Z }
sources:
  - id: decisions-l117
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/DECISIONS.md?plain=1#L117-L120
    title: DECISIONS.md lines 117-120, before the OKF migration
    last_modified: 2026-10-04T16:36:20Z
    author: claude-code/claude-opus-5-5
---

Accept an IML roster row with a blank permanent ID (owner approved). One such booking rejected
every roster scan for 11 hours. The booking number and result ID remain required; the row is
archived and counted as a booking, but counts no one in the population or other person-based
results until IML assigns an ID.

Related: [blank permanent ID issue](../source-quality/iml-blank-permanent-id.md), [IML population](../measures/iml-population.md).
