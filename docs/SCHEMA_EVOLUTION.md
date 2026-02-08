# Schema Evolution for Future Metadata

How the schema can evolve to support additional metadata (issues, PRs, commits, comments, reviews, CI checks) while keeping updates **efficient** and **minimal rows affected**.

## Design Principles

1. **Separate tables** – one table per entity type
2. **Foreign keys** – link to parent entities (e.g. `repo_id`, `pr_id`)
3. **Upsert by primary key** – update only changed rows
4. **Timestamp columns** – track when each row was last updated

## Proposed Schema Extension

```sql
-- Repositories (existing - minimal changes)
ALTER TABLE repositories ADD COLUMN IF NOT EXISTS issues_count INTEGER;
ALTER TABLE repositories ADD COLUMN IF NOT EXISTS prs_count INTEGER;

-- Issues: one row per issue, keyed by issue_id
CREATE TABLE issues (
    issue_id VARCHAR(50) PRIMARY KEY,
    repo_id VARCHAR(50) REFERENCES repositories(repo_id),
    number INTEGER,
    state VARCHAR(20),
    comments_count INTEGER,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Pull Requests: one row per PR
CREATE TABLE pull_requests (
    pr_id VARCHAR(50) PRIMARY KEY,
    repo_id VARCHAR(50) REFERENCES repositories(repo_id),
    number INTEGER,
    state VARCHAR(20),
    commits_count INTEGER,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Comments: one row per comment (PR or issue)
CREATE TABLE comments (
    comment_id VARCHAR(50) PRIMARY KEY,
    parent_type VARCHAR(20),  -- 'issue' | 'pull_request'
    parent_id VARCHAR(50),
    body TEXT,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- PR Reviews: one row per review
CREATE TABLE pr_reviews (
    review_id VARCHAR(50) PRIMARY KEY,
    pr_id VARCHAR(50) REFERENCES pull_requests(pr_id),
    state VARCHAR(20),
    submitted_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- CI Checks: one row per check run
CREATE TABLE ci_checks (
    check_id VARCHAR(50) PRIMARY KEY,
    pr_id VARCHAR(50),
    name VARCHAR(255),
    conclusion VARCHAR(50),
    completed_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

## Why This Keeps Updates Efficient

| Scenario | Impact |
|----------|--------|
| PR gets 10 → 20 comments | Only **insert** 10 new rows in `comments`; no updates to existing rows |
| Issue closed | **1 row** updated in `issues` |
| New CI check run | **1 row** inserted in `ci_checks` |
| Repo star count changes | **1 row** updated in `repositories` (existing) |

**Minimal rows affected** because:

- Each entity has its own table and primary key
- Comments, reviews, and checks are append-heavy (inserts)
- Updates are confined to the specific row that changed
- No nested JSON that would require full-document rewrites

## Indexes for Query Performance

```sql
CREATE INDEX idx_issues_repo ON issues(repo_id);
CREATE INDEX idx_prs_repo ON pull_requests(repo_id);
CREATE INDEX idx_comments_parent ON comments(parent_type, parent_id);
CREATE INDEX idx_reviews_pr ON pr_reviews(pr_id);
```
