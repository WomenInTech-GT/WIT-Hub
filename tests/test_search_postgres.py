"""Real PostgreSQL contract tests; set TEST_DATABASE_URL to enable.

All objects and fixture records live in a unique schema rolled back after each test.
"""
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import LiteralString, cast
from uuid import uuid4

import psycopg
import pytest
from psycopg import sql
from psycopg.rows import dict_row

from search.service import SearchFilters, StudentProfile, build_search, search_opportunities


@pytest.fixture
def db():
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL is required for PostgreSQL integration tests")
    with psycopg.connect(url) as conn:
        try:
            schema = "search_test_" + uuid4().hex
            conn.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
            conn.execute(sql.SQL("SET LOCAL search_path TO {}").format(sql.Identifier(schema)))
            migration = (Path(__file__).parents[1] / "backend/migrations/001_opportunities.sql").read_text()
            conn.execute(sql.SQL(cast(LiteralString, migration.removeprefix("BEGIN;").replace("COMMIT;", ""))))
            yield conn
        finally:
            conn.rollback()


def add(db, id, **changes):
    data = dict(id=id, title="WIT beginner coding workshop", description="Build coding projects",
                source_url="https://example.org/opportunity", opportunity_type="workshop",
                location_mode="online", location_name="Zoom", tags=["coding"])
    data.update(changes)
    db.execute(sql.SQL("INSERT INTO opportunities ({}) VALUES ({})").format(
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
    db.execute("UPDATE opportunities SET title = 'Robotics' WHERE id = 'other'")
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
