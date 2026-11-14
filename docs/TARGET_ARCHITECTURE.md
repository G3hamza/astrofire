# Target Architecture and Storage Decision

## Decision for the hackathon (implemented)

| Need | Choice | Why |
|---|---|---|
| Table format | **CSV + Parquet** | Data is ~20 MB. CSV is diff-able in Git and readable by every teammate; Parquet gives typed fast reads for Power BI/pandas. |
| Object storage | **Git repo / local disk** | No multi-writer or TB-scale need. |
| Orchestration | Python runner + GitHub Actions | Reproducible in one command; CI re-runs it. |
| Search | In-process BM25 | No server; works offline. |

## Evaluated, NOT implemented (do not claim these exist)

| Technology | Verdict | When it becomes worth it |
|---|---|---|
| Apache Iceberg | Not implemented. CSV/Parquet files here are **not** Iceberg tables. | If raw image/video data (PSI is ~13 TB) or many concurrent writers are added. Plan: Parquet files → Iceberg tables via PyIceberg with a SQL catalog; Bronze/Silver/Gold as namespaces. |
| MinIO / S3 | Not implemented. | Same trigger; would hold Bronze binaries + Iceberg data files. |
| Snowflake | Not recommended. | Paid, and 20 MB of data doesn't need a warehouse. Power BI reads the Parquet directly. |
| Vector DB / embeddings | Not implemented. | When BM25 recall is shown to be insufficient on a test question set. Interface: embed `gold/rag/chunks.jsonl` `text`, keep `chunk_id` as key, return the same JSON fields. |
| Prometheus / Grafana / cAdvisor | Not implemented. | When the API is deployed as a long-running service. Only `docker-compose.yml` with the API exists (not tested here; Docker daemon unavailable in the build environment). |
| PostgreSQL | Not needed. | The model in DATA_MODEL.md is database-ready (PK/FK defined) if a multi-user write path appears. |
