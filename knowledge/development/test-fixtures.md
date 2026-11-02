---
type: Reference
title: Synthetic test fixtures
description: The four checked-in XLS fixtures contain only invented records that exercise jail-row parsing, heading removal, and court-report field preservation.
resource: ../../tests/fixtures/
tags: [testing, privacy]
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T01:54:59Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:06:36Z }
sources:
  - id: fixtures-readme-l1
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/tests/fixtures/README.md?plain=1#L1-L13
    title: tests/fixtures/README.md lines 1-13, before the OKF migration
    last_modified: 2026-09-22T16:39:10Z
---

All four workbooks contain invented test records. None contains person-level
records copied from the live county sources.

- `injail.xls`: generated with xlwt; three charge rows for two invented booking
  numbers, with invented names and dates.
- `injail-repeated-headings.xls`: the same kind of synthetic jail rows, with
  repeated headings and surrounding whitespace to exercise heading removal.
- `court-indictments.xls`: synthetic indictment rows, repeated headings, an
  unnamed column, and a formatted ZIP code to check field preservation.
- `court-pending.xls`: synthetic pending-hearing rows with repeated headings
  and leading-zero case and booking numbers.

How the tests run is in [tests, lint, and dependency refresh](../operations/verification.md).
