"""Run the whole data pipeline: Bronze manifest -> Silver -> Gold -> profiles -> PSI knowledge base -> validation.

    python -m pipelines.orchestration.run_all            # full rebuild
    python -m pipelines.orchestration.run_all --check    # validation only

Writes a run log to data/manifests/pipeline_runs.jsonl. Exit code 1 if validation fails.
"""
import json, sys, time
from pipelines.common import MANIFESTS, RUN_TS


def step(name, fn, log):
    t = time.time(); print(f"[{name}] ...", flush=True)
    try:
        out = fn(); log.append(dict(step=name, status="ok", seconds=round(time.time() - t, 2))); return out
    except Exception as e:
        log.append(dict(step=name, status="failed", error=str(e)[:300])); raise


def main():
    log = []
    try:
        if "--check" not in sys.argv:
            from pipelines.ingestion import manifest
            from pipelines.transformation import silver, gold, rag, profiles
            step("bronze_manifest", manifest.build, log)
            step("silver", silver.build, log)
            step("gold", gold.build, log)
            step("investigation_profiles", profiles.build, log)
            step("rag", rag.build, log)
        from pipelines.validation import validate
        rc = step("validate", validate.main, log)
        from pipelines.validation import dictionary
        step("data_dictionary", dictionary.main, log)
    except Exception as e:
        rc = 1; print("PIPELINE FAILED:", e)
    MANIFESTS.mkdir(parents=True, exist_ok=True)
    with open(MANIFESTS / "pipeline_runs.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(dict(run_at=RUN_TS, exit_code=rc, steps=log)) + "\n")
    print("pipeline", "OK" if rc == 0 else "FAILED")
    return rc


if __name__ == "__main__":
    sys.exit(main())
