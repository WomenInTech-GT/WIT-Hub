"""PostgreSQL lexical retrieval and deterministic recommendations."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from search.query import interpret_query

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator, model_validator

class SearchFilters(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query: str = Field(default="", max_length=500)
    interpret: bool = True
    timezone: str = "America/New_York"
    majors: list[str] = Field(default_factory=list, max_length=50)
    academic_years: list[Literal[1, 2, 3, 4]] = Field(default_factory=list)
    opportunity_types: list[str] = Field(default_factory=list, max_length=50)
    content_kinds: list[Literal["opportunity", "event", "program", "resource"]] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list, max_length=50)
    location_modes: list[Literal["online", "in-person", "hybrid", "unknown", "not-applicable"]] = Field(default_factory=list)
    location: str = Field(default="", max_length=200)
    timeline: Literal["start", "deadline"] = "start"
    date_from: AwareDatetime | None = None
    date_to: AwareDatetime | None = None
    include_expired: bool = False
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0, le=100000)

    @field_validator("timezone")
    @classmethod
    def valid_timezone(cls, value):
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError("Use an IANA timezone such as America/New_York") from exc
        return value

    @field_validator("majors", "opportunity_types", "categories")
    @classmethod
    def normalize(cls, values):
        return sorted({value.strip().lower() for value in values if value.strip()})

    @model_validator(mode="after")
    def ordered_dates(self):
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValueError("date_from must be before or equal to date_to")
        return self


class StudentProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")
    majors: list[str] = Field(default_factory=list, max_length=50)
    academic_year: Literal[1, 2, 3, 4] | None = None
    experience_level: Literal["beginner", "intermediate", "advanced"] | None = None
    interests: list[str] = Field(default_factory=list, max_length=50)
    opportunity_types: list[str] = Field(default_factory=list, max_length=50)
    location_modes: list[Literal["online", "in-person", "hybrid"]] = Field(default_factory=list)
    available_from: AwareDatetime | None = None
    available_to: AwareDatetime | None = None

    @field_validator("majors", "interests", "opportunity_types")
    @classmethod
    def normalize(cls, values):
        return SearchFilters.normalize(values)

    @model_validator(mode="after")
    def ordered_dates(self):
        if self.available_from and self.available_to and self.available_from > self.available_to:
            raise ValueError("available_from must be before or equal to available_to")
        return self


class RankingWeights(BaseModel):
    """Server-owned tuning; scores are weighted sums"""
    interests: float = Field(default=3, ge=0, allow_inf_nan=False)
    opportunity_type: float = Field(default=2, ge=0, allow_inf_nan=False)
    location: float = Field(default=1, ge=0, allow_inf_nan=False)


class RecommendationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    profile: StudentProfile
    filters: SearchFilters = Field(default_factory=SearchFilters)


def build_search(filters: SearchFilters, profile: StudentProfile | None = None,
                 weights: RankingWeights | None = None, now: datetime | None = None):
    """Return parameterized SQL. Apply hard constraints before pagination."""
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("now must include a timezone")
    weights = weights or RankingWeights()
    plan = interpret_query(filters.query, now, filters.timezone, filters.interpret)
    params = {"query": filters.query.strip(), "now": now,
              "groups": plan.groups,
              "limit": filters.limit, "offset": filters.offset}
    clauses = []
    if profile is not None or not filters.include_expired:
        clauses.append("""(o.deadline_at IS NULL OR o.deadline_at >= %(now)s)
            AND (o.deadline_date IS NULL OR o.deadline_date >= (%(now)s AT TIME ZONE o.deadline_timezone)::date)
            AND (o.content_kind <> 'event' OR
                (o.schedule_precision = 'date' AND coalesce(o.end_date, o.start_date) >= (%(now)s AT TIME ZONE o.timezone)::date)
                OR (o.schedule_precision = 'time' AND
                    (o.ends_at >= %(now)s OR (o.ends_at IS NULL AND
                     (o.starts_at AT TIME ZONE o.timezone)::date >= (%(now)s AT TIME ZONE o.timezone)::date))))""")
    for field, column in (("majors", "eligible_majors"), ("academic_years", "eligible_years")):
        values = getattr(filters, field)
        if values:
            params[field] = values
            cast = "integer[]" if field == "academic_years" else "text[]"
            clauses.append(f"(cardinality(o.{column}) = 0 OR o.{column} && %({field})s::{cast})")
    for field, column in (("opportunity_types", "opportunity_type"), ("categories", "category"),
                          ("content_kinds", "content_kind"), ("location_modes", "location_mode")):
        if getattr(filters, field):
            params[field] = getattr(filters, field)
            clauses.append(f"o.{column} = ANY(%({field})s)")
    if filters.location.strip():
        params["location"] = filters.location.strip()
        clauses.append("strpos(lower(o.location_name), lower(%(location)s)) > 0")
    date_column, date_only, date_zone = {
        "start": ("starts_at", "start_date", "timezone"),
        "deadline": ("deadline_at", "deadline_date", "deadline_timezone"),
    }[filters.timeline]
    for field, operator in (("date_from", ">="), ("date_to", "<=")):
        if getattr(filters, field):
            params[field] = getattr(filters, field)
            clauses.append(f"(o.{date_column} {operator} %({field})s OR o.{date_only} {operator} (%({field})s AT TIME ZONE o.{date_zone})::date)")
    if plan.start:
        params.update(inferred_from=plan.start, inferred_before=plan.end)
        params.update(inferred_date_from=plan.start.date(), inferred_date_before=plan.end.date())
        clauses.append("""((o.starts_at >= %(inferred_from)s AND o.starts_at < %(inferred_before)s)
            OR (o.start_date >= %(inferred_date_from)s AND o.start_date < %(inferred_date_before)s))""")
    if plan.groups:
        clauses.append("o.search_vector @@ q.term")
    score = "0.0"
    if profile is not None:
        # Unparsed prose and unknown requirements cannot establish eligibility.
        clauses.append("o.eligibility_status <> 'unknown' AND cardinality(o.eligibility) = 0")
        params.update(student_majors=profile.majors,
                      student_years=[] if profile.academic_year is None else [profile.academic_year],
                      student_levels=[] if profile.experience_level is None else [profile.experience_level],
                      interests=profile.interests, preferred_types=profile.opportunity_types,
                      preferred_modes=profile.location_modes,
                      interest_weight=weights.interests, type_weight=weights.opportunity_type,
                      location_weight=weights.location)
        for column, key, cast in (("eligible_majors", "student_majors", "text[]"),
                                  ("eligible_years", "student_years", "integer[]"),
                                  ("experience_levels", "student_levels", "text[]")):
            clauses.append(f"(cardinality(o.{column}) = 0 OR o.{column} && %({key})s::{cast})")
        # Require a known schedule contained in the availability window.
        if profile.available_from:
            params["available_from"] = profile.available_from
            clauses.append("o.starts_at >= %(available_from)s")
        if profile.available_to:
            params["available_to"] = profile.available_to
            clauses.append("o.starts_at IS NOT NULL AND o.ends_at <= %(available_to)s")
        score = """%(interest_weight)s * (
            SELECT count(DISTINCT tag)::float FROM unnest(o.tags) AS tag
            WHERE tag = ANY(%(interests)s::text[])
        ) / greatest(cardinality(%(interests)s::text[]), 1)
        + %(type_weight)s * CASE WHEN o.opportunity_type = ANY(%(preferred_types)s::text[]) THEN 1 ELSE 0 END
        + %(location_weight)s * CASE WHEN o.location_mode = ANY(%(preferred_modes)s::text[]) THEN 1 ELSE 0 END"""
    where = " AND ".join(clauses) or "TRUE"
    sql = f"""
        WITH terms AS (
            SELECT websearch_to_tsquery('english', value) AS term
            FROM unnest(%(groups)s::text[]) AS value
        ), q AS (
            SELECT coalesce(string_agg('(' || term::text || ')', ' & ')
                   FILTER (WHERE numnode(term) > 0), '')::tsquery AS term FROM terms
        )
        SELECT o.*,
               ts_rank_cd(o.search_vector, q.term, 32) AS lexical_score,
               ({score}) AS match_score
        FROM (SELECT c.*, c.url AS source_url, c.category AS opportunity_type,
                     coalesce(c.location, '') AS location_name,
                     c.deadline_at AS application_deadline
              FROM catalog.content_items c) o CROSS JOIN q WHERE {where}
        ORDER BY match_score DESC, lexical_score DESC,
                 coalesce(o.deadline_at, (o.deadline_date + 1)::timestamp AT TIME ZONE o.deadline_timezone) ASC NULLS LAST, o.id ASC
        LIMIT %(limit)s OFFSET %(offset)s
    """
    return sql, params


def explain_match(row: dict, profile: StudentProfile) -> list[str]:
    reasons = []
    shared = sorted(set(row["tags"]) & set(profile.interests))
    if shared:
        reasons.append("Matches your interests: " + ", ".join(shared))
    if row["opportunity_type"] in profile.opportunity_types:
        reasons.append("Preferred opportunity type: " + row["opportunity_type"])
    if row["location_mode"] in profile.location_modes:
        reasons.append("Preferred location format: " + row["location_mode"])
    return reasons or ["Passes the eligibility and deadline filters; no preference overlap."]


def search_opportunities(connection, filters: SearchFilters,
                         profile: StudentProfile | None = None,
                         weights: RankingWeights | None = None,
                         now: datetime | None = None) -> list[dict]:
    from psycopg.rows import dict_row

    sql, params = build_search(filters, profile, weights, now)
    with connection.cursor(row_factory=dict_row) as cursor:
        cursor.execute(sql, params)
        rows = cursor.fetchall()
    for row in rows:
        row.pop("search_vector", None)
        row["explanations"] = explain_match(row, profile) if profile is not None else []
    return rows


def search_documents(query: str, limit: int = 5, *, connection=None):
    """Compatibility entry point; callers now supply a PostgreSQL connection."""
    if connection is None:
        raise ValueError("A PostgreSQL connection is required")
    return search_opportunities(connection, SearchFilters(query=query, limit=limit))
