"""Run the GitHub star crawler and store in DB."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from db import get_connection, upsert_repos
from crawl import crawl_repos


def main():
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("ERROR: GITHUB_TOKEN environment variable required")
        sys.exit(1)
    conn = get_connection()
    total = 0
    try:
        for batch in crawl_repos(token):
            upsert_repos(conn, batch)
            total += len(batch)
            print(f"Crawled {total} repos...")
            if total >= 100_000:
                break
        print(f"Done. Total repos: {total}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
