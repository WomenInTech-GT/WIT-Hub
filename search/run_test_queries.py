"""Run the user's exact queries against the configured catalog, without writes.

From the repository root: uv run --with-requirements backend/requirements.txt
python -m search.run_test_queries
"""
import json
import os
from pathlib import Path
import sys
from datetime import datetime, timezone
from search.query import interpret_query

import psycopg

from search.service import SearchFilters, search_opportunities


def main():
    queries = json.loads(Path(__file__).with_name("test_queries.json").read_text(encoding="utf-8"))
    url = os.environ.get("DATABASE_URL")
    if not url:
        print(json.dumps({"status": "blocked", "reason": "DATABASE_URL is not configured",
                          "executed": 0, "queries": queries}, indent=2))
        return 1
    results = []
    now = datetime.now(timezone.utc)
    try:
        with psycopg.connect(url, connect_timeout=5) as connection:
            connection.execute("SET TRANSACTION READ ONLY")
            connection.execute("SET LOCAL statement_timeout = '10s'")
            count_row = connection.execute("SELECT count(*) FROM catalog.content_items").fetchone()
            assert count_row is not None
            count = count_row[0]
            for query in queries:
                items = search_opportunities(connection, SearchFilters(query=query), now=now)
                results.append({"query": query, "returned_count": len(items), "items": items,
                                "interpretation": interpret_query(query, now).as_dict()})
        print(json.dumps({"status": "completed", "catalog_count": count,
                          "executed": len(results), "limit_per_query": 20, "evaluated_at": now.isoformat(),
                          "results": results}, indent=2, default=str))
        return 0
    except psycopg.Error:
        # Avoid exposing credentials or server details in a shared report.
        print(json.dumps({"status": "blocked", "reason": "Database query failed; check connectivity and migration",
                          "executed": len(results), "results": results}, indent=2, default=str))
        return 1


if __name__ == "__main__":
    sys.exit(main())
