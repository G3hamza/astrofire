"""Generate docs/DATA_DICTIONARY.md from the actual Silver/Gold files (so it never drifts from the data)."""
import csv
from pipelines.common import ROOT, DOCS

DESC = {
    "record_id": "Unique record id within AstroFire (investigation acronym + NASA test/sample number).",
    "test_id": "Same as Silver record_id.", "investigation_id": "NASA PSI accession (e.g. PSI-25).", "investigation": "Investigation acronym.",
    "source_file": "Bronze file the row came from (path in repo).", "source_row": "Line number in the NASA CSV (header = line 1).",
    "source_record": "Full original NASA row as JSON (nothing lost).", "quality_status": "valid | warning (see quality_notes).",
    "quality_notes": "Why the row was flagged.", "material_id": "FK -> silver/materials/materials.csv.",
    "material_original_name": "Material text exactly as NASA wrote it.", "material_family": "Family from an explicit name only; 'Unknown' if NASA did not name it.",
    "candidate_family": "Low-confidence family from investigation context (e.g. BASS-II rods). Never used as the classified family.",
    "material_family_effective": "material_family, or candidate_family when unknown. Use together with material_identity.",
    "material_identity": "named in NASA table | not named; family inferred from investigation context | unknown.",
    "classification_basis": "explicit_name | unknown_shape_only | unknown.", "classification_confidence": "high | none.",
    "o2_initial_pct": "Initial O2, % by volume (observed).", "o2_final_pct": "Final O2, % by volume (observed).",
    "pressure_kpa": "Ambient pressure, kPa. ISS/Cygnus solids: ASSUMED 101.3 (see pressure_status). FLEX: measured.",
    "pressure_status": "observed | assumed (...)", "flow_start_cm_s": "First air-flow setting, cm/s.", "flow_min_cm_s": "Lowest air-flow setting reached, cm/s.",
    "flow_cm_s": "Air flow, cm/s.", "outcome_class": "Burned | Extinction | Blowoff | No Ignition | Not Sustained | Disruption | Not a flame test | Unknown.",
    "outcome_basis": "observed (NASA wrote it) | inferred (derived from notes) | not_recorded | not_applicable.",
    "label_reliable": "True only when outcome_basis = observed.", "thickness_mm": "Sample thickness in mm, as labeled by NASA.",
    "diameter_mm": "Rod/sphere diameter in mm, converted from the NASA label (inches/cm).",
    "o2_pct": "O2 mole fraction x 100 (FLEX).", "co2_pct": "CO2 mole fraction x 100 (FLEX header 'CO' restored to CO2).",
    "he_pct": "Helium mole fraction x 100.", "n2_pct": "N2 mole fraction x 100.", "burning_rate_as_labeled": "FLEX 'Burning rate; mm' value, unit kept as NASA labeled it.",
    "value_status": "observed | derived (formula) | assumed.", "quantity": "Measured quantity name.", "unit": "Unit of value.",
    "duplicate_of": "SPICE: record this row exactly duplicates (excluded from Gold).", "split": "train | test (grouped by investigation+date).",
}
TABLES = ["silver/investigations/bass2_tests.csv", "silver/investigations/bass_tests.csv", "silver/investigations/saffire1_tests.csv",
          "silver/investigations/saffire2_tests.csv", "silver/investigations/saffire3_tests.csv", "silver/investigations/same_smoke_tests.csv",
          "silver/investigations/same_r_smoke_tests.csv", "silver/investigations/flex_droplet_tests.csv", "silver/investigations/spice_flames.csv",
          "silver/materials/materials.csv", "silver/materials/material_samples.csv", "silver/materials/material_properties.csv",
          "silver/measurements/measurements.csv",
          "gold/analytics/solid_fire_tests.csv", "gold/analytics/droplet_extinction_tests.csv", "gold/analytics/gas_jet_flame_conditions.csv",
          "gold/analytics/smoke_generation_tests.csv", "gold/analytics/mission_coverage.csv",
          "gold/analytics/investigation_profiles.csv",
          "gold/powerbi/investigation_overview.csv", "gold/powerbi/material_overview.csv", "gold/powerbi/outcome_summary.csv",
          "gold/powerbi/data_quality_overview.csv", "gold/powerbi/kpis.csv", "gold/ml/solid_outcome_features.csv", "quarantine/quarantine.csv"]


def main():
    out = ["# Data Dictionary", "", "Auto-generated from the files by `pipelines/validation/dictionary.py`. Each file also has a `.parquet` copy and (Silver/Gold) a JSON Schema in `schemas/`.", ""]
    for t in TABLES:
        p = ROOT / "data" / t
        if not p.exists(): continue
        rows = list(csv.DictReader(open(p, encoding="utf-8")))
        out += [f"## `data/{t}` — {len(rows)} rows", "", "| column | filled | example | meaning |", "|---|---|---|---|"]
        for c in (rows[0].keys() if rows else []):
            filled = sum(1 for r in rows if r[c] not in ("", None))
            ex = next((r[c] for r in rows if r[c]), "")[:40].replace("|", "/").replace("\n", " ")
            out.append(f"| {c} | {filled}/{len(rows)} | {ex} | {DESC.get(c, '')} |")
        out.append("")
    (DOCS / "DATA_DICTIONARY.md").write_text("\n".join(out), encoding="utf-8")


if __name__ == "__main__":
    main()
