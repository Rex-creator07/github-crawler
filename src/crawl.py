"""GitHub GraphQL crawler - rate-limited, retry-aware."""
import os
import time
import requests
from typing import List, Optional, Generator
from dataclasses import dataclass

from db import RepoRecord


GRAPHQL_URL = "https://api.github.com/graphql"
TARGET_REPOS = 100_000
PAGE_SIZE = 100
RATE_LIMIT_BUFFER = 50  # Stop before hitting limit


@dataclass
class RateLimit:
    remaining: int
    reset_at: float


def get_token() -> str:
    """Get token from env (GITHUB_TOKEN in Actions)."""
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        raise ValueError("GITHUB_TOKEN environment variable required")
    return token


def _parse_rate_limit(resp: requests.Response) -> RateLimit:
    """Parse rate limit headers."""
    remaining = int(resp.headers.get("x-ratelimit-remaining", 0))
    reset = float(resp.headers.get("x-ratelimit-reset", time.time() + 3600))
    return RateLimit(remaining=remaining, reset_at=reset)


def _search_query(search_term: str, cursor: Optional[str] = None) -> str:
    """Build GraphQL search query - minimal fields for speed."""
    after = f', after: "{cursor}"' if cursor else ""
    return """
    query {
      search(query: "%s", type: REPOSITORY, first: %d%s) {
        repositoryCount
        edges {
          cursor
          node {
            ... on Repository {
              id
              nameWithOwner
              url
              stargazerCount
            }
          }
        }
        pageInfo {
          hasNextPage
          endCursor
        }
      }
      rateLimit {
        remaining
        resetAt
      }
    }
    """ % (search_term.replace('"', '\\"'), PAGE_SIZE, after)


def _parse_repos(data: dict) -> List[RepoRecord]:
    """Extract repos from GraphQL response (anti-corruption)."""
    repos = []
    try:
        edges = data.get("data", {}).get("search", {}).get("edges", [])
        for edge in edges:
            node = edge.get("node") or {}
            repo_id = node.get("id") or ""
            if not repo_id:
                continue
            name_with_owner = node.get("nameWithOwner") or ""
            parts = name_with_owner.split("/", 1)
            owner = parts[0] if len(parts) > 1 else ""
            name = parts[1] if len(parts) > 1 else name_with_owner
            repos.append(RepoRecord(
                repo_id=repo_id,
                owner_login=owner,
                name=name,
                full_name=name_with_owner,
                url=node.get("url") or "",
                stargazer_count=int(node.get("stargazerCount") or 0),
            ))
    except (KeyError, TypeError, ValueError):
        pass
    return repos


def _fetch_page(token: str, search_term: str, cursor: Optional[str]) -> tuple[dict, Optional[str], RateLimit]:
    """Fetch one page, return (data, next_cursor, rate_limit)."""
    query = _search_query(search_term, cursor)
    resp = requests.post(
        GRAPHQL_URL,
        json={"query": query},
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        timeout=30,
    )
    rate = _parse_rate_limit(resp)
    resp.raise_for_status()
    data = resp.json()
    if "errors" in data:
        raise RuntimeError(f"GraphQL errors: {data['errors']}")
    search = data.get("data", {}).get("search", {})
    page_info = search.get("pageInfo", {})
    next_cursor = page_info.get("endCursor") if page_info.get("hasNextPage") else None
    return data, next_cursor, rate


def _search_terms() -> Generator[str, None, None]:
    """Generate search terms to cover 100k repos (search limited to 1000/query)."""
    # Each search returns max 1000 results; need 100+ unique searches
    languages = ["Python", "JavaScript", "Java", "Go", "TypeScript", "C#", "PHP", "C++", "Ruby", "Rust"]
    star_ranges = [">10000", ">5000", ">1000", ">500", ">100", ">50", ">10", ">1", ">=0"]
    for lang in languages:
        for stars in star_ranges:
            yield f"stars:{stars} language:{lang}"
    # Fallback generic searches
    for i in range(20):
        yield f"stars:>{(i+1)*10}"


def crawl_repos(token: Optional[str] = None) -> Generator[List[RepoRecord], None, None]:
    """
    Crawl repos respecting rate limits. Yields batches of RepoRecord.
    Stops when remaining points < RATE_LIMIT_BUFFER or target reached.
    """
    token = token or get_token()
    seen_ids = set()
    collected = 0

    for search_term in _search_terms():
        if collected >= TARGET_REPOS:
            break
        cursor = None
        while True:
            try:
                data, next_cursor, rate = _fetch_page(token, search_term, cursor)
                repos = _parse_repos(data)
                # Deduplicate
                batch = [r for r in repos if r.repo_id not in seen_ids]
                for r in batch:
                    seen_ids.add(r.repo_id)
                collected += len(batch)
                if batch:
                    yield batch
                if rate.remaining < RATE_LIMIT_BUFFER:
                    wait = max(0, rate.reset_at - time.time()) + 5
                    if wait > 0:
                        time.sleep(min(wait, 60))
                if not next_cursor or collected >= TARGET_REPOS:
                    break
                cursor = next_cursor
                time.sleep(0.5)  # Avoid secondary rate limits
            except requests.exceptions.HTTPError as e:
                if e.response and e.response.status_code == 403:
                    retry_after = e.response.headers.get("Retry-After")
                    wait = int(retry_after) if retry_after else 60
                    time.sleep(wait)
                else:
                    raise
            except requests.exceptions.RequestException:
                time.sleep(5)  # Retry after transient failure
