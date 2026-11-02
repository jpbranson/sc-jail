---
type: Decision
title: Start the local fallback while cloud setup waits
description: With no Google Cloud login or project configured locally, start the local fallback and supply a repeatable cloud deployment script.
tags: [local, cloud, deployment]
status: deprecated
decided: 2026-09-19
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T01:54:59Z }
sources:
  - id: decisions-l25
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/DECISIONS.md?plain=1#L25-L26
    title: DECISIONS.md lines 25-26, before the OKF migration
    last_modified: 2026-09-22T16:39:10Z
---

Superseded on 2026-09-22 by the [cloud cutover](../deployments/2026-09-22-cutover.md).

No Google Cloud login or project is configured locally. Start the local fallback now and supply
a repeatable cloud deployment script.

Related: [Local setup](../operations/local-setup.md), [Deploy to Google Cloud](../operations/deploy.md).
