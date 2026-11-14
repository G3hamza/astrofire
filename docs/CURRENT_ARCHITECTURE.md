# Architecture (as built, 13 Nov 2026)

```
NASA PSI (psi.nasa.gov, CC0)      NASA NTRS (ntrs.nasa.gov)
        │  mirror + SHA-256 check         │  NTRS API via Chrome
        ▼                                  ▼
BRONZE  data/raw/            (immutable; data/manifests/bronze_manifest.csv = sha256, url, size, time)
        │  pipelines/ingestion/manifest.py
        ▼
SILVER  data/silver/investigations/<one table per investigation>
        data/silver/materials/  materials · material_samples · material_properties
        data/silver/measurements/measurements.csv   (long: quantity, value, unit, status, source)
        data/silver/reference/partial_gravity_limits.csv (copied from data/curated/, hand-transcribed from a cited NTRS paper)
        │  pipelines/transformation/silver.py   ──►  data/quarantine/quarantine.csv
        ▼
GOLD    data/gold/analytics/  solid_fire_tests · droplet_extinction_tests · gas_jet_flame_conditions ·
                              smoke_generation_tests · partial_gravity_limits · mission_coverage
        data/gold/powerbi/    investigation_overview · material_overview · outcome_summary · data_quality_overview · kpis
        data/gold/ml/         solid_outcome_features (+ README: not validated)
        data/gold/rag/        documents.jsonl · chunks.jsonl
        │  pipelines/transformation/gold.py, rag.py
        ▼
VALIDATE pipelines/validation/validate.py → schemas/*.json, DATA_QUALITY_REPORT, PROVENANCE_REPORT (exit 1 on error)
        ▼
CONSUMERS  backend/ (FastAPI reads Gold only) · Power BI (gold/powerbi, CSV or Parquet) · RAG (gold/rag) · Kaggle (data/processed, legacy export)
```

Differences from the conceptual target:
- Bronze stays at `data/raw/` (not moved to `data/bronze/`) so existing links, docs and verification hashes keep working. `pipelines/common.py` names it `BRONZE`.
- Storage = CSV (source of truth) + Parquet copies. No Iceberg/MinIO/Snowflake: see TARGET_ARCHITECTURE.md.
- `data/processed/` is kept as a **legacy export** regenerated from Gold, for the Kaggle notebook. The backend no longer reads it.
- Orchestration is a single Python runner (`pipelines/orchestration/run_all.py`), logged to `data/manifests/pipeline_runs.jsonl`.
