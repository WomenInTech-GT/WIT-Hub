"""Real PostgreSQL contract tests; set TEST_DATABASE_URL to enable.

Use a disposable database without a catalog schema. Each test rolls back its schema.
"""
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import LiteralString, cast


import psycopg
import pytest
from psycopg import sql
from psycopg.rows import dict_row

from search.service import RankingWeights, SearchFilters, StudentProfile, build_search, search_opportunities


@pytest.fixture
def db():
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL is required for PostgreSQL integration tests")
    with psycopg.connect(url) as conn:
        try:
            # Dedicated disposable database: never drop or reuse an existing catalog.
            migration = (Path(__file__).parents[1] / "backend/migrations/002_content_catalog.sql").read_text()
            migration = migration.replace("BEGIN;", "", 1).rsplit("COMMIT;", 1)[0]
            conn.execute(sql.SQL(cast(LiteralString, migration)))
            yield conn
        finally:
            conn.rollback()


def add(db, id, **changes):
    data = dict(id=id, title="WIT beginner coding workshop", description="Build coding projects",
                url="https://example.org/opportunity", category="workshop",
                location_mode="online", location="Zoom", tags=["coding"], content_kind="opportunity", organization="Demo",
                source="Test fixture", last_updated="2026-11-09", eligibility_status="unrestricted")
    for old, new in {"source_url": "url", "opportunity_type": "category",
                     "location_name": "location", "application_deadline": "deadline_at"}.items():
        if old in changes:
            changes[new] = changes.pop(old)
    data.update(changes)
    if not data["description"]:
        data["description"] = "Fixture description"
    if data.get("starts_at"):
        data.setdefault("schedule_precision", "time")
        data.setdefault("timezone", "America/New_York")
    if data.get("deadline_at") or data.get("deadline_date"):
        data.setdefault("deadline_status", "fixed")
        data.setdefault("deadline_timezone", "America/New_York")
    if any(data.get(k) for k in ("eligible_majors", "eligible_years", "experience_levels", "eligibility")):
        data["eligibility_status"] = "restricted"
    db.execute(sql.SQL("INSERT INTO catalog.content_items ({}) VALUES ({})").format(
        sql.SQL(",").join(map(sql.Identifier, data)),
        sql.SQL(",").join(sql.Placeholder() for _ in data)), list(data.values()))


def ids(db, filters=None, profile=None):
    return [r["id"] for r in search_opportunities(db, filters or SearchFilters(), profile)]


def test_deadline_boundaries_and_override(db):
    now = datetime.now(timezone.utc)
    add(db, "expired", application_deadline=now - timedelta(seconds=1))
    add(db, "boundary", application_deadline=now)
    add(db, "open")
    statement, params = build_search(SearchFilters(), now=now)
    with db.cursor(row_factory=dict_row) as cur:
        cur.execute(statement, params)
        assert [r["id"] for r in cur.fetchall()] == ["boundary", "open"]
    assert set(ids(db, SearchFilters(include_expired=True))) == {"expired", "boundary", "open"}


def test_lexical_phrases_acronyms_and_trigger_updates(db):
    add(db, "coding")
    add(db, "other", title="Music workshop", description="Play piano", tags=["music"])
    assert ids(db, SearchFilters(query='WIT "beginner coding"')) == ["coding"]
    assert ids(db, SearchFilters(query="piano")) == ["other"]
    db.execute("UPDATE catalog.content_items SET title = 'Robotics' WHERE id = 'other'")
    assert ids(db, SearchFilters(query="robotics")) == ["other"]
    assert ids(db, SearchFilters(query="nonexistent")) == []


def test_eligibility_ranking_and_pagination(db):
    add(db, "a-low", tags=["music"])
    add(db, "z-best", eligible_majors=[" Computer Science "], eligible_years=[1],
        experience_levels=["beginner"])
    add(db, "wrong-major", eligible_majors=["physics"])
    add(db, "wrong-year", eligible_years=[4])
    add(db, "wrong-level", experience_levels=["advanced"])
    add(db, "expired", application_deadline=datetime.now(timezone.utc) - timedelta(days=1))
    profile = StudentProfile(majors=["computer science"], academic_year=1,
                             experience_level="beginner", interests=["coding"])
    assert ids(db, SearchFilters(limit=1, include_expired=True), profile) == ["z-best"]
    assert ids(db, SearchFilters(offset=1), profile) == ["a-low"]
    assert ids(db, profile=StudentProfile()) == ["a-low"]


def test_combined_filters_and_availability(db):
    start = datetime.now(timezone.utc) + timedelta(days=10)
    add(db, "match", starts_at=start, ends_at=start + timedelta(hours=1))
    add(db, "unknown-time")
    add(db, "physical", location_mode="in-person", location_name="Main Street", starts_at=start)
    filters = SearchFilters(academic_years=[1], majors=["physics"], opportunity_types=["workshop"],
                            location_modes=["online"], location="zoom", date_from=start, date_to=start)
    assert ids(db, filters) == ["match"]
    assert ids(db, SearchFilters(timeline="deadline", date_from=start)) == []
    assert ids(db, profile=StudentProfile(available_from=start, available_to=start + timedelta(hours=2))) == ["match"]
    assert ids(db, SearchFilters(location="%")) == []


def test_expansion_correction_and_required_terms(db):
    add(db, 'expanded', title='Computer science internship', description='', tags=[],
        starts_at=datetime(2027, 7, 1, tzinfo=timezone.utc))
    add(db, 'irrelevant', title='Computer science conference', description='', tags=[],
        starts_at=datetime(2027, 7, 1, tzinfo=timezone.utc))
    assert ids(db, SearchFilters(query='CS internshps summer 2027')) == ['expanded']
    assert ids(db, SearchFilters(query='CS internshps summer 2027', interpret=False)) == []
    assert ids(db, SearchFilters(query='"CS internship"')) == []


def test_next_week_boundaries_and_expiration(db):
    now = datetime.fromisoformat('2026-10-31T12:00:00-04:00')
    for id, start in [('before', '2026-11-01T23:59:59-05:00'),
                      ('first', '2026-11-02T00:00:00-05:00'),
                      ('last', '2026-11-08T23:59:59-05:00'),
                      ('after', '2026-11-09T00:00:00-05:00')]:
        add(db, id, title='Women in Tech event', starts_at=datetime.fromisoformat(start))
    add(db, 'expired', title='Women in Tech event', starts_at=datetime.fromisoformat('2026-11-03T12:00:00-05:00'),
        application_deadline=now - timedelta(seconds=1))
    rows = search_opportunities(db, SearchFilters(query='WIT events next week'), now=now)
    assert [r['id'] for r in rows] == ['first', 'last']
    assert len(search_opportunities(db, SearchFilters(query='next week'), now=now)) == 2


def test_lexical_ranking_and_stable_pages(db):
    add(db, 'z-title', title='Robotics', description='', tags=[])
    add(db, 'a-body', title='Engineering research', description='Robotics', tags=[])
    add(db, 'b-body', title='Engineering research', description='Robotics', tags=[])
    add(db, 'irrelevant', title='Music', description='', tags=[])
    rows = search_opportunities(db, SearchFilters(query='robotics'))
    assert [r['id'] for r in rows] == ['z-title', 'a-body', 'b-body']
    assert rows[0]['lexical_score'] > rows[1]['lexical_score']
    assert ids(db, SearchFilters(query='robotics', limit=1, offset=1)) == ['a-body']


def test_stopwords_and_exclusions(db):
    add(db, 'robot', title='Robotics', description='', tags=[])
    add(db, 'ai', title='Robotics AI', description='', tags=[])
    assert ids(db, SearchFilters(query='the and')) == []
    assert ids(db, SearchFilters(query='!!!')) == []
    assert ids(db, SearchFilters(query='robotics -AI')) == ['robot']


def test_tunable_recommendation_order_and_explanations(db):
    add(db, 'interest', tags=['coding'], opportunity_type='research', location_mode='in-person')
    add(db, 'format', tags=['music'], opportunity_type='workshop', location_mode='online')
    profile = StudentProfile(interests=['coding'], opportunity_types=['workshop'], location_modes=['online'])
    rows = search_opportunities(db, SearchFilters(limit=1), profile, RankingWeights(interests=4))
    assert rows[0]['id'] == 'interest'
    assert rows[0]['explanations'] == ['Matches your interests: coding']
    rows = search_opportunities(db, SearchFilters(limit=1), profile, RankingWeights(interests=1))
    assert rows[0]['id'] == 'format'
    assert len(rows[0]['explanations']) == 2


def test_explicit_or_and_quoted_phrases(db):
    add(db, 'robotics', title='Robotics', description='', tags=[])
    add(db, 'phrase', title='Machine learning', description='', tags=[])
    add(db, 'separated', title='Machine design and learning', description='', tags=[])
    add(db, 'unrelated', title='Music', description='', tags=[])
    assert set(ids(db, SearchFilters(query='robotics OR "machine learning"'))) == {'robotics', 'phrase'}
    assert ids(db, SearchFilters(query='"machine learning"')) == ['phrase']


def test_inferred_start_window_intersects_explicit_deadline_window(db):
    now = datetime.fromisoformat('2026-10-31T12:00:00-04:00')
    for id, start, deadline in [
        ('match', '2026-11-03T12:00:00-05:00', '2026-11-02T12:00:00-05:00'),
        ('wrong-start', '2026-11-10T12:00:00-05:00', '2026-11-02T12:00:00-05:00'),
        ('wrong-deadline', '2026-11-03T12:00:00-05:00', '2026-11-04T12:00:00-05:00'),
    ]:
        add(db, id, starts_at=datetime.fromisoformat(start),
            application_deadline=datetime.fromisoformat(deadline))
    add(db, 'unknown-start', application_deadline=datetime.fromisoformat('2026-11-02T12:00:00-05:00'))
    filters = SearchFilters(query='next week', timeline='deadline',
                            date_from='2026-11-02T00:00:00-05:00',
                            date_to='2026-11-03T00:00:00-05:00')
    assert [r['id'] for r in search_opportunities(db, filters, now=now)] == ['match']

def test_catalog_kinds_and_compatibility_fields(db):
    add(db, 'program', content_kind='program', category='mentorship', location_mode='hybrid')
    add(db, 'resource', content_kind='resource', category='guide',
        schedule_precision='not-applicable', location_mode='not-applicable', location=None,
        deadline_status='none')
    rows = search_opportunities(db, SearchFilters(content_kinds=['program'], categories=['mentorship'],
                                                  location_modes=['hybrid']))
    assert [r['id'] for r in rows] == ['program']
    assert rows[0]['category'] == rows[0]['opportunity_type'] == 'mentorship'
    assert rows[0]['url'] == rows[0]['source_url']
    assert 'search_vector' not in rows[0]
    assert ids(db, SearchFilters(content_kinds=['resource'])) == ['resource']

def test_unknown_and_unparsed_eligibility_are_not_recommended(db):
    add(db, 'unknown', eligibility_status='unknown')
    add(db, 'prose', eligibility=['Requires faculty approval'])
    add(db, 'open')
    assert set(ids(db)) == {'unknown', 'prose', 'open'}
    assert ids(db, profile=StudentProfile()) == ['open']

def test_date_only_deadline_dst_and_expired_events(db):
    add(db, 'deadline', deadline_date='2026-11-01')
    add(db, 'event', content_kind='event', schedule_precision='date',
        start_date='2026-11-01', timezone='America/New_York')
    before = datetime.fromisoformat('2026-11-02T04:59:59+00:00')
    after = datetime.fromisoformat('2026-11-02T05:00:00+00:00')
    assert {r['id'] for r in search_opportunities(db, SearchFilters(), now=before)} == {'deadline', 'event'}
    assert search_opportunities(db, SearchFilters(), now=after) == []
    assert len(search_opportunities(db, SearchFilters(include_expired=True), now=after)) == 2

def test_date_only_query_preserves_precision(db):
    add(db, 'date', content_kind='event', schedule_precision='date',
        start_date='2026-11-02', timezone='America/New_York')
    add(db, 'outside', content_kind='event', schedule_precision='date',
        start_date='2026-11-09', timezone='America/New_York')
    now = datetime.fromisoformat('2026-10-31T12:00:00-04:00')
    rows = search_opportunities(db, SearchFilters(query='next week'), now=now)
    assert [r['id'] for r in rows] == ['date']
    assert rows[0]['starts_at'] is None
    assert str(rows[0]['start_date']) == '2026-11-02'

def test_new_seed_is_standalone_and_repeatable(db):
    seed = (Path(__file__).parents[1] / 'content/seed_catalog_demo.sql').read_text()
    seed = seed.replace('BEGIN;', '', 1).rsplit('COMMIT;', 1)[0]
    for _ in range(2):
        db.execute(sql.SQL(cast(LiteralString, seed)))
    assert db.execute('SELECT count(*) FROM catalog.content_items').fetchone()[0] == 20
    assert {r['content_kind'] for r in search_opportunities(db, SearchFilters(include_expired=True))} == {
        'opportunity', 'event', 'program', 'resource'}

def test_api_serializes_catalog_dates_and_compatibility_fields(db, monkeypatch):
    from contextlib import contextmanager
    from fastapi.testclient import TestClient
    from backend.app.main import app

    add(db, 'api', content_kind='program', schedule_precision='date',
        start_date='2027-06-01', timezone='America/New_York')

    @contextmanager
    def connect(*args, **kwargs):
        yield db

    monkeypatch.setenv('DATABASE_URL', 'test-connection')
    monkeypatch.setattr('backend.app.main.psycopg.connect', connect)
    client = TestClient(app)
    response = client.post('/api/search', json={'content_kinds': ['program']})
    assert response.status_code == 200
    item = response.json()['items'][0]
    assert item['start_date'] == '2027-06-01'
    assert item['starts_at'] is None
    assert item['source_url'] == item['url']
    assert client.post('/api/recommendations', json={'profile': {}}).json()['items'][0]['id'] == 'api'
