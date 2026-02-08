-- Flexible schema for GitHub repositories
-- Uses repo_id as primary key for efficient upserts (ON CONFLICT)

CREATE TABLE IF NOT EXISTS repositories (
    repo_id          VARCHAR(50) PRIMARY KEY,
    owner_login      VARCHAR(255) NOT NULL,
    name             VARCHAR(255) NOT NULL,
    full_name        VARCHAR(500) NOT NULL,
    url              TEXT NOT NULL,
    stargazer_count  INTEGER NOT NULL DEFAULT 0,
    fetched_at       TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index for efficient star-based queries and daily updates
CREATE INDEX IF NOT EXISTS idx_repos_stars ON repositories(stargazer_count DESC);
CREATE INDEX IF NOT EXISTS idx_repos_fetched ON repositories(fetched_at);

-- Upsert: update only changed rows, minimal write amplification
COMMENT ON TABLE repositories IS 'Flexible schema - add columns for issues, PRs, etc. as needed';
