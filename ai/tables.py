"""Thin cached access to the Gold tables and the EXISTING engines (no second engine is built here).

Real names used (see docs/DATA_DICTIONARY.md):
  gold/analytics/solid_fire_tests.csv      test_id, investigation_id, investigation, material_raw, material_family_effective,
                                           material_identity, geometry, o2_initial_pct, pressure_kpa, pressure_status,
                                           flow_min_cm_s, outcome_class, outcome_basis, source_file, source_row, psi_url
  gold/analytics/droplet_extinction_tests  test_id, fuel, o2_pct, pressure_kpa, diluent, outcome_class, outcome_basis, source_file, source_row
  gold/analytics/gas_flame_tests           test_id, investigation, fuel, flame_type, o2_pct, pressure_kpa, outcome_class, ...
  gold/analytics/smoke_generation_tests    record_id, investigation, material, flow_cm_s, heater_resistance_ratio, aging_time_s, ...
  gold/analytics/investigation_profiles.json (24 profiles)   gold/ml/solid_outcome_features.csv (ML table)
Engines reused: backend.engine.Engine (scenario, gaps), backend.ranking.rank, backend.compare.compare_profiles.
"""
from __future__ import annotations

import json
from functools import lru_cache

import pandas as pd

from .config import ROOT

GOLD = ROOT / "data" / "gold"
TABLES = {
    "solid": "analytics/solid_fire_tests.csv", "droplet": "analytics/droplet_extinction_tests.csv",
    "cool_flame": "analytics/cool_flame_tests.csv", "gas": "analytics/gas_flame_tests.csv",
    "smoke": "analytics/smoke_generation_tests.csv", "gas_jet": "analytics/gas_jet_flame_conditions.csv",
    "ml": "ml/solid_outcome_features.csv",
}


@lru_cache(maxsize=None)
def table(name: str) -> pd.DataFrame:
    return pd.read_csv(GOLD / TABLES[name], dtype=str, keep_default_na=False)


@lru_cache(maxsize=1)
def profiles() -> dict:
    return {p["investigation_id"]: p for p in json.loads((GOLD / "analytics" / "investigation_profiles.json").read_text(encoding="utf-8"))}


@lru_cache(maxsize=1)
def engine():
    from backend.engine import Engine
    return Engine()


def habitats() -> dict:
    from pipelines.common import HABITATS
    return HABITATS


def missions() -> dict:
    from backend.engine import MISSIONS
    return MISSIONS


def by_acronym() -> dict:
    return {p["acronym"].upper(): p for p in profiles().values()}


def psi_url(investigation_id: str | None) -> str | None:
    p = profiles().get(investigation_id or "")
    return p["psi_url"] if p else None
