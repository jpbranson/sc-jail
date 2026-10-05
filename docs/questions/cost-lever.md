---
type: Open Question
title: If the allowances are shared, how should the project get under $5?
description: Three options, none applied, to keep the project under $5 a month if free allowances are shared with other projects.
tags: [cost, cloud]
raised: 2026-09-26
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T01:54:59Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:10:00Z }
sources:
  - id: flight-log-l56
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/FLIGHT_LOG.md?plain=1#L56-L61
    title: FLIGHT_LOG.md lines 56-61, before the OKF migration
    last_modified: 2026-09-26T02:01:31Z
    author: claude-code/claude-opus-5-5
---

Raised in step 6 of the [next-steps run](../history/next-steps-run-2026-09.md). It applies if the
answer to [which cost case applies](./cost-allowance-case.md) is that the allowances are shared.

Options, none applied:

- (a) move this project to its own billing account, which gets its own free allowances (owner
  action, needs a payment method);
- (b) test the collector at about 0.17 vCPU (busy-minute CPU is 49% of 0.25), roughly
  −$1.20/month, with a risk of longer runs;
- (c) cut [failed IML scans](../source-quality/iml-pagination-shift.md) (about 11% of collector
  time) by restarting a shifted scan sooner or scanning faster, a code change that needs care with
  county request volume.

The measurements behind (b) and (c) are in [measured usage and
cost](../cost/measured-usage-2026-09-26.md).
