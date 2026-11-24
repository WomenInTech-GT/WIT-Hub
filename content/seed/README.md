# Draft source and catalog import

Source: [PR #6](https://github.com/WomenInTech-GT/WIT-Hub/pull/6),
head `dcf62127a0e30524a0c02c13355f43af52d0968c`.
The source JSON/CSV and export/validation scripts are intentionally absent here:
they will arrive through the teammate's PR merge. This change contains only the
new mapping, import, publication controls and related tests/documentation.
Descriptions can be supplied in the mapping without modifying teammate-owned
files. Missing descriptions remain publication blockers. The teammate's exporter
would need separate Description-column support if descriptions are authored in CSV.
No live links, dates, eligibility or permissions have been independently verified.
`catalog_import_review.json` is a historical report generated while the source
snapshot was available: 72 records, zero approved. Regenerate it after the merge;
its digests are not current approvals. Source-dependent tests and the CI preview
skip until both seed JSON files are present; synthetic importer tests still run.

## Review the mapping

`catalog_mapping.json` contains a proposed entry for every one of the 64 opportunity
records and eight projects. No record is approved. Tina still needs to verify
the schema, expressed by `schema_review.status: pending`.

- `id`, `title`, `url` map directly; `organizer` becomes `organization`.
- `type` is preserved as a specific lowercase `category`; migration 004 adds
  the required vocabulary. `content_kind` is chosen per record, not inferred
  at import time. Directories are resources; ongoing initiatives are programs;
  scheduled occurrences are events; applications/awards are opportunities.
  A student-project showcase event is distinct from the projects it showcases.
- `topics` becomes normalized `tags`. No subject is assumed to be an eligible major.
- `description` comes from source JSON or the mapping's reviewed description.
  Do not copy editorial warnings into public descriptions or fabricate facts.
- `source` defaults to the official source URL (provenance, not the organizer).
- `last_updated` initially uses `source_reviewed` for this imported revision.
  On later editorial edits, set the mapping's `last_updated` to the actual content
  revision date; the raw source review date remains in the staging payload.
- `event_date`/`event_end_date` become date-only start/end dates; `deadline`
  becomes a date-only fixed deadline. Missing dates stay unknown. Events without
  verified dates remain drafts. Raw date/availability/editorial fields are retained
  in `source_payload`; they are never silently parsed into asserted facts.
- Set `timezone` and `deadline_timezone` independently where dates exist.
  Use a verified IANA name such as `America/New_York` for Eastern local time,
  not fixed `EST`. International events may need different zones. No default
  timezone is assumed; no date-only value is converted into a midnight timestamp.
- Explicitly choose `deadline_status`: fixed with a date, or unknown/rolling/none.
  An absent deadline does not establish that applications are open or rolling.
- Source eligibility prose is retained as an array with `restricted` status.
  Prose-only restrictions stay out of automatic recommendations. Structured majors,
  years and experience levels can be added after verification. Empty requirements
  use `unknown`; `unrestricted` requires an explicit editorial decision.
- Resource mappings explicitly use `deadline_status: none` and
  `location_mode: not-applicable`. Unknown participation location stays unknown.

## Commands (PowerShell, repository root)

Use an installed Python environment with `backend/requirements.txt`, or prefix
the `python` commands below with `uv run --with-requirements backend/requirements.txt`.
Neither Python, uv nor psql is assumed to be preinstalled.
The default paths require PR #6 to be merged first. Alternatively supply your own
files using `--opportunities`, `--projects` and a matching `--mapping` manifest.

```powershell
# Offline preview: no database connection or writes.
python -m scripts.import_catalog --report catalog-import-report.json

# Strict readiness check: exits 1 while any record is draft or invalid.
python -m scripts.import_catalog --check-ready

```

The import report lists each record's blockers and `approval_digest`. A successful
dry run only means the source and manifest can be processed; it is not approval.
The teammate's exporter and source QA commands will be available after PR #6 merges.
The importer independently checks missing descriptions and duplicate IDs. HTTP
success alone never verifies that a listing's facts or eligibility are correct.

## Apply and publish only after review

1. Review the proposed schema and set `schema_review.status` to `approved` and
   `schema_review.reviewed_by` to the actual schema reviewer. This authorizes the
   CLI's schema mapping, not the content. Keep pending while Tina's review is pending.
2. Apply migrations **002, 003, 004 in order**, once each, using psql's `-f` option.
   For an existing 003 installation, apply only 004. **004 marks all existing
   catalog content as draft**; it does not grant retrospective publication approval.
   Deploy the updated search code with the migration. Only explicitly approved
   rows appear in `catalog.published_content` and the search/recommendation API.
3. With a reviewed schema, `--apply` can save incomplete records as drafts.
   Opportunity drafts go to `catalog.content_drafts`; student projects go to
   `catalog.student_projects`. The importer does not create or migrate the schema.
4. For publication, resolve a record's report issues, verify source facts and
   mapping, and rerun the preview. Set `publication_status: approved`, an actual
   `reviewed_by`, an ISO `reviewed_at` timestamp with timezone, and `approved_digest`
   to the digest from the report. Digest changes require fresh review. Approval
   metadata is deliberately excluded from the digest so those final edits do not
   invalidate it. The digest is a change detector, not a cryptographic signature.
5. Set `DATABASE_URL` in your own environment, then run:

```powershell
python -m scripts.import_catalog --apply --report catalog-import-report.json
```

The CLI is an operator tool, not an authenticated web administrator interface.
Review identity is operator-supplied; restrict database credentials to authorized
editors. It exposes no public write/approve endpoint.

Imports are parameterized, transactional and repeatable. Any invalid approved
record, database constraint error, or conflicting existing ID rolls back the entire
batch. Existing records maintained outside this importer are not overwritten.
Reimporting a tracked record as draft or rejected hides its previous public row.
Omitting a record is **not** a deletion or withdrawal; explicitly mark it rejected.
Duplicate IDs (including collisions between opportunities and projects) are rejected.

Student projects retain team, year, summary, problem, solution, technologies,
original category and source payload separately. Publication additionally requires
`publication_permission: granted` and nonempty `permission_evidence`. Only approved,
permitted projects appear in `catalog.published_student_projects`; they never enter
opportunity search. A dedicated public project page/search API remains a separate
product feature. The eight imported projects remain unconfirmed and unpublished.

Do not host the draft seed directory as public site assets. Only export approved
views if implementing a future static JSON search. No real records were published
and no production database was changed by this implementation.
