# IML roster

* [07:00 UTC roster shrinks mid-scan](iml-0700-roster-shrinks.md) - The 07:00 UTC (2 a.m. Central) IML roster can fail completeness checks because its total falls during every attempt.
* [Roster pagination shifts mid-scan](iml-pagination-shift.md) - The IML roster total often changes during a scan, shifting pagination, so the scan is rejected and retried (about 25 to 40 times a day).
* [Permanent person ID can change](iml-permanent-id-changes.md) - IML can reassign a booking's permanent person ID, so counts use the ID in effect at each moment.
* [Booking listed with a blank permanent ID](iml-blank-permanent-id.md) - IML can list a booking before assigning its permanent ID; the row is archived and counted as a booking but as no person.
* [Release date withdrawn and relisted](iml-release-date-relisted.md) - IML can withdraw a listed release date and list it again later, so the panel keeps every release-date change.
* [Roster lists recently released bookings](iml-lists-recent-releases.md) - The IML roster also lists recently released bookings with their release date, so the population counts only blank or future release dates.
* [Missed roster slots before the cloud cutover](iml-local-missed-slots.md) - Before the September 22 cloud cutover, local collection missed roughly one IML roster slot in five.

# IML record pages

* [Record pages refreshed about daily](iml-details-daily-refresh.md) - IML record pages are refreshed about daily, so a detail change is dated when it is seen, not when it happened.
* [Record pages fill in over the first day or two](iml-details-fill-in.md) - Case entries appear a median 6.5 hours and a bond decision a median 20.5 hours after a booking is first listed, so new bookings are grouped by the filled-in page.
* [Meaning of "Sentenced" on General Sessions entries](iml-details-sentenced-meaning.md) - Most General Sessions entries are marked "Sentenced", which may mean disposed rather than serving a sentence; unverified, so the profile may understate pretrial detention.
* [Court dates change after the hearing passes](iml-details-court-date-changes.md) - Most court-date changes appear after a listed date passes, so daily refresh cannot tell a continuance from a scheduled next step.
* [Misspelled bond type](iml-details-bond-type-spelling.md) - Record pages spell one bond type "Uknown-Contact Court Cerks Office"; it is kept as published and is not a money bond.

# XFER jail workbook

* [Repeated column headings in the jail workbook](xfer-repeated-headings.md) - The XFER jail workbook repeats its column headings between printed pages; the parser skips them and historical observations were repaired.
* [Jail workbook regenerated about every two hours](xfer-two-hour-regeneration.md) - The XFER jail workbook is regenerated about every two hours, independently of polling, so a successful poll does not mean a new report.
* [One workbook row per charge](xfer-charge-rows.md) - The XFER jail workbook has one row per charge with bond values repeated across rows, so count distinct bookings and never sum bonds across rows.

# XFER court reports

* [Unescaped quote in a court calendar row](xfer-court-unescaped-quote.md) - A county CSV court calendar can contain a row with an unescaped quote; the row is quarantined and the rest of the report is parsed.
* [Empty dispositions folder](xfer-dispositions-empty.md) - The XFER dispositions folder has no files, so court outcomes are unavailable and bond status is not treated as a disposition.

# IML compared with XFER

* [XFER bookings the IML roster never shows](iml-xfer-hidden-bookings.md) - XFER lists about 135 held bookings the public IML roster never shows, a stable set of older active adult cases whose cause is unconfirmed.
* [IML-held bookings missing from XFER](iml-xfer-missing-from-xfer.md) - About 10 IML-held bookings are missing from the XFER workbook at any time, not explained by its two-hour refresh.
* [Shared IML and XFER fields mostly agree](iml-xfer-shared-fields.md) - For bookings both sources list, book dates always match and case-number sets mostly match; court-date and detainer differences are partly timing.

# Both sources

* [Legacy TLS handshake on both county servers](county-legacy-tls.md) - Both county servers require a legacy TLS handshake option, enabled only in their HTTP sessions with certificate and hostname checks kept.
* [Several case-number formats](case-number-formats.md) - Case numbers come in several formats, a few with a lowercase letter, so joins use the exact string and never names.
