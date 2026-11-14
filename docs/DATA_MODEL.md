# Data Model (Phases 3–5)

Normalized entities in Silver; denormalized analytical tables in Gold. Machine-readable row schemas: `schemas/silver/*.schema.json`, `schemas/gold/*.schema.json`. Diagram: ER_DIAGRAM.md.

## Entities

| Entity | Physical table | PK | Key FKs | Cardinality |
|---|---|---|---|---|
| Investigation | `gold/powerbi/investigation_overview.csv` (+ `data/raw/psi/*/investigation.json`) | `investigation_id` (PSI accession) | — | 1 investigation → N records |
| Test / Experiment record | `silver/investigations/<investigation>.csv` (one schema per investigation) | `record_id` | `investigation_id`, `material_id` | N records → 1 material |
| Material | `silver/materials/materials.csv` | `material_id` | — | 1 material → N samples |
| Sample (specimen) | `silver/materials/material_samples.csv` | `sample_id` | `record_id`, `material_id` | 1 record → 1 sample (these tables have one specimen per row) |
| Material property | `silver/materials/material_properties.csv` | `property_id` | `sample_id`, `material_id` | 1 sample → 0..N properties |
| Measurement | `silver/measurements/measurements.csv` | `measurement_id` (`record_id|quantity`) | `record_id` | 1 record → 0..N measurements |
| Environmental condition | columns on each record (`o2_*`, `pressure_kpa` + `pressure_status`, `flow_*`, `gravity_g`) and rows in Measurement | — | — | per record |
| Combustion outcome | `outcome_class` + `outcome_basis` on each record | — | — | per record |
| Scientific paper | `gold/rag/documents.jsonl` | `document_id` (`NTRS-<id>`) | `related_investigations` (keyword-matched, not FK-enforced) | 1 doc → N chunks |
| Passage | `gold/rag/chunks.jsonl` | `chunk_id` | `document_id` | |
| Data source (file) | `data/manifests/bronze_manifest.csv` | `path` | referenced by every record's `source_file` | 1 file → N records |
| Data quality issue | `data/quarantine/quarantine.csv` | (row) | `record_id` (when known), `source_file` | 1 record → 0..N issues |
| Reference limit (partial g) | `silver/reference/partial_gravity_limits.csv` | `material` | `source_ntrs_id` → paper | |

## Material classification (Phase 3D)

| `classification_basis` | Meaning | `material_family` |
|---|---|---|
| `explicit_name` | NASA wrote the material (PMMA, SIBAL, Nomex, Kapton, ...) | the family |
| `unknown_shape_only` | NASA wrote only a shape ("1/4\" black rod", "2 cm sphere", "200 micron film") | `Unknown`; `candidate_family` may hold PMMA from investigation context (BASS/BASS-II), confidence `none` |
| `unknown` | nothing usable | `Unknown` |

`chemical_name`, `material_composition`, `manufacturer`, `material_description` are empty because no source table states them.

## Value status vocabulary
- `observed` — NASA table value; `derived (formula)` — unit conversion, formula recorded; `assumed (...)` — not in source, reason given; `missing` — left empty.
- Outcome: `outcome_class` ∈ Burned, Extinction, Blowoff, No Ignition, Not Sustained, Disruption (FLEX droplet), Not a flame test, Unknown. `outcome_basis` ∈ observed, inferred, not_recorded, not_applicable.

## Constraints enforced by `validate.py`
Unique PKs; required columns non-empty; numeric types; ranges (O2 0–100 %, pressure 1–500 kPa, flow 0–100 cm/s); FK integrity (samples→materials, samples/measurements→records, properties→samples, Gold tests→Silver); allowed outcome vocabularies; every Silver/Gold row has `source_file` + `source_row` present in the Bronze manifest; Bronze hashes unchanged; ML table has only observed labels; no inferred outcome marked reliable.

## Indexing (if loaded into a database)
`record_id`, `material_id`, `investigation_id` (all tables); `(record_id, quantity)` on measurements; `document_id` on chunks; full-text index on `chunks.text`.

## Why not one generic experiment table
BASS-II (solid flame spread, air flow), FLEX (fuel droplets, pressure + diluent), SPICE (gas-jet soot flames), SAME/SAME-R (smoke from heated materials, no flame) measure different things. They share only the Investigation, Material, Measurement and Data-source entities; each keeps its own Silver table, and Gold only combines tables of the same experiment kind (solid flame spread: BASS + BASS-II + SAFFIRE; smoke: SAME + SAME-R, non-shared columns left blank).
