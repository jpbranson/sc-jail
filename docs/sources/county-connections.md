---
type: Reference
title: County server connections
description: Both county appliances need a legacy TLS handshake option; collectors keep certificate checks and use normal sessions, bounded retries, and 150 ms pacing.
tags: [iml, xfer, security]
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T01:54:59Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:06:36Z }
sources:
  - id: readme-l145
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/README.md?plain=1#L145-L155
    title: README.md lines 145-155, before the OKF migration
    last_modified: 2026-09-22T16:39:10Z
---

Both county appliances require the legacy TLS initial-handshake option.
Certificate and hostname checks remain enabled; no global TLS settings change.
The collectors use normal sessions, bounded retries, and at least 150 ms between
roster page request starts. They do not use browsers or download unrelated county folders.

This applies to the [IML roster](iml-roster.md) and [IML record pages](iml-record-pages.md)
(`imljail.shelbycountytn.gov`) and to the [XFER jail workbook](xfer-jail-workbook.md) and
[XFER court reports](xfer-court-reports.md) (`xfer.shelbycountytn.gov`). See the source-quality
entry on the [legacy TLS requirement](../source-quality/county-legacy-tls.md) and the
[decision to enable it only in those sessions](../decisions/2026-09-19-legacy-tls-option.md).
