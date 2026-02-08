"""Database layer - separation of concerns, anti-corruption."""
import os
import psycopg2
from psycopg2.extras import execute_values
from typing import List, Tuple
from dataclasses import dataclass


@dataclass(frozen=True)
class RepoRecord:
    """Immutable repository record."""
    repo_id: str
    owner_login: str
    name: str
    full_name: str
    url: str
    stargazer_count: int


def get_connection():
    """Get DB connection from env."""
    return psycopg2.connect(
        host=os.environ.get("PGHOST", "localhost"),
        port=os.environ.get("PGPORT", "5432"),
        dbname=os.environ.get("PGDATABASE", "github"),
        user=os.environ.get("PGUSER", "postgres"),
        password=os.environ.get("PGPASSWORD", "postgres"),
    )


def run_schema(conn) -> None:
    """Create tables from schema.sql."""
    with open(os.path.join(os.path.dirname(__file__), "schema.sql")) as f:
        schema_sql = f.read()
    cursor = conn.cursor()
    for stmt in schema_sql.split(";"):
        stmt = stmt.strip()
        if stmt and not stmt.startswith("--"):
            cursor.execute(stmt)
    conn.commit()


def upsert_repos(conn, repos: List[RepoRecord]) -> int:
    """Upsert repos - efficient, minimal rows affected."""
    if not repos:
        return 0
    rows = [
        (r.repo_id, r.owner_login, r.name, r.full_name, r.url, r.stargazer_count)
        for r in repos
    ]
    cursor = conn.cursor()
    execute_values(
        cursor,
        """
        INSERT INTO repositories (repo_id, owner_login, name, full_name, url, stargazer_count)
        VALUES %s
        ON CONFLICT (repo_id) DO UPDATE SET
            stargazer_count = EXCLUDED.stargazer_count,
            fetched_at = CURRENT_TIMESTAMP
        """,
        rows,
    )
    conn.commit()
    return len(rows)
