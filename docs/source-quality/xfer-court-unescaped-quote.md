---
type: Source Quality Issue
title: Unescaped quote in a court calendar row
description: A county CSV court calendar can contain a row with an unescaped quote; the row is quarantined and the rest of the report is parsed.
tags: [xfer-courts, courts, data-quality]
affects: XFER court reports
first_seen: 2026-10-06
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-06T20:45:00Z }
sources:
  - id: courts-parser
    resource: ../../src/sc_jail/courts.py
    title: Court report parser, version 2
---

# Issue

The county's CSV export does not escape a double quote inside a field, so a row whose party
name contains one is not valid CSV.

# Latest evidence

The General Sessions calendar `Calendar100626.csv`, posted at 10:02 UTC on October 6, had one
such row (line 41 of 1,187). The strict parser rejected the whole file as "not valid CSV",
the file was marked unsupported, and the court-report freshness check returned HTTP 503 from
10:22 UTC; the other 39 listed reports parsed normally. Parser version 2 reads the same file
as 1,185 records with one quarantined row.

# Handling

From parser version 2,[^courts-parser] a row that is not valid CSV, or has the wrong number of
fields, is left out of the normalized records and counted as quarantined; the raw file keeps
it. A report with more quarantined rows than 1% of its data rows stays unsupported and alerts.
See [monitoring and limits](../operations/monitoring-and-limits.md) and the
[decision](../decisions/2026-10-06-quarantine-unreadable-court-rows.md).

[^courts-parser]: Court report parser, version 2
