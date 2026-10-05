---
type: Source Quality Issue
title: Legacy TLS handshake on both county servers
description: Both county servers require a legacy TLS handshake option, enabled only in their HTTP sessions with certificate and hostname checks kept.
tags: [iml, xfer, security]
affects: Both county servers
first_seen: 2026-09-19
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T01:54:59Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:10:00Z }
sources:
  - id: source-quality-l22
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/docs/SOURCE_QUALITY.md?plain=1#L22-L22
    title: docs/SOURCE_QUALITY.md lines 22-22, before the OKF migration
    last_modified: 2026-09-26T02:01:31Z
    author: claude-code/claude-opus-5-5
---

# Issue

Both county servers require a legacy TLS handshake option.

# Handling

Enabled only in those HTTP sessions; certificate and hostname checks kept. See [county
connections](../sources/county-connections.md) and the
[decision](../decisions/2026-09-19-legacy-tls-option.md).
