from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from backend.app.main import app
from search.service import SearchFilters, StudentProfile, build_search, explain_match


@pytest.mark.parametrize("values", [
    {"limit": 0}, {"limit": 101}, {"offset": -1}, {"academic_years": [5]},
    {"timeline": "title"}, {"location_modes": ["hybrid"]},
    {"date_from": "2026-11-01T10:00:00"},
    {"date_from": "2026-12-01T00:00:00Z", "date_to": "2026-11-01T00:00:00Z"},
])
def test_invalid_filters(values):
    with pytest.raises(ValidationError):
        SearchFilters(**values)


def test_default_deadline_and_explicit_override():
    now = datetime(2026, 10, 30, tzinfo=timezone.utc)
    sql, params = build_search(SearchFilters(), now=now)
    assert "application_deadline >= %(now)s" in sql
    assert params["now"] == now
    sql, _ = build_search(SearchFilters(include_expired=True))
    assert "application_deadline >= %(now)s" not in sql
    sql, _ = build_search(SearchFilters(include_expired=True), StudentProfile())
    assert "application_deadline >= %(now)s" in sql


def test_values_are_parameters_and_unknown_eligibility_is_conservative():
    query = "'; DROP TABLE opportunities; --"
    sql, params = build_search(SearchFilters(query=query, location="%_"), StudentProfile())
    assert query not in sql
    assert params["query"] == query
    assert params["location"] == "%_"
    assert params["student_majors"] == []
    assert "eligible_majors && %(student_majors)s::text[]" in sql


def test_normalization_and_explanations():
    profile = StudentProfile(interests=[" Coding ", "coding"], opportunity_types=["Workshop"],
                             location_modes=["online"])
    assert profile.interests == ["coding"]
    reasons = explain_match({"tags": ["coding", "music"], "opportunity_type": "workshop",
                             "location_mode": "online"}, profile)
    assert reasons == ["Matches your interests: coding", "Preferred opportunity type: workshop",
                       "Preferred location format: online"]


def test_year_filter_uses_postgres_integer_array():
    # psycopg may infer smallint[] for Python values 1-4; cast for the && operator.
    sql, params = build_search(SearchFilters(academic_years=[1, 4]))
    assert "eligible_years && %(academic_years)s::integer[]" in sql
    assert params["academic_years"] == [1, 4]


def test_api_validation_and_missing_configuration(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    client = TestClient(app)
    assert client.post("/api/search", json={"limit": -1}).status_code == 422
    assert client.post("/api/search", json={}).status_code == 503
    assert client.post("/api/recommendations", json={"profile": {}}).status_code == 503
    assert client.get("/health").status_code == 200
