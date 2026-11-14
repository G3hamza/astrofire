# Pipeline Guide (reproducible execution)

## Run everything
```bash
pip install -r requirements.txt
python -m pipelines.orchestration.run_all     # Bronze manifest → Silver → Gold → RAG → validate → data dictionary
pytest -q                                     # data rules + API tests
uvicorn backend.app:app --reload              # API at http://127.0.0.1:8000/docs
```
Validation only: `python -m pipelines.orchestration.run_all --check`. Exit code 1 = failed; read `docs/DATA_QUALITY_REPORT.md`.

## What runs automatically vs manually
| Automatic (GitHub Actions `.github/workflows/ci.yml`, every push/PR) | Manual |
|---|---|
| structure check, `compileall`, full pipeline, validation, pytest, reproducibility diff, quality report artifact | downloading new NASA files; refreshing Power BI; Docker build (untested here) |

## Add a new source file to an existing investigation
1. Put it under `data/raw/psi/<PSI-xx_NAME>/...` (never edit existing raw files).
2. Run the pipeline: the manifest records its SHA-256 and URL.
3. If it is a new experiment table, extend that investigation's `silver_*` function in `pipelines/transformation/silver.py`.

## Add a new NASA investigation
1. Download its folder to `data/raw/psi/PSI-xx_NAME/` (`investigation.json` + `Experimental table/*.csv`).
2. Add it to `INVESTIGATIONS` in `pipelines/common.py` (acronym, folder, table, role, kind, platform).
3. Write `silver_<name>()` in `silver.py`: keep `source_record`, add `record_id`, `source_row`, normalized columns with `*_status`, register materials via `add_sample()`, measurements via `meas()`, quarantine anything unusable.
4. Add its schema to `SPEC` in `pipelines/validation/validate.py` and the endpoint map `SILVER_TABLES` in `backend/app.py`.
5. Only add it to a Gold table if it measures the same thing as that table; otherwise create a new Gold table.
6. Run pipeline + tests.

## Versioning
- Bronze: `data/manifests/bronze_manifest.csv` (hash per file). A changed hash fails validation — raw data is immutable.
- Silver/Gold: regenerated deterministically; versioned by Git commit. Each run is appended to `data/manifests/pipeline_runs.jsonl`.

## Recovery from a failed run
Outputs are fully regenerated each run, so: fix the cause shown in the console / quality report, re-run. If Bronze was modified by mistake, `git checkout -- data/raw` restores it (hashes must match the manifest).
