# Content catalog SQL design

The MVP remains JSON-based. This SQL is an optional future persistence target,
not a requirement to deploy PostgreSQL for the MVP. JSON validation, export,
application integration, and tests are deferred to the next stage.

## Migration stages

- `001_opportunities.sql` is the existing search prototype. Leave it unchanged
  for databases that have already applied it.
- `002_content_catalog.sql` adds the canonical model in the `catalog` schema.
  It does not alter, delete, or automatically copy legacy opportunity records.
  Apply each migration once, in filename order, using a migration ledger or
  an operator-maintained record. These scripts intentionally fail on reapplication.
- `content/seed_demo.sql` remains the legacy fixture. The separate
  `content/seed_catalog_demo.sql` illustrates all four new kinds after migration 002.
  It uses fixed dates and skips existing IDs on rerun; it does not refresh them.

No SQL was applied to a database during this design stage. Existing search/API
code still reads the legacy table and does not yet expose the new catalog.

## Combined model

`catalog.content_items` stores shared fields once, with conditional constraints
for each kind. Four filtered, updatable views provide the teammate's entry points:
`catalog.opportunities`, `catalog.events`, `catalog.programs`, and
`catalog.resources`. Inserts through a view must supply the matching
`content_kind`; CHECK OPTION prevents writing a different kind through that view.
IDs are globally unique across all four kinds. Search should eventually query
the shared table, not union independently ranked result sets.

An event is one scheduled occurrence; a program is an ongoing or cohort-based
experience; an opportunity is something to apply for or pursue; a resource is
reference material. Category (internship, workshop, mentorship, guide) is separate
from kind. Category and tag values are normalized but not a fixed taxonomy yet.

## Field mapping

| Earlier field | Shared contract | Notes |
| --- | --- | --- |
| Teammate's table name | `content_kind` | opportunity/event/program/resource |
| `type` / `opportunity_type` | `category` | Must not be used to guess kind without review |
| `url` / `source_url` | `url` | HTTP(S), no whitespace |
| `organization`, `source`, `last_updated` | Same names | Required except resource organization |
| `location` / `location_name` | `location` | Display text, alongside `location_mode` |
| `eligibility` | `eligibility` | Human-readable requirements retained |
| Structured eligibility arrays | Same names | Separate from `relevant_majors` |
| Event `date` / `time` | Date-only or timed schedule | Requires a verified timezone |
| `deadline` / `application_deadline` | `deadline_date` / `deadline_at` | Preserve source precision |

Metadata must be verified, not filled with invented organizations or sources.
`last_updated` is the content revision date, not automatically changed on every
database write. Category, tags, relevant majors, and eligible majors normalize
to lowercase; prose and organization names retain their case.

## Missing values and eligibility

- `unknown` means requirements have not been verified. Empty arrays do not prove
  unrestricted eligibility.
- `unrestricted` explicitly means no eligibility restrictions; requirement arrays
  must be empty.
- `restricted` requires readable requirements and/or structured constraints.
  A prose-only restriction is valid content but is not machine-verifiable.
- Future recommendations must distinguish verified matches from unknown or
  unparsed requirements. Never claim eligibility solely because arrays are empty.
- Academic years preserve the prototype convention: 1, 2, 3, 4 (4 means fourth
  year or later). Major relevance describes subject matter, not admission rules.

## Dates, deadlines, and recurrence

- Date-only schedules use `start_date` and optional `end_date`; dates are inclusive.
  Timed schedules use `starts_at` and optional `ends_at`. Both require a named
  timezone. Never convert an unknown event time to midnight.
- Events require a schedule. Programs and opportunities may have unknown schedules.
  Resources have no participation schedule, deadline, or attendance location.
- Fixed deadlines have exactly one of `deadline_date` or `deadline_at`, with a
  timezone. A date-only deadline remains open through that local date; future
  filtering should compare against the next local midnight, not midnight at its start.
- `rolling`, `none`, and `unknown` are distinct statuses with no fabricated cutoff.
  Event deadlines represent registration; other participation deadlines represent
  applications. The model currently supports one deadline per item.
- `recurrence` is event-only display text. Store separate event records with unique
  IDs for searchable occurrences; no recurrence expansion is implemented here.
- Future expiration rules must consider both registration and occurrence dates for
  events. When an exact end is unknown, do not invent one. Programs may close for
  applications before they finish. Resources need freshness review, not date expiry.

## Next integration stage

1. Implement the same field rules in the JSON schema and content validation.
2. Review each legacy record's kind, category, source, organization, eligibility
   status, and date precision before generating canonical JSON. Preserve IDs.
3. Generate/import SQL from validated JSON when a database is needed; do not
   maintain independent production JSON and SQL seed catalogs.
4. Adapt search/API consumers and date-aware filtering, then update tests and CI.
5. Retire the legacy table only after a reviewed migration and consumer cutover.

The new schema is deliberately additive so this SQL-only work does not silently
change the behavior of the existing search implementation.
