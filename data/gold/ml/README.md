# ML-ready table — read before training

`solid_outcome_features.csv` holds the ONLY rows suitable as labels: solid flame tests whose outcome NASA wrote down (`label_source = observed`), with O2 and air flow recorded.

- Rows: see file (33 at last build). Target: `target_burned` (1 = burned, 0 = extinction / blowoff / no ignition / not sustained).
- Features: `o2_initial_pct`, `flow_min_cm_s`, `thickness_mm`, `diameter_mm`, `geometry`, `material_family_effective` (+ `material_identity`: named vs inferred).
- Split: `split` (train/test) grouped by investigation + test date (`split_group`) to reduce leakage between tests run the same day.
- Missing values: left empty. Do not impute thickness/diameter for fabrics or films without a source.
- Inferred outcomes (BASS-II rows where NASA only listed flows) are EXCLUDED on purpose.

**Status: not validated.** A logistic-regression baseline scored 0.74 accuracy vs 0.90 for "always predict the majority class" (5-fold CV). The data does not support a predictive model. Use this table for exploration only; the product uses evidence-distance ranking with citations instead.
