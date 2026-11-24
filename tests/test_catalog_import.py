"""Offline contract tests plus real PostgreSQL import tests (see db fixture)."""
from copy import deepcopy
from pathlib import Path
import json

import psycopg
import pytest
from pydantic import ValidationError

from scripts.import_catalog import (
    CATEGORIES, ReviewMapping, apply_import, digest, plan_import, read_records, ready_to_publish,
)
from search.service import SearchFilters, StudentProfile, search_opportunities
from tests.test_search_postgres import db

ROOT = Path(__file__).parents[1]


@pytest.fixture
def pr6_sources():
    paths = [ROOT / 'content/seed/opportunities.draft.json',
             ROOT / 'content/seed/student_projects.draft.json']
    if not all(path.is_file() for path in paths):
        pytest.skip('PR #6 source files will be supplied by the teammate merge')
    return read_records(paths[0], 'opportunities'), read_records(paths[1], 'projects')


def inputs():
    record = dict(id='review-test', title='A reviewed workshop', description='Learn Python in a guided workshop.',
                  type='Workshop', organizer='Example group', topics=[' Coding ', 'coding'],
                  eligibility='Faculty approval required', url='https://example.org/workshop',
                  source_reviewed='2026-11-01', event_date='2027-06-01', event_end_date='2027-06-02',
                  deadline='2027-05-01', publication_status='draft_review')
    mapping = dict(content_kind='event', category='workshop', timezone='America/New_York',
                   deadline_timezone='America/New_York', deadline_status='fixed', eligibility_status='restricted')
    manifest = dict(version=1, schema_review={'status': 'approved', 'reviewed_by': 'Test schema reviewer'},
                    records={record['id']: mapping})
    return [record], [], manifest


def approve(record, mapping):
    mapping.update(publication_status='approved', reviewed_by='Test editor', reviewed_at='2026-11-01T00:00:00Z')
    mapping['approved_digest'] = digest(record, ReviewMapping.model_validate(mapping).model_dump())


def test_pr6_all_records_mapped_and_not_publishable(pr6_sources):
    opportunities, projects = pr6_sources
    manifest = json.loads((ROOT / 'content/seed/catalog_mapping.json').read_text())
    entries = plan_import(opportunities, projects, manifest)
    assert len(opportunities) == 64 and len(projects) == 8 and len(entries) == 72
    assert all(e['mapping']['publication_status'] == 'draft_review' for e in entries)
    assert all(e['issues'] for e in entries)
    assert all(not r.get('description') for r in opportunities)
    assert all(e['row']['category'] == e['source']['type'].lower() for e in entries if e['group'] == 'opportunities')
    assert manifest['schema_review']['status'] == 'pending'


def test_mapping_preserves_precision_and_eligibility():
    opp, projects, manifest = inputs()
    entry = plan_import(opp, projects, manifest)[0]
    assert not entry['issues']
    row = entry['row']
    assert row['start_date'] == '2027-06-01' and row['end_date'] == '2027-06-02'
    assert row['schedule_precision'] == 'date' and 'starts_at' not in row
    assert row['tags'] == ['coding']
    assert row['eligibility'] == ['Faculty approval required']
    assert row['source'] == opp[0]['url']
    assert row['last_updated'] == opp[0]['source_reviewed']


@pytest.mark.parametrize('field,value,issue', [
    ('description', '', 'description'), ('event_date', '2027-02-30', 'event_date'),
    ('event_end_date', '2027-05-01', 'event_end_date'), ('deadline', '20270501', 'deadline'),
    ('url', 'javascript:alert(1)', 'url'), ('topics', ['coding', None], 'topics'),
    ('source_reviewed', None, 'last_updated'),
])
def test_source_errors_reported(field, value, issue):
    opp, projects, manifest = inputs()
    opp[0][field] = value
    assert any(message.startswith(issue + ':') or message.startswith(issue + '/')
               for message in plan_import(opp, projects, manifest)[0]['issues'])


@pytest.mark.parametrize('field,value,issue', [
    ('timezone', None, 'timezone'), ('timezone', 'EST', 'timezone'),
    ('timezone', 'Not/AZone', 'timezone'), ('deadline_timezone', None, 'deadline_timezone'),
    ('content_kind', None, 'content_kind'), ('category', 'unknown-category', 'category'),
    ('eligibility_status', 'unrestricted', 'eligibility_status'),
    ('experience_levels', ['EXPERT'], 'experience_levels'), ('eligible_years', [5], 'eligible_years'),
])
def test_mapping_errors_reported(field, value, issue):
    opp, projects, manifest = inputs()
    manifest['records']['review-test'][field] = value
    assert any(message.startswith(issue + ':') for message in plan_import(opp, projects, manifest)[0]['issues'])


def test_approval_cannot_be_reused_after_changes():
    opp, projects, manifest = inputs()
    mapping = manifest['records']['review-test']
    approve(opp[0], mapping)
    assert not plan_import(opp, projects, manifest)[0]['issues']
    opp[0]['description'] = 'Changed after review'
    assert any('stale approval' in e for e in plan_import(opp, projects, manifest)[0]['issues'])
    approve(opp[0], mapping)
    mapping['timezone'] = 'Europe/London'
    assert any('stale approval' in e for e in plan_import(opp, projects, manifest)[0]['issues'])


def test_readiness_requires_schema_approval_as_well_as_content():
    opp, projects, manifest = inputs()
    approve(opp[0], manifest['records']['review-test'])
    assert ready_to_publish(plan_import(opp, projects, manifest), manifest)
    manifest['schema_review']['status'] = 'pending'
    assert not ready_to_publish(plan_import(opp, projects, manifest), manifest)


def test_duplicate_ids_and_incomplete_mapping_rejected():
    opp, projects, manifest = inputs()
    with pytest.raises(ValueError, match='Duplicate'):
        plan_import(opp + opp, projects, manifest)
    manifest['records'] = {}
    with pytest.raises(ValueError, match='missing record-level'):
        plan_import(opp, projects, manifest)


def test_mapping_typos_and_null_arrays_rejected():
    opp, projects, manifest = inputs()
    manifest['records']['review-test']['experience_levels'] = ['beginner', None]
    with pytest.raises(ValidationError):
        plan_import(opp, projects, manifest)
    manifest['records']['review-test'] = {'content_knd': 'event'}
    with pytest.raises(ValidationError):
        plan_import(opp, projects, manifest)


def test_sql_vocabulary_matches_import_contract(db):
    assert {row[0] for row in db.execute('SELECT category FROM catalog.categories')} == CATEGORIES


def test_import_publish_withdraw_and_repeat(db):
    opp, projects, manifest = inputs()
    for _ in range(2):
        apply_import(db, opp, projects, manifest)
    assert db.execute('SELECT count(*) FROM catalog.content_drafts').fetchone()[0] == 1
    assert not search_opportunities(db, SearchFilters(include_expired=True))
    approve(opp[0], manifest['records']['review-test'])
    for _ in range(2):
        apply_import(db, opp, projects, manifest)
    rows = search_opportunities(db, SearchFilters(include_expired=True))
    assert [row['id'] for row in rows] == ['review-test']
    assert 'reviewed_by' not in rows[0]
    # Preserved eligibility prose does not turn into an automatic recommendation.
    assert not search_opportunities(db, SearchFilters(), StudentProfile())
    manifest['records']['review-test']['publication_status'] = 'rejected'
    apply_import(db, opp, projects, manifest)
    assert not search_opportunities(db, SearchFilters(include_expired=True))


def test_import_validates_before_writes_and_rolls_back_collision(db):
    opp, projects, manifest = inputs()
    manifest['schema_review']['status'] = 'pending'
    with pytest.raises(ValueError, match='Schema mapping'):
        apply_import(db, opp, projects, manifest)
    manifest['schema_review']['status'] = 'approved'
    approve(opp[0], manifest['records']['review-test'])
    opp[0]['description'] = None
    with pytest.raises(ValueError, match='validation errors'):
        apply_import(db, opp, projects, manifest)
    assert db.execute('SELECT count(*) FROM catalog.content_drafts').fetchone()[0] == 0
    opp, projects, manifest = inputs()
    second = dict(opp[0], id='collision')
    opp.append(second)
    manifest['records']['collision'] = deepcopy(manifest['records']['review-test'])
    from tests.test_search_postgres import add
    add(db, 'collision')
    with pytest.raises(ValueError, match='manual reconciliation'):
        apply_import(db, opp, projects, manifest)
    assert db.execute('SELECT count(*) FROM catalog.content_drafts').fetchone()[0] == 0


def test_pr6_drafts_stage_without_becoming_searchable(pr6_sources, db):
    opp, projects = pr6_sources
    manifest = json.loads((ROOT / 'content/seed/catalog_mapping.json').read_text())
    manifest['schema_review'] = {'status': 'approved', 'reviewed_by': 'Test only'}
    apply_import(db, opp, projects, manifest)
    assert db.execute('SELECT count(*) FROM catalog.content_drafts').fetchone()[0] == 64
    assert db.execute('SELECT count(*) FROM catalog.student_projects').fetchone()[0] == 8
    assert not search_opportunities(db, SearchFilters(include_expired=True))
    assert db.execute('SELECT count(*) FROM catalog.published_student_projects').fetchone()[0] == 0


def test_project_permission_and_separate_publication(db):
    project = dict(id='project-test', title='Demo student project', type='Robotics',
                   team='Test team', year=2026, summary='A fictional robotics project.',
                   problem='Test problem', solution='Test solution', technologies=['Python'],
                   url='https://example.org/project', publication_permission='unconfirmed',
                   publication_status='draft_review')
    mapping = dict(publication_permission='granted', permission_evidence='Test-only signed release')
    manifest = dict(version=1, schema_review={'status': 'approved', 'reviewed_by': 'Test'},
                    records={project['id']: mapping})
    approve(project, mapping)
    apply_import(db, [], [project], manifest)
    result = db.execute('SELECT team, year, problem, solution, technologies FROM catalog.published_student_projects').fetchone()
    assert result[0] == project['team'] and result[1] == project['year']
    assert result[2] == project['problem'] and result[3] == project['solution']
    assert result[4]
    assert not search_opportunities(db, SearchFilters(include_expired=True))
    with pytest.raises(psycopg.errors.CheckViolation), db.transaction():
        db.execute("UPDATE catalog.student_projects SET publication_permission = 'unconfirmed'")
    mapping.update(publication_status='draft_review', publication_permission='denied')
    apply_import(db, [], [project], manifest)
    assert db.execute('SELECT count(*) FROM catalog.published_student_projects').fetchone()[0] == 0
