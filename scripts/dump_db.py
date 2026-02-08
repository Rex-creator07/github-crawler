"""Dump repository table to CSV and JSON artifacts."""
import os
import sys
import csv
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from db import get_connection


def main():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT repo_id, owner_login, name, full_name, url, stargazer_count, fetched_at "
        "FROM repositories ORDER BY stargazer_count DESC"
    )
    rows = cursor.fetchall()
    cols = [d[0] for d in cursor.description]
    conn.close()

    os.makedirs("artifacts", exist_ok=True)

    # CSV
    csv_path = "artifacts/repositories.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(cols)
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {csv_path}")

    # JSON
    json_path = "artifacts/repositories.json"
    data = [dict(zip(cols, row)) for row in rows]
    for d in data:
        if "fetched_at" in d and d["fetched_at"]:
            d["fetched_at"] = str(d["fetched_at"])
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"Wrote {len(rows)} rows to {json_path}")


if __name__ == "__main__":
    main()
