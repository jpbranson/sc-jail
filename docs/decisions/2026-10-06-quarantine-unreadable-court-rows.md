---
type: Decision
title: Quarantine unreadable court-report rows
description: A court report with a few unreadable rows is parsed without them; more than 1% unreadable rows keeps the report unsupported and alerting.
tags: [xfer-courts, courts, data-quality, monitoring]
decided: 2026-10-06
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-06T20:45:00Z }
sources:
  - id: courts-parser
    resource: ../../src/sc_jail/courts.py
    title: Court report parser, version 2
---

Quarantine an unreadable court-report row and parse the rest of the report (owner
direction). One [unescaped quote](../source-quality/xfer-court-unescaped-quote.md) in one row
of a 1,187-line calendar made the whole report unsupported and kept the court-report freshness
alert open for hours. A row that is not valid CSV or has the wrong number of fields is left
out of the normalized records, the raw file keeps it, and the count is recorded with the
report version. If quarantined rows exceed 1% of a report's data rows, the report stays
unsupported and the alert still fires, so a format change is not hidden.

The court parser version became 2, so unchanged reports are parsed again once; the
`--all-versions` export keeps only the newest parse of each report's content.[^courts-parser]
IML pagination retry behavior is unchanged.

Related: [monitoring and limits](../operations/monitoring-and-limits.md),
[XFER court reports](../sources/xfer-court-reports.md).

[^courts-parser]: Court report parser, version 2
