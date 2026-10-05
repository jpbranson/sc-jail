# Population sources

* [IML roster](iml-roster.md) - The public Shelby County IML roster, read 30 records per page with at most two concurrent pages and accepted only when its range, total, and IDs validate.
* [XFER jail workbook](xfer-jail-workbook.md) - The SCSO-InJail.xls workbook on the public XFER file service, one row per charge, downloaded every interval and deduplicated by content hash.

# Case data

* [IML record pages](iml-record-pages.md) - IML individual detail pages for bookings on the latest complete roster, identity-checked and refreshed about daily in bounded batches.
* [XFER court reports](xfer-court-reports.md) - Public XFER court-calendar, indictment, pending-hearing, and dispositions folders, monitored each cycle with bounded downloads of new or changed files.

# Shared behavior

* [County server connections](county-connections.md) - Both county appliances need a legacy TLS handshake option; collectors keep certificate checks and use normal sessions, bounded retries, and 150 ms pacing.
