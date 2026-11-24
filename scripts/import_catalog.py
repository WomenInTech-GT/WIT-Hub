"""Validate PR #6 drafts and their record-level review mapping; dry-run by default.

Run from the repository root: python -m scripts.import_catalog --help.
Only --apply connects to PostgreSQL. It requires a reviewed schema manifest.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, ValidationError

ROOT = Path(__file__).resolve().parents[1]
BASE_CATEGORIES = {
    'internship', 'scholarship', 'competition', 'job', 'research', 'project',
    'workshop', 'conference', 'hackathon', 'event', 'program', 'mentorship', 'guide', 'tutorial',
}
SPECIFIC_CATEGORIES = {
    'conference support', 'award', 'recognition', 'leadership program', 'workshop series',
    'mentorship program', 'research internship', 'research directory', 'research opportunity',
    'career event', 'research advising', 'international internship', 'course / program',
    'innovation program', 'capstone program', 'accelerator', 'makerspace', 'seminar',
    'conference session', 'student project showcase', 'info session',
}
CATEGORIES = BASE_CATEGORIES | SPECIFIC_CATEGORIES
ALIASES = {value + 's': value for value in BASE_CATEGORIES if value != 'research'}


class ReviewMapping(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    content_kind: Literal['opportunity', 'event', 'program', 'resource'] | None = None
    category: str | None = None
    description: str | None = None
    source: str | None = None
    last_updated: str | None = None
    timezone: str | None = None
    deadline_timezone: str | None = None
    deadline_status: Literal['unknown', 'fixed', 'rolling', 'none'] = 'unknown'
    eligibility_status: Literal['unknown', 'unrestricted', 'restricted'] = 'unknown'
    eligible_majors: list[str] = Field(default_factory=list)
    eligible_years: list[int] = Field(default_factory=list)
    experience_levels: list[str] = Field(default_factory=list)
    location_mode: Literal['unknown', 'online', 'in-person', 'hybrid', 'not-applicable'] = 'unknown'
    location: str | None = None
    publication_status: Literal['draft_review', 'approved', 'rejected'] = 'draft_review'
    reviewed_by: str | None = None
    reviewed_at: str | None = None
    approved_digest: str | None = None
    publication_permission: Literal['unconfirmed', 'granted', 'denied'] = 'unconfirmed'
    permission_evidence: str | None = None
    notes: str | None = None


def clean(value):
    return value.strip() if isinstance(value, str) else ''


def terms(values):
    return sorted({value.strip().lower() for value in values if value.strip()})


def digest(record, mapping):
    """Bind approval to both source content and the reviewed transformation."""
    mapping = {k: v for k, v in mapping.items()
               if k not in {'publication_status', 'reviewed_by', 'reviewed_at', 'approved_digest'}}
    encoded = json.dumps([record, mapping], sort_keys=True, ensure_ascii=False, separators=(',', ':'))
    return hashlib.sha256(encoded.encode('utf-8')).hexdigest()


def iso_date(value, field, issues, required=False):
    if value is None and not required:
        return None
    try:
        if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
            raise ValueError
        return date.fromisoformat(value).isoformat()
    except ValueError:
        issues.append(f'{field}: required valid YYYY-MM-DD date')
        return None


def valid_zone(value, field, issues):
    try:
        # Reject ambiguous abbreviations including EST; UTC is an explicit choice.
        if not isinstance(value, str) or ('/' not in value and value != 'UTC'):
            raise ValueError
        ZoneInfo(value)
        return value
    except (ValueError, ZoneInfoNotFoundError):
        issues.append(f'{field}: explicit IANA timezone required (e.g. America/New_York)')
        return None


def valid_url(value):
    if not isinstance(value, str) or re.search(r'\s', value):
        return False
    try:
        parsed = urlsplit(value)
        return parsed.scheme in ('http', 'https') and bool(parsed.hostname)
    except ValueError:
        return False


def review_issues(mapping, expected_digest):
    issues = []
    if mapping['publication_status'] == 'approved':
        if not clean(mapping['reviewed_by']):
            issues.append('reviewed_by: explicit reviewer required')
        try:
            stamp = datetime.fromisoformat(mapping['reviewed_at'] or '')
            if stamp.tzinfo is None or stamp > datetime.now(timezone.utc):
                raise ValueError
        except ValueError:
            issues.append('reviewed_at: non-future timestamp with timezone required')
        if mapping['approved_digest'] != expected_digest:
            issues.append('approved_digest: missing or stale approval; review this source and mapping again')
    return issues


def opportunity_row(record, mapping, issues):
    kind = mapping['content_kind']
    if kind is None:
        issues.append('content_kind: explicit record-level mapping required')
    category = clean(mapping['category']).lower()
    category = ALIASES.get(category, category)
    if category not in CATEGORIES:
        issues.append('category: choose an approved catalog category')
    row = dict(id=record['id'], content_kind=kind, category=category,
               title=clean(record.get('title')), description=clean(mapping['description'] or record.get('description')),
               organization=clean(record.get('organizer')) or None, url=record.get('url'),
               source=clean(mapping['source'] or record.get('url')),
               last_updated=iso_date(mapping['last_updated'] or record.get('source_reviewed'),
                                     'last_updated/source_reviewed', issues, required=True))
    for field in ('title', 'description', 'source'):
        if not row[field]:
            issues.append(f'{field}: required nonempty text')
    if kind != 'resource' and not row['organization']:
        issues.append('organizer: required for participation content')
    if not valid_url(row['url']):
        issues.append('url: valid HTTP(S) URL required')
    topics = record.get('topics', [])
    if not isinstance(topics, list) or any(not isinstance(v, str) for v in topics):
        issues.append('topics: must be an array of strings')
        topics = []
    row['tags'] = terms(topics)
    # Keep source prose; never silently translate it into a claim of eligibility.
    prose = record.get('eligibility')
    if prose is not None and not isinstance(prose, str):
        issues.append('eligibility: must be text or null')
    row.update(eligibility=[clean(prose)] if clean(prose) else [],
               eligibility_status=mapping['eligibility_status'],
               eligible_majors=terms(mapping['eligible_majors']),
               eligible_years=sorted(set(mapping['eligible_years'])),
               experience_levels=terms(mapping['experience_levels']))
    if any(v not in (1, 2, 3, 4) for v in row['eligible_years']):
        issues.append('eligible_years: only 1, 2, 3, 4 allowed')
    if set(row['experience_levels']) - {'beginner', 'intermediate', 'advanced'}:
        issues.append('experience_levels: only beginner, intermediate, advanced allowed')
    restricted = any(row[k] for k in ('eligibility', 'eligible_majors', 'eligible_years', 'experience_levels'))
    if restricted != (row['eligibility_status'] == 'restricted'):
        issues.append('eligibility_status: restrictions require restricted; empty requirements do not prove unrestricted')
    start = iso_date(record.get('event_date'), 'event_date', issues)
    end = iso_date(record.get('event_end_date'), 'event_end_date', issues)
    deadline = iso_date(record.get('deadline'), 'deadline', issues)
    if end and (not start or end < start):
        issues.append('event_end_date: must follow or equal event_date')
    row.update(schedule_precision='date' if start else 'unknown', start_date=start, end_date=end,
               timezone=valid_zone(mapping['timezone'], 'timezone', issues) if start else None,
               deadline_status=mapping['deadline_status'], deadline_date=deadline,
               deadline_timezone=valid_zone(mapping['deadline_timezone'], 'deadline_timezone', issues) if deadline else None,
               location_mode=mapping['location_mode'], location=clean(mapping['location']) or None)
    if not start and mapping['timezone']:
        issues.append('timezone: cannot supply a schedule timezone without a date')
    if not deadline and mapping['deadline_timezone']:
        issues.append('deadline_timezone: cannot supply a deadline timezone without a date')
    if (deadline is not None) != (row['deadline_status'] == 'fixed'):
        issues.append('deadline_status: fixed requires a deadline date; absent dates must remain explicit unknown/rolling/none')
    if kind == 'event' and not start:
        issues.append('event_date: events need a verified schedule before publication')
    if kind == 'resource':
        row['schedule_precision'] = 'not-applicable'
        if start or end or deadline or row['deadline_status'] != 'none' or row['location_mode'] != 'not-applicable' or row['location']:
            issues.append('resource: no schedule/deadline/location; use none and not-applicable explicitly')
    elif row['location_mode'] == 'not-applicable':
        issues.append('location_mode: participation content cannot use not-applicable in this import contract')
    row.update(publication_status=mapping['publication_status'], reviewed_by=mapping['reviewed_by'],
               reviewed_at=mapping['reviewed_at'])
    return row


def project_row(record, mapping, issues):
    row = {field: clean(record.get(field)) or None
           for field in ('title', 'team', 'summary', 'problem', 'solution', 'url')}
    row.update(id=record['id'], category=clean(record.get('type')) or None, year=record.get('year'))
    for field in ('title', 'category', 'team', 'summary', 'problem', 'solution'):
        if not row[field]:
            issues.append(f'{field}: required for a published student project')
    if type(row['year']) is not int or not 1900 <= row['year'] <= 9999:
        issues.append('year: integer between 1900 and 9999 required')
        row['year'] = None
    if not valid_url(row['url']):
        issues.append('url: valid HTTP(S) URL required')
        row['url'] = None
    tech = record.get('technologies', [])
    if not isinstance(tech, list) or any(not isinstance(v, str) for v in tech):
        issues.append('technologies: must be an array of strings')
        tech = []
    row['technologies'] = terms(tech)
    row.update({k: mapping[k] for k in ('publication_permission', 'permission_evidence',
                                      'publication_status', 'reviewed_by', 'reviewed_at')})
    if row['publication_permission'] != 'granted' or not clean(row['permission_evidence']):
        issues.append('publication_permission: explicit granted permission and evidence required before publishing')
    if record.get('publication_permission') == 'denied' and row['publication_permission'] == 'granted':
        issues.append('publication_permission: source denies publication; resolve before approving')
    return row


def plan_import(opportunities, projects, manifest):
    if not isinstance(manifest, dict) or manifest.get('version') != 1:
        raise ValueError('Mapping manifest must be an object with version 1')
    mappings = manifest.get('records')
    if not isinstance(mappings, dict):
        raise ValueError('Mapping manifest requires a records object keyed by ID')
    entries, seen = [], set()
    for group, records in (('opportunities', opportunities), ('projects', projects)):
        if not isinstance(records, list):
            raise ValueError(f'{group} must be a list')
        for record in records:
            if not isinstance(record, dict) or not clean(record.get('id')):
                raise ValueError(f'{group}: every record requires a nonblank string ID')
            rid = record['id']
            if rid != rid.strip() or rid in seen:
                raise ValueError(f'Duplicate or whitespace-padded ID: {rid}')
            seen.add(rid)
            if rid not in mappings:
                raise ValueError(f'{rid}: missing record-level mapping')
            mapping = ReviewMapping.model_validate(mappings[rid]).model_dump()
            fingerprint = digest(record, mapping)
            issues = review_issues(mapping, fingerprint)
            row = (opportunity_row if group == 'opportunities' else project_row)(record, mapping, issues)
            entries.append(dict(id=rid, group=group, source=record, mapping=mapping,
                                digest=fingerprint, row=row, issues=issues))
    if set(mappings) - seen:
        raise ValueError('Mapping has IDs absent from the input: ' + ', '.join(sorted(set(mappings) - seen)))
    return entries


def upsert(connection, table, row):
    from psycopg import sql
    fields = list(row)
    statement = sql.SQL('INSERT INTO catalog.{} ({}) VALUES ({}) ON CONFLICT (id) DO UPDATE SET {}').format(
        sql.Identifier(table), sql.SQL(', ').join(map(sql.Identifier, fields)),
        sql.SQL(', ').join(sql.Placeholder() for _ in fields),
        sql.SQL(', ').join(sql.SQL('{} = EXCLUDED.{}').format(sql.Identifier(k), sql.Identifier(k))
                          for k in fields if k != 'id'))
    connection.execute(statement, [row[k] for k in fields])


def apply_import(connection, opportunities, projects, manifest):
    """Revalidate before any writes; all rows are committed or rolled back together."""
    from psycopg.types.json import Jsonb
    entries = plan_import(opportunities, projects, manifest)
    approval = manifest.get('schema_review', {})
    if approval.get('status') != 'approved' or not clean(approval.get('reviewed_by')):
        raise ValueError('Schema mapping must be approved in schema_review before --apply')
    if any(e['issues'] and e['mapping']['publication_status'] == 'approved' for e in entries):
        raise ValueError('Approved records have validation errors; nothing imported')
    with connection.transaction():
        for entry in entries:
            rid, row = entry['id'], entry['row']
            # Never silently overwrite a manually maintained catalog record or another kind.
            existing = connection.execute('SELECT content_kind FROM catalog.content_items WHERE id = %s', (rid,)).fetchone()
            tracked = connection.execute('SELECT 1 FROM catalog.content_drafts WHERE id = %s', (rid,)).fetchone()
            project = connection.execute('SELECT 1 FROM catalog.student_projects WHERE id = %s', (rid,)).fetchone()
            if (entry['group'] == 'projects' and (existing or tracked)) or (entry['group'] == 'opportunities' and project):
                raise ValueError(f'{rid}: ID already belongs to the other content collection')
            if existing and (not tracked or existing[0] != row.get('content_kind')):
                raise ValueError(f'{rid}: existing catalog ID needs manual reconciliation')
            if entry['group'] == 'projects':
                upsert(connection, 'student_projects', dict(row, source_payload=Jsonb(entry['source']),
                                                           source_digest=entry['digest']))
            else:
                upsert(connection, 'content_drafts', dict(id=rid, source_payload=Jsonb(entry['source']),
                    mapping=Jsonb(entry['mapping']), source_digest=entry['digest'],
                    validation_issues=Jsonb(entry['issues']), publication_status=row['publication_status'],
                    imported_at=datetime.now(timezone.utc)))
                if row['publication_status'] == 'approved':
                    upsert(connection, 'content_items', row)
                else:
                    # Rejection or a revised draft withdraws the previously imported public row.
                    connection.execute('UPDATE catalog.content_items SET publication_status = %s, reviewed_by = NULL, reviewed_at = NULL WHERE id = %s',
                                       (row['publication_status'], rid))
    return entries


def read_records(path, key):
    payload = json.loads(Path(path).read_text(encoding='utf-8'))
    if not isinstance(payload, dict) or not isinstance(payload.get(key), list):
        raise ValueError(f'{path}: expected an object containing {key}: [...]')
    return payload[key]


def ready_to_publish(entries, manifest):
    schema = manifest.get('schema_review', {})
    return (isinstance(schema, dict) and schema.get('status') == 'approved'
            and bool(clean(schema.get('reviewed_by')))
            and bool(entries)
            and all(e['mapping']['publication_status'] == 'approved' and not e['issues'] for e in entries))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--opportunities', default=str(ROOT / 'content/seed/opportunities.draft.json'))
    parser.add_argument('--projects', default=str(ROOT / 'content/seed/student_projects.draft.json'))
    parser.add_argument('--mapping', default=str(ROOT / 'content/seed/catalog_mapping.json'))
    parser.add_argument('--report', help='Optional JSON report path; includes validation issues and review digests')
    parser.add_argument('--apply', action='store_true', help='Apply atomically using DATABASE_URL; requires schema review')
    parser.add_argument('--check-ready', action='store_true', help='Exit 1 unless every record is approved and valid')
    args = parser.parse_args()
    try:
        opportunities = read_records(args.opportunities, 'opportunities')
        projects = read_records(args.projects, 'projects')
        manifest = json.loads(Path(args.mapping).read_text(encoding='utf-8'))
        entries = plan_import(opportunities, projects, manifest)
        ready = ready_to_publish(entries, manifest)
        if args.apply and args.check_ready and not ready:
            raise ValueError('--check-ready failed; --apply made no database changes')
        if args.apply:
            import psycopg
            url = os.environ.get('DATABASE_URL')
            if not url:
                raise ValueError('DATABASE_URL is required for --apply')
            try:
                with psycopg.connect(url, connect_timeout=5) as connection:
                    apply_import(connection, opportunities, projects, manifest)
            except psycopg.Error as exc:
                # Report the failure without echoing a connection string or credentials.
                parser.exit(2, 'Import blocked; transaction rolled back: ' +
                            (exc.diag.message_primary or 'database connection/query failed') + '\n')
        report = dict(mode='applied' if args.apply else 'dry_run', records=len(entries),
                      ready_to_publish=ready,
                      approved=sum(e['mapping']['publication_status'] == 'approved' and not e['issues'] for e in entries),
                      records_with_issues=sum(bool(e['issues']) for e in entries),
                      schema_review=manifest.get('schema_review'),
                      entries=[dict(id=e['id'], collection=e['group'], status=e['mapping']['publication_status'],
                                    issues=e['issues'], approval_digest=e['digest']) for e in entries])
        if args.report:
            Path(args.report).write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
        print(json.dumps({k: v for k, v in report.items() if k != 'entries'}, indent=2))
        return 1 if args.check_ready and not ready else 0
    except (ValueError, ValidationError, OSError) as exc:
        parser.exit(2, f'Import blocked: {exc}\n')


if __name__ == '__main__':
    raise SystemExit(main())
