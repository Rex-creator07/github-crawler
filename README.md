# GitHub Repositories Star Crawler

A technical assessment for Sofstica Solutions - crawls 100,000 GitHub repositories with star counts using the GraphQL API and stores them in PostgreSQL.

## Structure

```
github-crawler/
├── .github/workflows/     # CI/CD pipeline
├── src/
│   ├── crawl.py          # Main crawler logic
│   ├── db.py             # Database operations
│   └── schema.sql        # PostgreSQL schema
├── scripts/
│   ├── setup_db.py       # Create tables
│   └── dump_db.py        # Export to CSV/JSON
├── docs/
│   ├── SCALING_500M.md   # 500M repo considerations
│   └── SCHEMA_EVOLUTION.md # Future metadata schema
└── requirements.txt
```

## Quick Start

1. **Setup**: `pip install -r requirements.txt`
2. **Database**: Run `scripts/setup_db.py` to create schema
3. **Crawl**: Run `scripts/run_crawl.py` (requires `GITHUB_TOKEN` env var)
4. **Dump**: Run `scripts/dump_db.py` to export data

## GitHub Actions

The pipeline runs automatically on push:
- Starts PostgreSQL service container
- Sets up schema
- Crawls 100,000 repos (uses default `GITHUB_TOKEN`)
- Exports DB as CSV artifact

## Documentation

- [Scaling to 500M Repositories](docs/SCALING_500M.md)
- [Schema Evolution for Future Metadata](docs/SCHEMA_EVOLUTION.md)
