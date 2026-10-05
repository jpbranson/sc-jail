---
type: Open Question
title: "Which case applies to the $5 target: $0.52 or $5.38 a month?"
description: Measured usage projects $0.52 a month if this project receives the billing account's free allowances and $5.38 if other projects use them first.
tags: [cost, cloud]
raised: 2026-09-26
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:15:07Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:10:00Z }
sources:
  - id: flight-log-l45
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/FLIGHT_LOG.md?plain=1#L45-L51
    title: FLIGHT_LOG.md lines 45-51, before the OKF migration
    last_modified: 2026-09-26T02:01:31Z
    author: claude-code/claude-opus-5-5
---

Raised in step 6 of the [next-steps run](../history/next-steps-run-2026-09.md), against the
[under-$5 target](../decisions/2026-09-26-under-5-dollars.md).

The [projection](../cost/measured-usage-2026-09-26.md) is $0.52/month if this project receives the
billing account's free allowances and $5.38 if other projects use them first (Cloud Run CPU alone
$3.81). The billing account has five billing-enabled projects (this one and four others, not named
here); I did not inspect the others. Check Billing → Reports for this project, grouped by SKU with
credits shown, or say whether the other projects run Cloud Run. No billing export is configured, so
this cannot be read by CLI.

If the allowances are shared, see [how the project could get under $5](./cost-lever.md).

The [September 30 weekly measurement](../cost/measured-usage-2026-09-30.md) projects $0.51 and
$5.44 a month for the same two cases; as of October 5, 2026, the question is still open.
