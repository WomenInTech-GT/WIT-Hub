# Content catalog SQL design

The MVP remains JSON-based. This SQL is an optional future persistence target,
not a requirement to deploy PostgreSQL for the MVP. The PostgreSQL search path is integrated; JSON validation and export remain follow-up work.

## Setup and existing databases

`002_content_catalog.sql` is now the standalone baseline. Apply it once to a new
PostgreSQL database, then optionally load `content/seed_catalog_demo.sql`.
The number is retained so installations that already applied it do not confuse
it with a new migration. Search, API, CI, and tests now use `catalog.content_items`.
The earlier opportunity migration and seed have been removed from the repository.

Existing databases: apply the catalog migration only if it has not already been
applied. It does not copy or delete the old `public.opportunities` table. Export
and review any real records before importing them into the catalog; verify kind,
organization, source, dates, and eligibility rather than inventing metadata.
Keep deployed migration records/backups. Do not drop the old table until its data
has been migrated and checked. No user database is modified by this code change.

Integration tests require a disposable database without a `catalog` schema;
they create that schema inside a transaction and roll it back after each test.
They never drop an existing schema. Run them before loading the demo catalog.

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

## Remaining JSON MVP work

The PostgreSQL search implementation is now integrated. JSON validation, static
client-side search, and JSON-to-SQL import/export remain separate follow-up work.
When introduced, validated JSON should be the source of truth rather than a
second independently maintained production catalog.
