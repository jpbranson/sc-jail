---
type: Decision
title: Lower the budget alert to $5
description: The budget alert drops from $15 to $5 with the same actual-spend and forecast thresholds; it alerts but does not cap spending.
tags: [cost, cloud]
decided: 2026-09-26
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T01:54:59Z }
verified:
  - { by: human:jpbranson, at: 2026-09-26T02:00:00Z }
  - { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:10:00Z }
sources:
  - id: decisions-l114
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/DECISIONS.md?plain=1#L114-L115
    title: DECISIONS.md lines 114-115, before the OKF migration
    last_modified: 2026-09-26T02:01:31Z
    author: claude-code/claude-opus-5-5
---

Lower the budget alert from $15 to $5 (owner approved), keeping alerts at 50%, 90%, and 100% of
actual spend and 100% of forecast. It alerts; it does not cap.

Related: [Configure a $15 monthly budget alert](2026-09-22-budget-15.md), [Measured usage and cost](../cost/measured-usage-2026-09-26.md).
