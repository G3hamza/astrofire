"""Rank the 24 PSI investigations by relevance to a crew habitat (challenge objective 1).

Score 0-100 = weighted sum of four components, each 0-1, every one explained in plain words:

  conditions (40)  How close the investigation's TESTED oxygen, pressure and gravity are to the habitat's.
                   Inside the tested range = 1; falls off linearly outside it (oxygen: 0 at 10 points away,
                   pressure: 0 at 50 kPa away). Gravity: same gravity = 1; PSI flight data at ~0 g only BOUNDS
                   Moon/Mars gravity (challenge: "microgravity and normal-gravity results could bound ...") = 0.5.
                   A factor NASA did not record scores 0 and is said so.
  relevance (25)   Challenge-based tier: direct 1.0 / related 0.6 / background 0.25 (see data/curation/).
  fuel (20)        Cabin fire risk is mostly solid materials: solid 1.0, smoke from heated materials 0.9,
                   dust/aerosol 0.5, gas or liquid-droplet flames 0.4.
  evidence (15)    Usable test records: flight records 0.5 (+0.5 x share of outcomes NASA observed);
                   ground analysis of flight data 0.3; models without a table 0.2.

Weights follow the team's agreed order: conditions > relevance > fuel > evidence. They are constants here (RANK_WEIGHTS)
and are returned with every ranking so a judge can see and question them. This is a relevance ranking, not a
probability or a safety rating.
"""

RANK_WEIGHTS = {"conditions": 40, "relevance": 25, "fuel": 20, "evidence": 15}
TIER_SCORE = {"direct": 1.0, "related": 0.6, "background": 0.25}
FUEL_SCORE = {"solid": 1.0, "smoke (heated materials)": 0.9, "dust / aerosol": 0.5, "gas": 0.4, "liquid droplet": 0.4}
O2_ZERO_AT, P_ZERO_AT = 10.0, 50.0


def _range(profile, prefixes):
    vals = [(c["min"], c["max"]) for c in profile["conditions"]
            if c["kind"] == "range" and any(c["factor"].startswith(p) for p in prefixes)]
    if not vals:
        return None
    return min(v[0] for v in vals), max(v[1] for v in vals)


def _closeness(value, rng, zero_at):
    lo, hi = rng
    gap = 0.0 if lo <= value <= hi else (lo - value if value < lo else value - hi)
    return max(0.0, 1 - gap / zero_at), gap


def _fmt(lo, hi, unit):
    return f"{lo:g}{unit}" if lo == hi else f"{lo:g}–{hi:g}{unit}"


def score(profile, hab):
    reasons = []
    # --- conditions
    o2 = _range(profile, ("Oxygen", "Highest oxygen"))
    if o2:
        s_o2, gap = _closeness(hab["o2_pct"], o2, O2_ZERO_AT)
        reasons.append(f"Oxygen tested {_fmt(*o2, '%')}: " + ("covers" if gap == 0 else f"{gap:.1f} points from") + f" the habitat's {hab['o2_pct']:g}%.")
    else:
        s_o2 = 0.0
        reasons.append("Oxygen not recorded in NASA's table for this investigation.")
    pr = _range(profile, ("Pressure",))
    if pr:
        s_p, gap = _closeness(hab["pressure_kpa"], pr, P_ZERO_AT)
        assumed = " (assumed ISS cabin pressure, not measured)" if profile["fuel_phase"] == "solid" else ""
        reasons.append(f"Pressure tested {_fmt(*pr, ' kPa')}{assumed}: " + ("covers" if gap == 0 else f"{gap:.1f} kPa from") + f" the habitat's {hab['pressure_kpa']:g} kPa.")
    else:
        s_p = 0.0
        reasons.append("Pressure not recorded in NASA's table for this investigation.")
    flight = profile["study_type"] == "flight"
    if hab["gravity_g"] < 0.01:
        s_g = 1.0 if flight else 0.5
        reasons.append("Microgravity flight data: same gravity as the habitat." if flight else "Ground analysis of microgravity flight data.")
    else:
        s_g = 0.5 if flight else 0.25
        reasons.append(f"Only ~0 g data: PSI has no partial-gravity combustion tests, so this can only bound {hab['gravity_g']:g} g from below.")
    if profile.get("partial_gravity_note"):
        reasons.append(profile["partial_gravity_note"])
    s_cond = 0.45 * s_o2 + 0.35 * s_p + 0.20 * s_g
    # --- relevance, fuel, evidence
    s_rel = TIER_SCORE[profile["relevance_tier"]]
    s_fuel = FUEL_SCORE.get(profile["fuel_phase"], 0.4)
    reasons.append(f"{profile['relevance_tier'].capitalize()} relevance ({profile['pillar']}); fuel: {profile['fuel_phase']}.")
    n = profile["records"]
    obs = (profile.get("outcomes") or {}).get("by_basis", {}).get("observed", 0)
    if profile["study_type"] == "flight" and n:
        share = obs / n if profile.get("outcomes") else 0
        s_ev = 0.5 + 0.5 * share
        reasons.append(f"{n} flight records" + (f", {obs} with outcomes NASA observed." if profile.get("outcomes") else "; no outcomes in the table."))
    elif profile["study_type"] == "ground analysis":
        s_ev = 0.3; reasons.append("Ground analysis; no flight test table of its own.")
    else:
        s_ev = 0.2 if not n else 0.4; reasons.append("Modeling study; no flight test table." if not n else f"{n} records.")
    comps = {"conditions": s_cond, "relevance": s_rel, "fuel": s_fuel, "evidence": s_ev}
    total = sum(RANK_WEIGHTS[k] * v for k, v in comps.items())
    return {"investigation_id": profile["investigation_id"], "acronym": profile["acronym"], "title": profile["title"],
            "pillar": profile["pillar"], "pillar_secondary": profile["pillar_secondary"], "relevance_tier": profile["relevance_tier"],
            "fuel_phase": profile["fuel_phase"], "hardware_family": profile["hardware_family"], "psi_url": profile["psi_url"],
            "score": round(total, 1), "components": {k: round(v, 3) for k, v in comps.items()},
            "condition_parts": {"oxygen": round(s_o2, 3), "pressure": round(s_p, 3), "gravity": round(s_g, 3)},
            "reasons": reasons}


def rank(profiles, hab, pillar=None):
    rows = [score(p, hab) for p in profiles if not pillar or pillar in (p["pillar"], p["pillar_secondary"])]
    rows.sort(key=lambda r: (-r["score"], r["acronym"]))
    for i, r in enumerate(rows, 1):
        r["rank"] = i
    return rows


METHOD = __doc__
