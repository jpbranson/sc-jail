# Synthetic fixtures

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
