# Scaling to 500 Million Repositories

If this crawler were extended to collect data on **500 million** repositories instead of 100,000, here is what would change:

## 1. **API Strategy**

| Current (100k) | At 500M scale |
|----------------|---------------|
| Single-process GraphQL search | **Distributed crawling** with multiple tokens (GitHub Apps, multiple PATs) |
| Sequential pagination | **Parallel workers** across different search slices |
| 1,000 points/hour (GITHUB_TOKEN) | **Rate limit pooling** – 5,000 pts/hr per user × N tokens |

## 2. **Data Storage**

| Current | At 500M scale |
|---------|---------------|
| Single Postgres instance | **Sharded DB** (e.g. by repo_id hash) or **data warehouse** (BigQuery, Snowflake) |
| Upserts in one DB | **Batch writes** to partitioned tables, append-only where possible |
| Local disk | **Object storage** (S3/GCS) for raw dumps, Parquet for analytics |

## 3. **Computation**

| Current | At 500M scale |
|---------|---------------|
| Single script | **Orchestrated jobs** (Airflow, Prefect, Kubernetes Jobs) |
| In-memory deduplication | **Distributed deduplication** (e.g. Bloom filters, Redis) |
| One crawl run | **Incremental/streaming** – only fetch changed repos |

## 4. **Rate Limits & Throughput**

- 500M repos ≈ 5M API calls (100 repos/call)
- At 5,000 pts/hr/token: ~1,000 tokens needed for a 1-hour run
- Use **GitHub Archive** or **Google BigQuery GitHub dataset** for historical bulk data where possible
- Integrate **webhooks** for real-time updates instead of full re-crawls

## 5. **Monitoring & Reliability**

- **Checkpointing** – save progress so failures don’t restart from zero
- **Rate limit monitoring** – track remaining points, back off before hitting limits
- **Idempotency** – safe retries without double-counting
