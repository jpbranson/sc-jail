---
type: Data Source
title: XFER court reports
description: Public XFER court-calendar, indictment, pending-hearing, and dispositions folders, monitored each cycle with bounded downloads of new or changed files.
resource: https://xfer.shelbycountytn.gov/
tags: [xfer-courts, courts]
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T01:54:59Z }
verified: { by: claude-code/claude-opus-5-5, at: 2026-10-05T02:06:36Z }
sources:
  - id: case-data-l47
    resource: https://github.com/jpbranson/sc-jail/blob/61a6e3a/docs/CASE_DATA.md?plain=1#L47-L78
    title: docs/CASE_DATA.md lines 47-78, before the OKF migration
    last_modified: 2026-09-23T03:04:09Z
---

# Folders

The following public folders are monitored each cycle:

| Folder | Report family | Useful identifiers and fields |
| --- | --- | --- |
| GS-Criminalcourtcalendar | General Sessions calendar | Party, connection type, case number/type, hearing date/time, location, officer, hearing type |
| CriminalCourtCalendar | Criminal Court calendar | The same calendar fields; its .txt files contain CSV |
| StateCriminalCourtCalendar | Daily indictment list | Case number, cross references, indictment date, defendant, offenses, location/judge, next hearing, published address fields |
| StateCriminalCourtCalendar | Pending hearings | Case/booking/indictment/AG numbers, offenses, hearing date/time/type, officer, session, attorney |
| GS-CriminalCourtDispositions | Dispositions | Folder monitored; no files were published at initial verification |

The dispositions folder's later state is tracked in
[the source-quality log](../source-quality/xfer-dispositions-empty.md).

# Downloads

By default, new or changed files are downloaded, up to eight per pass within
60 seconds. The newest report from each family is considered before older backfill. All
currently listed reports are eligible; the initial backlog is drained over
subsequent cycles. Files with unchanged size and modification time are fetched
again after 24 hours to detect silent replacements. A failed download waits an
hour before another attempt. Metadata checks cannot detect a silent replacement
immediately; this is a deliberate request-volume tradeoff for court reports.

The defaults are set in [configuration](../architecture/configuration.md); storage is described
in [case-data storage](../architecture/case-data-storage.md).

# Formats

Schemas for the four populated report families were checked against live
files. CSV and XLS disposition reports with an unambiguous case-number header
can be normalized if published. Unexpected filenames or layouts are retained
as raw files with an explicit unsupported status. An HTML error page or truncated
download is a failure, never an empty court report. Empty valid calendars and an
empty dispositions folder are legitimate source states.

# Joining to bookings

Court calendars contain parties and cases beyond the jail roster. Booking
numbers can connect the pending-hearing and jail reports. Preserve case numbers
as strings, including spaces and leading zeroes, and retain court/report context:
one field may be a composite indictment/booking number. No automatic name-based
matching or inferred court dispositions are performed.

See [case-number formats](../source-quality/case-number-formats.md) and the
[court linkage analysis](../analysis/court-linkage.md).
