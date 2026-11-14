"""StarryNight engine: answers from real NASA tests, never invented numbers.

- scenario(): finds the NASA space tests closest to your mission conditions ("evidence distance"),
  reads what actually happened in them, and says how confident we can be.
- flammability_map(): real microgravity points (oxygen vs airflow) from BASS-II, with outcome.
- gaps(): which gravity / oxygen / pressure combinations have been tested, and which have not.
- atmosphere(): closest FLEX/CFI droplet flames and ACME gas flames at the same oxygen and pressure.

Reads ONLY the Gold layer (data/gold), which the pipeline regenerates from Bronze (python -m pipelines.orchestration.run_all).
Scientific-safety rules: similarity-weighted shares are NOT probabilities; inputs outside tested ranges return
"Insufficient validated experimental evidence"; every result lists its evidence with source file + row.
"""
import csv, json, math, re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GOLD = ROOT / "data" / "gold"
SILVER = ROOT / "data" / "silver"

# Mission design points: single definition in pipelines/common.HABITATS (sources in docs/SOURCES.md)
from pipelines.common import HABITATS
MISSIONS = {k: {"name": h["name"], "gravity_g": h["gravity_g"], "o2_pct": h["o2_pct"], "pressure_kpa": h["pressure_kpa"]}
            for k, h in HABITATS.items() if h["in_missions"]}
# Distance scales: how far apart two conditions must be to count as "one unit" different
SCALE = {"gravity_g": 0.1, "o2_pct": 2.0, "pressure_kpa": 15.0, "flow_cm_s": 5.0}


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _kind(t):
    o = t["outcome_class"]
    return "blowoff" if o == "Blowoff" else "went out" if o in ("Extinction", "No Ignition", "Not Sustained") else "burned" if o == "Burned" else None


class Engine:
    def __init__(self):
        rd = lambda p: list(csv.DictReader(open(p, encoding="utf-8")))
        self.tests = rd(GOLD / "analytics" / "solid_fire_tests.csv")
        for t in self.tests:
            for k in ("gravity_g", "o2_initial_pct", "pressure_kpa", "flow_start_cm_s", "flow_min_cm_s", "thickness_mm"):
                t[k] = _f(t[k])
            t["material_family"] = t["material_family_effective"]   # search key; identity basis kept in material_identity
        self.investigations = rd(GOLD / "powerbi" / "investigation_overview.csv")
        self.material_overview = rd(GOLD / "powerbi" / "material_overview.csv")
        self.kpis = rd(GOLD / "powerbi" / "kpis.csv")
        self.coverage = rd(GOLD / "analytics" / "mission_coverage.csv")
        # FLEX fuel-droplet flames (ISS, ~0 g). A different experiment kind: never mixed into solid-material results,
        # only shown as "what flames did at this oxygen and pressure".
        self.droplets = rd(GOLD / "analytics" / "droplet_extinction_tests.csv")
        for t in self.droplets:
            t["investigation"] = "FLEX"
            for k in ("o2_pct", "pressure_kpa", "burn_time_s", "droplet_initial_diameter_mm", "extinction_diameter_mm"):
                t[k] = _f(t[k])
        # CFI cool-flame droplet tests (ISS): conditions only, NASA recorded no outcome.
        self.cool = rd(GOLD / "analytics" / "cool_flame_tests.csv")
        for t in self.cool:
            t["investigation"] = "CFI"
            for k in ("o2_pct", "pressure_kpa"):
                t[k] = _f(t[k])
        self.space_flames = self.droplets + self.cool  # liquid-fuel flames in orbit (never material evidence)
        # ACME gaseous flames (CFI-G with NASA outcome codes, Flame Design conditions only): 12-85 % O2, 0.42-3.3 atm.
        self.gas = rd(GOLD / "analytics" / "gas_flame_tests.csv")
        for t in self.gas:
            for k in ("o2_pct", "pressure_kpa", "burn_time_s"):
                t[k] = _f(t[k])

    # ---------- materials ----------
    def materials(self):
        c = Counter(t["material_family"] for t in self.tests)
        named = Counter(t["material_family"] for t in self.tests if t["material_identity"] == "named in NASA table")
        return [{"material": m, "tests": n, "tests_material_named": named[m], "tests_material_inferred": n - named[m]} for m, n in c.most_common()]

    # ---------- real microgravity flammability map ----------
    def flammability_map(self, material=None):
        pts = []
        for t in self.tests:
            if t["o2_initial_pct"] is None or t["flow_min_cm_s"] is None: continue
            if material and t["material_family"] != material: continue
            kind = _kind(t)
            if kind is None: continue
            pts.append({"test_id": t["test_id"], "investigation": t["investigation"], "material": t["material_family"],
                        "material_identity": t["material_identity"], "o2_pct": t["o2_initial_pct"], "flow_cm_s": t["flow_min_cm_s"],
                        "outcome": kind, "outcome_class": t["outcome_class"], "outcome_basis": t["outcome_basis"], "raw": t["notes_raw"],
                        "source_file": t["source_file"], "source_row": t["source_row"], "psi_url": t["psi_url"]})
        return pts

    # ---------- scenario: evidence distance + what really happened ----------
    def scenario(self, material, gravity_g, o2_pct, pressure_kpa, flow_cm_s):
        q = {"gravity_g": gravity_g, "o2_pct": o2_pct, "pressure_kpa": pressure_kpa, "flow_cm_s": flow_cm_s}
        cands = []
        for t in self.tests:
            if t["o2_initial_pct"] is None or t["flow_min_cm_s"] is None or _kind(t) is None: continue
            v = {"gravity_g": t["gravity_g"], "o2_pct": t["o2_initial_pct"], "pressure_kpa": t["pressure_kpa"], "flow_cm_s": t["flow_min_cm_s"]}
            parts = {k: (q[k] - v[k]) / SCALE[k] for k in q}
            d = math.sqrt(sum(x * x for x in parts.values()))
            same = t["material_family"] == material
            d_eff = d + (0 if same else 1.5)
            cands.append((d_eff, d, same, parts, t))
        cands.sort(key=lambda x: x[0])
        top = cands[:8]
        if not top:
            return {"verdict": "Insufficient validated experimental evidence", "evidence_status": "none", "confidence": "none", "evidence": [], "flags": ["No tests with conditions recorded."]}

        w = Counter()
        for d_eff, d, same, parts, t in top:
            w["burned" if _kind(t) == "burned" else "out"] += 1 / (1 + d_eff)
        share = w["burned"] / sum(w.values())
        tendency = "nearby tests mostly burned" if share >= 0.66 else "nearby tests mixed" if share >= 0.33 else "nearby tests mostly went out"

        flags, blockers = [], []
        tested_o2 = [t["o2_initial_pct"] for t in self.tests if t["o2_initial_pct"] is not None]
        if all(abs(gravity_g - g) > 0.01 for g in {t["gravity_g"] for t in self.tests}):
            blockers.append(f"No solid-material space test in the NASA PSI tables ran at {gravity_g} g (all are ~0 g).")
        if o2_pct > max(tested_o2) + 0.5 or o2_pct < min(tested_o2) - 0.5:
            blockers.append(f"Oxygen {o2_pct}% is outside the range tested in the PSI tables ({min(tested_o2)}–{max(tested_o2)}%).")
        if abs(pressure_kpa - 101.3) > 15:
            blockers.append(f"Pressure {pressure_kpa} kPa: every solid space test in the PSI tables is at assumed ISS cabin pressure (~101 kPa).")
        if not any(c[2] for c in top):
            blockers.append(f"No space test of '{material}' near these conditions.")
        if any(c[4]["outcome_basis"] == "inferred" for c in top[:3]):
            flags.append("Some nearby outcomes are inferred from NASA notes (no extinction/blowoff written).")
        if any(c[4]["material_identity"] != "named in NASA table" for c in top[:3]):
            flags.append("Some nearby samples are not named in the NASA table; their family is inferred from the investigation.")
        flags.append("Pressure of all ISS/Cygnus solid tests is assumed, not measured.")

        best = top[0][0]
        if blockers:
            verdict, status, confidence = "Insufficient validated experimental evidence", "exploratory", "Low"
        else:
            verdict = {"nearby tests mostly burned": "Evidence suggests it burns", "nearby tests mixed": "Borderline in tested evidence",
                       "nearby tests mostly went out": "Evidence suggests it goes out"}[tendency]
            status = "evidence-based"
            confidence = "High" if best < 1.0 and len(flags) <= 1 else "Medium" if best < 2.5 else "Low"

        ev = []
        for d_eff, d, same, parts, t in top[:5]:
            far = max(parts, key=lambda k: abs(parts[k]))
            ev.append({"test_id": t["test_id"], "investigation": t["investigation"], "material": t["material_raw"],
                       "material_family": t["material_family"], "material_identity": t["material_identity"], "same_material": same,
                       "o2_pct": t["o2_initial_pct"], "flow_cm_s": t["flow_min_cm_s"], "gravity_g": t["gravity_g"],
                       "pressure_kpa": t["pressure_kpa"], "pressure_status": t["pressure_status"], "outcome": t["outcome_class"],
                       "outcome_basis": t["outcome_basis"], "distance": round(d_eff, 2), "biggest_difference": far.replace("_", " "),
                       "raw": t["notes_raw"], "source_file": t["source_file"], "source_row": t["source_row"], "psi_url": t["psi_url"], "doi": t["doi"]})
        return {"scenario": {"material": material, **q}, "verdict": verdict, "evidence_status": status, "confidence": confidence,
                "nearby_tendency": tendency, "nearby_burn_share": round(share, 2),
                "nearby_burn_share_note": "Similarity-weighted share of the closest tests that burned. NOT a calibrated probability.",
                "evidence_distance": round(best, 2), "blockers": blockers, "flags": flags,
                "evidence": ev, "why_untested": self.why_untested(q),
                "atmosphere_evidence": self.atmosphere(q),
                "gravity_bounds": self.gravity_bounds(material, q) if q["gravity_g"] > 0.01 else None}

    # ---------- partial gravity: bound between 0 g (orbit) and 1 g (NASA's own 1 g comparison in PSI) ----------
    PARTIAL_G_SOURCES = {
        "e_field": {"investigation": "ACME E-FIELD Flames (PSI-22)", "url": "https://psi.nasa.gov/physci/repo/data/investigations/PSI-22",
                    "text": "Partial gravity was mimicked in ACME's E-FIELD Flames with an electric field acting on the ions in gas flames. "
                            "It is a mimic for gas flames, not a partial-gravity test of any material."},
        "coming": [{"name": "LUCI (Lunar-g Combustion Investigation)", "status": "expected in PSI in the future (challenge text)"},
                   {"name": "FM2 (Flammability of Materials on the Moon)", "status": "expected in PSI in the future (challenge text)"}],
        "basis": "Challenge text: there is currently no partial-gravity combustion data in PSI; microgravity and normal-gravity "
                 "results could bound what occurs at intermediate gravity levels.",
    }

    def gravity_bounds(self, material, q):
        """What PSI says at the two ends of the gravity range for this material. Never a value for the requested gravity."""
        mat = (material or "").lower()
        key = mat.split("(")[-1].rstrip(")").strip() if "(" in mat else mat
        same = lambda t: t["material_family"] == material or (key and key in (t["material_raw"] or "").lower())
        zero = [t for t in self.tests if same(t) and _kind(t) is not None]
        z_o2 = [t["o2_initial_pct"] for t in zero if t["o2_initial_pct"] is not None]
        one = [t for t in self.tests if same(t) and (t.get("one_g_burn_length") or "").strip()]
        lower = {"gravity_g": 0.0, "label": "microgravity (ISS / Cygnus)", "tests": len(zero),
                 "outcomes": dict(Counter(t["outcome_class"] for t in zero)),
                 "outcome_basis": dict(Counter(t["outcome_basis"] for t in zero)),
                 "o2_range": [min(z_o2), max(z_o2)] if z_o2 else None, "pressure": "assumed ~101 kPa (cabin)",
                 "note": None if zero else f"No microgravity test of '{material}' with a recorded outcome in PSI."}
        upper = {"gravity_g": 1.0, "label": "normal gravity (1 g) comparison by NASA in Saffire-II", "tests": len(one),
                 "pairs": [{"test_id": t["test_id"], "material": t["material_raw"], "o2_pct": t["o2_initial_pct"],
                            "microgravity_burn_length": t["ug_burn_length"], "one_g_burn_length": t["one_g_burn_length"],
                            "microgravity_outcome": t["outcome_class"], "source_file": t["source_file"],
                            "source_row": t["source_row"], "psi_url": t["psi_url"]} for t in one],
                 "note": None if one else (f"PSI holds no 1 g result for '{material}'. NASA's 1 g certification tests "
                                           "(NASA-STD-6001 Test 1) are not in the PSI repository.")}
        both_o2 = [x for x in (lower["o2_range"] or [])] + [t["o2_initial_pct"] for t in one if t["o2_initial_pct"] is not None]
        covers = bool(zero and one and both_o2 and min(both_o2) - 1 <= q["o2_pct"] <= max(both_o2) + 1 and abs(q["pressure_kpa"] - 101.3) <= 15)
        applies = ("Both ends exist at this atmosphere, so they bracket the requested gravity; the value in between is still untested."
                   if covers else
                   f"These bounds were measured at cabin air (~{min(both_o2):g}-{max(both_o2):g}% O2, ~101 kPa), not at "
                   f"{q['o2_pct']:g}% O2 and {q['pressure_kpa']:g} kPa, so they do not bound this scenario: "
                   "Insufficient validated experimental evidence." if both_o2 else
                   "No PSI data at either end of the gravity range for this material: Insufficient validated experimental evidence.")
        return {"requested_gravity_g": q["gravity_g"], "lower_bound": lower, "upper_bound": upper, "bounds_cover_request": covers,
                "applies": applies, "partial_gravity_mimic": self.PARTIAL_G_SOURCES["e_field"],
                "coming_next": self.PARTIAL_G_SOURCES["coming"], "basis": self.PARTIAL_G_SOURCES["basis"]}

    def atmosphere(self, q, k=3):
        """Closest space flames by oxygen + pressure: up to k droplet flames (FLEX/CFI) and k gas flames (ACME),
        so one kind never hides the other. Never material evidence; never changes a verdict."""
        return self._atm_droplets(q, k) + self._atm_gas(q, k)

    def _atm_gas(self, q, k):
        rows = [t for t in self.gas if t["o2_pct"] is not None and t["pressure_kpa"] is not None]
        def d(t):
            return math.hypot((q["o2_pct"] - t["o2_pct"]) / SCALE["o2_pct"], (q["pressure_kpa"] - t["pressure_kpa"]) / SCALE["pressure_kpa"])
        # prefer tests where NASA recorded how the flame ended, then nearest
        best = sorted(rows, key=lambda t: (t["outcome_basis"] != "observed", round(d(t), 1)))
        best = sorted(best[: max(k * 4, 12)], key=d)[:k] if best else []
        return [{"test_id": t["test_id"], "investigation": t["investigation"], "kind": "gas flame",
                 "fuel": f"{t['fuel']} ({t['flame_type'].lower()} flame)", "o2_pct": t["o2_pct"], "pressure_kpa": t["pressure_kpa"],
                 "diluent": "not stated in NASA table", "gravity_g": 0.0, "outcome": t["outcome_class"], "outcome_basis": t["outcome_basis"],
                 "test_end_raw": t["test_end_raw"], "burn_time_s": t["burn_time_s"], "droplet_initial_diameter_mm": None,
                 "distance": round(d(t), 2), "source_file": t["source_file"], "source_row": t["source_row"], "psi_url": t["psi_url"],
                 "note": f"Gas-jet flame ({t['investigation']}), not a solid material. Pressure: {t['pressure_status']}."} for t in best]

    def _atm_droplets(self, q, k=3):
        """Closest FLEX / CFI droplet flames by oxygen + pressure, nitrogen-diluted (air-like) runs only.
        Liquid fuel in ~0 g: says what flames did in that atmosphere, not whether a material burns."""
        rows = [t for t in self.space_flames if t["o2_pct"] is not None and t["pressure_kpa"] is not None and t["diluent"].startswith("N2")]
        def d(t):
            return math.hypot((q["o2_pct"] - t["o2_pct"]) / SCALE["o2_pct"], (q["pressure_kpa"] - t["pressure_kpa"]) / SCALE["pressure_kpa"])
        out = []
        for t in sorted(rows, key=d)[:k]:
            out.append({"test_id": t["test_id"], "investigation": t["investigation"], "kind": "droplet flame", "fuel": t["fuel"], "o2_pct": t["o2_pct"],
                        "pressure_kpa": t["pressure_kpa"], "diluent": t["diluent"], "gravity_g": 0.0,
                        "outcome": t["outcome_class"], "outcome_basis": t["outcome_basis"],
                        "burn_time_s": _f(t.get("burn_time_s")), "droplet_initial_diameter_mm": _f(t.get("droplet_initial_diameter_mm")),
                        "distance": round(d(t), 2), "source_file": t["source_file"], "source_row": t["source_row"], "psi_url": t["psi_url"],
                        "note": f"Liquid fuel droplet ({t['investigation']}), not a solid material. Shows what flames did at this oxygen and pressure in ~0 g."})
        return out

    PSI_SEARCH = "https://psi.nasa.gov/physci/repo/search?q=combustion"
    WHY = {
        "gravity": ("Every solid-material, droplet and gas-flame test in NASA's PSI combustion repository ran in orbit at ~0 g "
                    "(ISS or the uncrewed Cygnus). None ran at Moon (0.17 g) or Mars (0.38 g) gravity: nothing in orbit runs at "
                    "partial gravity, and the PSI repository holds no partial-gravity combustion tests.",
                    PSI_SEARCH),
        "oxygen": ("Solid-material fire tests in PSI ran at cabin air or below: BASS-II lowered oxygen by adding nitrogen. "
                   "The ISS combustion chamber did burn fuel droplets (FLEX, up to 34% O2) and gas flames (ACME, up to 85% O2), "
                   "shown below as atmosphere evidence, but no cabin materials.",
                   "https://psi.nasa.gov/physci/repo/data/investigations/PSI-25"),
        "pressure": ("The PSI tables for the ISS/Cygnus solid tests don't record pressure; it is the cabin's ~101 kPa. "
                     "Low-pressure flames in PSI are droplets (FLEX down to 70 kPa, CFI down to 50.7 kPa) and gas flames "
                     "(ACME down to 43 kPa), shown below.",
                     "https://psi.nasa.gov/physci/repo/data/investigations/PSI-159"),
    }

    def why_untested(self, q):
        tested_o2 = [t["o2_initial_pct"] for t in self.tests if t["o2_initial_pct"] is not None]
        out = []
        if q["gravity_g"] > 0.01:
            out.append("gravity")
        if q["o2_pct"] > max(tested_o2) + 0.5:
            out.append("oxygen")
        if abs(q["pressure_kpa"] - 101.3) > 15:
            out.append("pressure")
        return [{"topic": k, "text": self.WHY[k][0], "source_url": self.WHY[k][1]} for k in out]

    # ---------- gaps ----------
    def gaps(self):
        g_bins = [0.0, 0.166, 0.38, 1.0]
        o2_bins = [(14, 18), (18, 22.5), (22.5, 26), (26, 30), (30, 36)]
        p_bins = [(95, 105, "~101 kPa (ISS / sea level)"), (50, 80, "50–80 kPa (exploration)")]
        cells = []
        for g in g_bins:
            for lo, hi in o2_bins:
                for plo, phi, plab in p_bins:
                    n = sum(1 for t in self.tests if t["gravity_g"] == g and t["o2_initial_pct"] is not None
                            and lo <= t["o2_initial_pct"] < hi and plo <= (t["pressure_kpa"] or 0) <= phi)
                    note = ""
                    if g == 1.0:
                        note = "Earth certification (NASA-STD-6001 Test 1) runs here; results in MAPTIS, not in this dataset"
                    mission = [m["name"] for m in MISSIONS.values()
                               if abs(m["gravity_g"] - g) < 0.01 and lo <= m["o2_pct"] < hi and plo <= m["pressure_kpa"] <= phi]
                    drops = 0 if g != 0.0 else sum(1 for t in self.space_flames if t["o2_pct"] is not None and t["pressure_kpa"] is not None
                                                   and lo <= t["o2_pct"] < hi and plo <= t["pressure_kpa"] <= phi)
                    gas = 0 if g != 0.0 else sum(1 for t in self.gas if t["o2_pct"] is not None and t["pressure_kpa"] is not None
                                                 and lo <= t["o2_pct"] < hi and plo <= t["pressure_kpa"] <= phi)
                    cells.append({"gravity_g": g, "o2_range": f"{lo}–{hi}%", "pressure": plab, "space_tests": n, "gas_flame_tests": gas,
                                  "mission_design_points": mission, "note": note,
                                  "droplet_tests": drops})
        return cells

    def stats(self):
        burn = self.tests
        return {"tests": len(burn), "with_conditions": sum(1 for t in burn if t["o2_initial_pct"] is not None),
                "outcomes_observed": sum(t["outcome_basis"] == "observed" for t in burn),
                "investigations_with_tables": sum(1 for i in self.investigations if i["has_experimental_table"] == "True"),
                "investigations_total": len(self.investigations), "droplet_flame_tests": len(self.space_flames),
                "gas_flame_tests": len(self.gas),
                "o2_range_tested": [min(t["o2_initial_pct"] for t in burn if t["o2_initial_pct"] is not None),
                                    max(t["o2_initial_pct"] for t in burn if t["o2_initial_pct"] is not None)]}
