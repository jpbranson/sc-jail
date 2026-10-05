---
type: Decision
title: Run local collection on UTC quarter hours under a Windows check
description: Local collection starts on UTC quarter hours, retries a failed source within the slot, and is supervised by a one-minute Windows check.
tags: [local, operations]
status: deprecated
decided: 2026-09-19
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T01:54:59Z }
sources:
  - id: decisions-l28
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/DECISIONS.md?plain=1#L28-L29
    title: DECISIONS.md lines 28-29, before the OKF migration
    last_modified: 2026-09-22T16:39:10Z
---

Superseded on 2026-09-22 by the [cloud cutover](../deployments/2026-09-22-cutover.md).

Local collection now starts on UTC quarter hours, retries a failed source within the slot, and
is supervised by a one-minute Windows check.

Related: [Local setup](../operations/local-setup.md).
