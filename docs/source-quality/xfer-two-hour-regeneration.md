---
type: Source Quality Issue
title: Jail workbook regenerated about every two hours
description: The XFER jail workbook is regenerated about every two hours, independently of polling, so a successful poll does not mean a new report.
tags: [xfer, data-quality]
affects: XFER jail workbook
first_seen: 2026-09-19
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:10:00Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:10:00Z }
sources:
  - id: source-quality-l20
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/docs/SOURCE_QUALITY.md?plain=1#L20-L20
    title: docs/SOURCE_QUALITY.md lines 20-20, before the OKF migration
    last_modified: 2026-09-26T02:01:31Z
    author: claude-code/claude-opus-5-5
---

# Issue

Regenerated about every two hours (about 34 minutes past the hour), independently of polling.

# Latest evidence

135 versions from Sept 19 07:34 to Sept 30 13:34 UTC; median 120 minutes apart (116 to 239),
mostly 33 or 34 minutes past the hour (Sept 30 reconciliation). The first 80 versions, to
Sept 25 23:34 UTC, showed the same spacing.

# Handling

[Reconcile](../analysis/source-reconciliation.md) each version at its own timestamp; a successful
poll does not mean a new report.
