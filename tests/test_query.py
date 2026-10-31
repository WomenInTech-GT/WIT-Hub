from datetime import datetime

import pytest

from search.query import interpret_query
from search.service import SearchFilters, build_search

NOW = datetime.fromisoformat('2026-10-31T12:00:00-04:00')


@pytest.mark.parametrize('query,start,end', [
    ('next week', '2026-11-02T00:00:00-05:00', '2026-11-09T00:00:00-05:00'),
    ('this weekend', '2026-10-31T00:00:00-04:00', '2026-11-02T00:00:00-05:00'),
    ('summer 2027', '2027-06-01T00:00:00-04:00', '2027-09-01T00:00:00-04:00'),
    ('November', '2026-11-01T00:00:00-04:00', '2026-12-01T00:00:00-05:00'),
    ('2027', '2027-01-01T00:00:00-05:00', '2028-01-01T00:00:00-05:00'),
    ('tomorrow', '2026-11-01T00:00:00-04:00', '2026-11-02T00:00:00-05:00'),
])
def test_calendar_windows(query, start, end):
    plan = interpret_query(query, NOW)
    assert plan.start.isoformat() == start
    assert plan.end.isoformat() == end
    assert plan.groups == []


def test_typos_aliases_and_ambiguity():
    plan = interpret_query('CS internshps summer 2027', NOW)
    assert plan.groups == ['cs OR "computer science"', 'internships']
    assert interpret_query('PM mentorship', NOW).groups == ['pm', 'mentorship']
    assert interpret_query('unfamiliarname', NOW).groups == ['unfamiliarname']


@pytest.mark.parametrize('query', ['"CS next week"', 'CS OR robotics', 'robotics -AI'])
def test_explicit_syntax_is_preserved(query):
    plan = interpret_query(query, NOW)
    assert plan.groups == [query]
    assert plan.start is None


def test_opt_out_and_intersection():
    assert interpret_query('internshps next week', NOW, enabled=False).groups == ['internshps next week']
    statement, params = build_search(SearchFilters(query='next week', date_from='2026-11-04T00:00:00Z'), now=NOW)
    assert 'o.starts_at >= %(date_from)s' in statement
    assert 'o.starts_at < %(inferred_before)s' in statement
    assert params['inferred_from'].day == 2


def test_invalid_timezone():
    with pytest.raises(ValueError):
        SearchFilters(timezone='Not/AZone')


def test_date_with_preposition_and_year_rollover():
    assert interpret_query('in November', NOW).groups == []
    plan = interpret_query('next week', datetime.fromisoformat('2026-12-31T12:00:00-05:00'))
    assert plan.start.isoformat() == '2027-01-04T00:00:00-05:00'
    sunday = interpret_query('this weekend', datetime.fromisoformat('2026-11-01T12:00:00-05:00'))
    assert sunday.start.isoformat() == '2026-10-31T00:00:00-04:00'
