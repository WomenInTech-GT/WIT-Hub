import os
from datetime import datetime, timezone
from search.query import interpret_query

import psycopg
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from search.service import RecommendationRequest, SearchFilters, search_opportunities

app = FastAPI(title="WIT-Hub API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def healthcheck():
    return {"status": "ok", "service": "backend"}


@app.get("/api")
def api_root():
    return {
        "message": "Welcome to WIT-Hub",
        "services": ["backend", "search"],
    }


def run_search(filters: SearchFilters, profile=None):
    now = datetime.now(timezone.utc)
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise HTTPException(status_code=503, detail="Search database is not configured")
    try:
        with psycopg.connect(database_url, connect_timeout=5) as connection:
            connection.execute("SET LOCAL statement_timeout = '5s'")
            items = search_opportunities(connection, filters, profile, now=now)
    except psycopg.OperationalError as exc:
        raise HTTPException(status_code=503, detail="Search database is unavailable") from exc
    return {"items": items, "limit": filters.limit, "offset": filters.offset,
            "interpretation": interpret_query(filters.query, now, filters.timezone, filters.interpret).as_dict()}


@app.post("/api/search")
def search(filters: SearchFilters):
    return run_search(filters)


@app.post("/api/recommendations")
def recommendations(request: RecommendationRequest):
    return run_search(request.filters, request.profile)
