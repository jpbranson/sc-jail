---
type: Decision
title: Enable the legacy TLS option only for county sessions
description: Both county servers need a legacy TLS handshake option, enabled only in their HTTP sessions with certificate and hostname checks kept.
tags: [security, iml, xfer]
decided: 2026-09-19
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T01:54:59Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:06:36Z }
sources:
  - id: decisions-l19
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/DECISIONS.md?plain=1#L19-L20
    title: DECISIONS.md lines 19-20, before the OKF migration
    last_modified: 2026-09-22T16:39:10Z
---

Both county servers require a legacy TLS handshake option. Enable it only in their HTTP
sessions; keep certificate and hostname verification.

Related: [County server connections](../sources/county-connections.md), [legacy TLS issue](../source-quality/county-legacy-tls.md).
