# Search and quiz matching

Run from the repository root with Python 3.10+ and PostgreSQL 14+:

```powershell
uv venv
uv pip install -r backend/requirements.txt
$env:DATABASE_URL = 'postgresql://USER:PASSWORD@localhost:5432/wit_hub'
psql $env:DATABASE_URL -v ON_ERROR_STOP=1 -f backend/migrations/001_opportunities.sql
uv run uvicorn backend.app.main:app --reload
```

The migration is applied **once** to a new database, never automatically at server startup.
Populate `opportunities` from verified catalog records; there are no pretend production results.
The insert/update trigger maintains a weighted, GIN-indexed full-text vector (title, then
tags/type, then description/location). See `/docs` for the interactive API.

## Directory search

`POST /api/search` accepts JSON:

```json
{
  "query": "WIT \"coding projects\"",
  "majors": ["computer science"],
  "academic_years": [1, 2],
  "opportunity_types": ["workshop", "hackathon"],
  "location_modes": ["online"],
  "location": "Zoom",
  "timeline": "deadline",
  "date_from": "2026-11-01T00:00:00-05:00",
  "date_to": "2026-12-01T00:00:00-05:00",
  "limit": 20,
  "offset": 0
}
```

All fields are optional. Blank queries browse the catalog. Nonblank queries use PostgreSQL
`websearch_to_tsquery` (quoted phrases, OR, and exclusions) and `ts_rank_cd`; stopword-only
or punctuation-only queries return no lexical matches. There is no semantic matching or LLM.

Selections within a filter use OR; different filters use AND. Major/year filters include
unrestricted opportunities. Year `4` means **4+ year**. Use consistent full major names;
aliases such as CS are not expanded automatically. Location name is a case-insensitive,
literal substring (street, venue, Zoom). Mode is `online` or `in-person`.

Date ranges are inclusive and target `starts_at` or `application_deadline`. Supply timestamps
with UTC offsets, including the desired time of day. Date-only UI inputs should be converted
to the appropriate local day boundaries. Null dates do not satisfy a date range.

Deadlines strictly before the current instant are hidden. Null deadlines mean **no application
deadline**, not an unverified deadline. Directory callers may set `include_expired: true`.
This rule does not automatically hide past events with no application deadline.

## Find Something for Me

`POST /api/recommendations`:

```json
{
  "profile": {
    "majors": ["computer science"],
    "academic_year": 1,
    "experience_level": "beginner",
    "interests": ["coding", "web development"],
    "opportunity_types": ["project", "workshop"],
    "location_modes": ["online"],
    "available_from": "2026-11-01T00:00:00-05:00",
    "available_to": "2026-12-01T00:00:00-05:00"
  },
  "filters": {"limit": 20}
}
```

Quiz mapping: topics -> interests; desired opportunities -> opportunity_types;
experience/year -> eligibility; availability -> an explicit timestamp window; location
preference -> location_modes. Also collect major for restricted opportunities. Recurring
weekly availability is not modeled in this MVP.

Recommendations always exclude expired deadlines, even if `include_expired` is true.
Empty catalog eligibility arrays mean unrestricted. Missing quiz eligibility answers only
allow unrestricted records for that dimension. Availability requires a known start at/after
the lower bound and a known end at/before the upper bound when provided. Type and location
preferences boost scores; use `filters` to make them mandatory.

Score = 3 × fraction of selected interests matching tags + 2 × preferred type match
+ 1 × preferred location mode match. Tune server-side `RankingWeights` when calling
`search_opportunities`. All eligible records are scored **before** limit/offset. Ties sort
by lexical score, earliest deadline (null last), then ID. Explanations list actual overlaps;
zero-overlap results are labeled as such. Responses contain `items`, `limit`, and `offset`,
with catalog facts, source URL, lexical/match scores, and explanations per item.

## Verification and future hybrid retrieval

Run the 20 user-supplied exploratory searches against your populated catalog:

```powershell
uv run --with-requirements backend/requirements.txt python -m search.run_test_queries
```

The runner uses `DATABASE_URL`, read-only transactions, and the normal default deadline
filter. It prints actual results as JSON and exits unsuccessfully if the database is
unconfigured or a query fails. Queries are preserved in `search/test_queries.json`.
This is an exploratory report, not a relevance pass/fail test: expected records require
a curated catalog. Relative dates, acronym expansion, and typo correction are not
implemented; these inputs are sent unchanged to lexical search.

```powershell
uv run --with-requirements backend/requirements.txt --with pytest --with httpx python -m pytest -q
# Enable real SQL tests using a test database where you can create schemas:
$env:TEST_DATABASE_URL = 'postgresql://USER:PASSWORD@localhost:5432/wit_hub_test'
uv run --with-requirements backend/requirements.txt --with pytest --with httpx python -m pytest -q
```

PostgreSQL tests use unique schemas and roll back their changes. Without TEST_DATABASE_URL,
they are explicitly skipped; unit/API tests alone do not validate database execution.

Future pgvector retrieval should reuse the same hard eligibility/deadline constraints on
both candidate lists, then fuse their ranks using RRF before final pagination. Current
`lexical_score` is a retrieval score, separate from quiz preference `match_score`.

PostgreSQL reference: https://www.postgresql.org/docs/current/textsearch-controls.html
