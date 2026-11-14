# AstroFire — data analysis (run in Kaggle or Jupyter; one "# %%" block = one cell)
# Upload these files as a Kaggle Dataset named "astrofire" (from data/gold/ and data/processed/):
#   solid_fire_tests.csv, droplet_extinction_tests.csv, partial_gravity_limits.csv, papers.csv
# Each section answers ONE decision question. Read the "SO WHAT" after each output.

# %% 0. Load
import pandas as pd, numpy as np, matplotlib.pyplot as plt, glob, os
base = next((os.path.dirname(p) for p in glob.glob('/kaggle/input/**/solid_fire_tests.csv', recursive=True)), '.')
T  = pd.read_csv(f'{base}/solid_fire_tests.csv')
T['material_family'] = T['material_family_effective']; T['outcome'] = T['outcome_class']
FX = pd.read_csv(f'{base}/droplet_extinction_tests.csv')
PG = pd.read_csv(f'{base}/partial_gravity_limits.csv')
P  = pd.read_csv(f'{base}/papers.csv')
print(T.shape, PG.shape, P.shape)

# %% 1. QUALITY CHECK — can we trust each column?  (do this before any chart)
q = pd.DataFrame({'missing_%': T.isna().mean().mul(100).round(0), 'unique': T.nunique()})
print(q.sort_values('missing_%', ascending=False).head(12))
print('\nOutcome basis:\n', T.outcome_basis.value_counts())
print('Material identity:\n', T.material_identity.value_counts())
print('Pressure status:\n', T.pressure_status.value_counts())
# SO WHAT: only use 'observed' outcomes for headline claims; 'inferred' = supporting evidence only.
# 1 in 3 tests do not name the material (rods/spheres) -> treat their family as a guess.

# %% 2. WHAT IS TESTED?  Pareto of materials (vital few)
m = T.material_family.value_counts()
cum = m.cumsum() / m.sum() * 100
ax = m.plot.bar(figsize=(10, 4), title='Tests per material family')
ax2 = ax.twinx(); cum.plot(ax=ax2, color='k', marker='o'); ax2.set_ylim(0, 105); ax2.axhline(80, ls='--')
plt.show(); print(pd.DataFrame({'tests': m, 'cum_%': cum.round(0)}))
# SO WHAT: a few materials (PMMA, cotton-fibreglass…) carry most evidence. Any other material = "Low confidence".

# %% 3. WHERE IS THE EVIDENCE?  Conditions tested vs. where astronauts will live
print(T.groupby('investigation').agg(tests=('test_id', 'count'), g=('gravity_g', 'max'),
      o2_min=('o2_initial_pct', 'min'), o2_max=('o2_initial_pct', 'max'),
      kpa=('pressure_kpa', 'median'), flow_max=('flow_start_cm_s', 'max')))
targets = pd.DataFrame({'mission': ['ISS', 'Exploration (8.2 psia)', 'Moon habitat', 'Mars habitat'],
                        'g': [0, 0, 0.166, 0.38], 'o2': [21, 34, 34, 34], 'kpa': [101, 56.5, 56.5, 56.5]})
targets['space_tests_matching'] = [((T.o2_initial_pct.sub(r.o2).abs() <= 2) & (T.pressure_kpa.sub(r.kpa).abs() <= 15)).sum()
                                   for r in targets.itertuples()]
print(targets)
# SO WHAT: this table IS the product's headline: 0 space tests at the Moon/Mars design atmosphere.

# %% 4. WHEN DOES A FLAME GO OUT?  Oxygen x air-flow map (stated outcomes only)
S = T[(T.outcome_basis == 'observed') & T.o2_initial_pct.notna() & T.flow_start_cm_s.notna()]
fig, ax = plt.subplots(figsize=(8, 5))
groups = {'burned': S.outcome.eq('Burned'), 'went out': S.outcome.isin(['Extinction', 'No Ignition', 'Not Sustained']),
          'blowoff': S.outcome.eq('Blowoff')}
for (o, mask), c in zip(groups.items(), ['tab:red', 'tab:blue', 'tab:purple']):
    s = S[mask]
    ax.scatter(s.flow_start_cm_s, s.o2_initial_pct, c=c, label=f'{o} ({len(s)})', alpha=.7)
ax.set_xlabel('air flow (cm/s)'); ax.set_ylabel('O2 %'); ax.legend(); ax.set_title('Microgravity flammability map'); plt.show()
print(S.groupby('outcome')[['o2_initial_pct', 'flow_start_cm_s']].describe().round(1))
# SO WHAT: in space, low air flow can put a flame out that would keep burning on Earth -> ventilation is a safety lever.

# %% 5. EARTH vs SPACE — does the 1 g test predict space? (SAFFIRE burn lengths)
sf = T[T.investigation.str.contains('SAFFIRE', na=False)][['material_raw', 'flow_start_cm_s', 'ug_burn_length', 'one_g_burn_length', 'notes_raw']]
print(sf.dropna(subset=['ug_burn_length', 'one_g_burn_length'], how='all').to_string()[:3000])
# SO WHAT: same material, different result by gravity -> Earth pass/fail is not enough on its own.

# %% 5b. FLEX — the only space fires near the exploration atmosphere (fuel droplets, not materials)
hi = FX[FX.o2_pct >= 30]
print(hi.groupby(['fuel', 'diluent']).agg(tests=('test_id', 'count'), p_min_kpa=('pressure_kpa', 'min'), p_max_kpa=('pressure_kpa', 'max')))
print(FX.groupby(['diluent', 'outcome_class']).size().unstack(fill_value=0))
# SO WHAT: 34% O2 at ~71 kPa HAS been flown — but only for liquid droplets. No solid material ever has.

# %% 6. MOON & MARS — the oxygen safety margin (NASA drop-tower data, Olson/Ferkul 2013)
ax = PG.set_index('material')[['moon_margin_o2', 'mars_margin_o2', 'zero_g_margin_o2']].plot.bar(figsize=(8, 4))
ax.axhline(0, c='k'); ax.set_ylabel('O2 margin vs 1 g (percentage points)')
ax.set_title('Negative = burns at LOWER oxygen than on Earth'); plt.show()
print(PG[['material', 'moon_margin_o2', 'mars_margin_o2', 'zero_g_margin_o2']])
# SO WHAT: all 3 materials are MORE flammable on Moon and Mars than on Earth (up to 5.75 points of O2).
# An Earth "pass" near the limit can be a "fail" on the Moon. This is the business case for AstroFire.

# %% 7. HOW FRESH / HOW DEEP IS THE LITERATURE?
P['year'] = pd.to_numeric(P['year'], errors='coerce')
P.year.plot.hist(bins=range(1965, 2030, 5), figsize=(8, 3), title='Papers per 5 years'); plt.show()
print(P.groupby('topic').size().sort_values(ascending=False))
# SO WHAT: show paper year next to every AI citation; flag answers that rely only on pre-2000 papers.

# %% 8. SIMPLE BASELINE MODEL — honest, small, explainable (optional)
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score
M = S.assign(y=S.outcome.eq('Burned').astype(int))[['o2_initial_pct', 'flow_start_cm_s', 'thickness_mm', 'y']].dropna()
if M.y.nunique() == 2 and len(M) > 20:
    X, y = M.drop(columns='y'), M.y
    print('rows', len(M), '| 5-fold accuracy', cross_val_score(LogisticRegression(max_iter=1000), X, y, cv=5).mean().round(2),
          '| baseline (always majority)', round(max(y.mean(), 1 - y.mean()), 2))
    print(dict(zip(X.columns, LogisticRegression(max_iter=1000).fit(X, y).coef_[0].round(3))))
# SO WHAT: if accuracy is not clearly above the baseline, do NOT ship a "predictor". Ship the evidence-distance ranking.
