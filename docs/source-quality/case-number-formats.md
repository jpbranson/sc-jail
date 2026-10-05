---
type: Source Quality Issue
title: Several case-number formats
description: Case numbers come in several formats, a few with a lowercase letter, so joins use the exact string and never names.
tags: [courts, data-quality]
affects: Case numbers
first_seen: 2026-09-19
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:10:00Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:10:00Z }
sources:
  - id: source-quality-l24
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/docs/SOURCE_QUALITY.md?plain=1#L24-L24
    title: docs/SOURCE_QUALITY.md lines 24-24, before the OKF migration
    last_modified: 2026-09-26T02:01:31Z
    author: claude-code/claude-opus-5-5
---

# Issue

Several formats: a letter plus seven digits (mostly `C`, also `H`), eight-digit General Sessions
numbers, composite indictment-booking numbers (`NN NNNNN-NNNNNNNN`), and AG numbers. A few use a
lowercase letter.

# Latest evidence

Sept 23 IML [export](../operations/exports.md): 14,333 charges with `C`, 4,677 with `H`, 12 with
lowercase `c`. Sept 25 and Sept 30 [panels](../analysis/booking-panel.md): 1 distinct lowercase
case number, which matches no court report even uppercased.

# Handling

Join by exact string only; never by name. The weekly [court linkage](../analysis/court-linkage.md)
counts lowercase prefixes.
