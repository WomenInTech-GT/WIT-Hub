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


@pytest.mark.parametrize('query,groups,note', [
    ('AI', ['ai OR "artificial intelligence"'], 'Expanded ai to artificial intelligence'),
    ('ML', ['ml OR "machine learning"'], 'Expanded ml to machine learning'),
    ('WIT', ['wit OR "women in tech"'], 'Expanded wit to women in tech'),
    ('internsip', ['internship'], 'Corrected internsip to internship'),
    ('scholorships', ['scholarships'], 'Corrected scholorships to scholarships'),
    ('hackaton', ['hackathon'], 'Corrected hackaton to hackathon'),
])
def test_vocabulary_expansions_are_explained(query, groups, note):
    plan = interpret_query(query, NOW)
    assert plan.as_dict() == {
        'lexical_groups': groups, 'notes': [note],
        'starts_at_from': None, 'starts_at_before': None,
    }


@pytest.mark.parametrize('query,groups', [
    ('', []), (' \t\n ', []), (' !!! ', ['!!!']),
    ('  Robotics, DATA-science!  ', ['robotics', 'data-science']),
    ('PM unfamiliarname', ['pm', 'unfamiliarname']),
    ('mentoring for beginners', ['mentoring', 'for', 'beginners']),
])
def test_plain_text_normalization_preserves_unknown_terms(query, groups):
    plan = interpret_query(query, NOW)
    assert plan.groups == groups
    assert plan.notes == []
    assert plan.start is None and plan.end is None


@pytest.mark.parametrize('query', [
    '  "AI tomorrow"  ', 'CS or ML next week', '-AI tomorrow',
    'robotics -internshps summer 2027',
])
def test_explicit_syntax_bypasses_all_interpretation(query):
    assert interpret_query(query, NOW).as_dict() == {
        'lexical_groups': [query.strip()], 'notes': [],
        'starts_at_from': None, 'starts_at_before': None,
    }


@pytest.mark.parametrize('query', ['  AI internshps tomorrow  ', '!!!', '  '])
def test_opt_out_bypasses_dates_corrections_and_aliases(query):
    assert interpret_query(query, NOW, enabled=False).as_dict() == {
        'lexical_groups': [query.strip()] if query.strip() else [], 'notes': [],
        'starts_at_from': None, 'starts_at_before': None,
    }


@pytest.mark.parametrize('query,now,zone,start,end', [
    ('today', '2026-11-01T02:30:00+00:00', 'America/New_York',
     '2026-10-31T00:00:00-04:00', '2026-11-01T00:00:00-04:00'),
    ('today', '2026-11-01T02:30:00+00:00', 'Asia/Tokyo',
     '2026-11-01T00:00:00+09:00', '2026-11-02T00:00:00+09:00'),
    ('today', '2026-03-08T12:00:00+00:00', 'America/New_York',
     '2026-03-08T00:00:00-05:00', '2026-03-09T00:00:00-04:00'),
    ('next week', '2026-11-02T12:00:00-05:00', 'America/New_York',
     '2026-11-09T00:00:00-05:00', '2026-11-16T00:00:00-05:00'),
    ('February 2028', '2026-10-31T12:00:00-04:00', 'America/New_York',
     '2028-02-01T00:00:00-05:00', '2028-03-01T00:00:00-05:00'),
    ('December 2026', '2026-10-31T12:00:00-04:00', 'America/New_York',
     '2026-12-01T00:00:00-05:00', '2027-01-01T00:00:00-05:00'),
    ('summer', '2026-10-31T12:00:00-04:00', 'America/New_York',
     '2026-06-01T00:00:00-04:00', '2026-09-01T00:00:00-04:00'),
])
def test_calendar_edge_cases(query, now, zone, start, end):
    assert interpret_query(query, datetime.fromisoformat(now), zone).as_dict() == {
        'lexical_groups': [],
        'notes': [f'{query} interpreted as a start-date window in {zone}'],
        'starts_at_from': start, 'starts_at_before': end,
    }


def test_dates_remove_filler_but_keep_required_search_terms():
    plan = interpret_query('AI workshops happening during the summer 2027', NOW)
    assert plan.groups == ['ai OR "artificial intelligence"', 'workshops']
    assert plan.start.isoformat() == '2027-06-01T00:00:00-04:00'
    assert plan.end.isoformat() == '2027-09-01T00:00:00-04:00'


@pytest.mark.parametrize('enabled', [True, False])
def test_naive_evaluation_time_is_rejected(enabled):
    with pytest.raises(ValueError, match='now must include a timezone'):
        interpret_query('today', datetime(2026, 10, 31), enabled=enabled)
