<!-- Append-only opportunity log. Skills append an entry here when they detect
billable-service work that is NOT contracted in specs/SERVICES.md — they log it
for sales, they never implement it. Never delete entries; update `Status` only. -->

# Upsell Opportunities

Usage note: **log, never implement.** Detecting an opportunity here is not
authorization to build it — implementation starts only after the service is
added to `specs/SERVICES.md` and a SPEC is created for it.

## Log

| Date | Opportunity | Evidence | Related spec | Status |
|---|---|---|---|---|
| YYYY-MM-DD | e.g. "hreflang / i18n SEO work" | file:line or review finding | specs/features/NNN-slug | open |

Status values: `open` (logged, not yet raised with client) · `proposed` (raised with client) · `won` (contracted — move to SERVICES.md and implement via a new SPEC) · `discarded` (client declined or opportunity no longer applies).
