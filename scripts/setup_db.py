"""Create PostgreSQL schema - used by GitHub Actions and locally."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from db import get_connection, run_schema


def main():
    conn = get_connection()
    try:
        run_schema(conn)
        print("Schema created successfully.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
