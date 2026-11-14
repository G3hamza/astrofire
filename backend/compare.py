"""Similarities and differences between investigation profiles (used by /api/investigations/compare and the AI tools)."""

KEYS = ("investigation_id", "acronym", "title", "pillar", "pillar_secondary", "relevance_tier", "hardware_family",
        "fuel_phase", "study_type", "records", "varied_factors", "constant_factors", "conditions", "psi_url")
NOTE = ("Factors come from NASA tables; sensors and measured quantities from keyword matches on NASA's text. "
        "A missing sensor means NASA's text does not name it, not that it was absent.")


def compare_profiles(ps):
    def split(sets):
        common = set.intersection(*sets)
        return sorted(common), {p["investigation_id"]: sorted(s - common) for p, s in zip(ps, sets)}

    fac_common, fac_unique = split([{c["factor"] for c in p["conditions"]} for p in ps])
    sen_common, sen_unique = split([{s["sensor"] for s in p["sensors"]} for p in ps])
    mea_common, mea_unique = split([{m["sensor"] for m in p["measured_quantities"]} for p in ps])
    return {"investigations": [{k: p[k] for k in KEYS} for p in ps],
            "same": {k: len({p[k] for p in ps}) == 1 for k in ("pillar", "hardware_family", "fuel_phase", "study_type", "relevance_tier")},
            "factors": {"in_all": fac_common, "only_in": fac_unique},
            "sensors": {"in_all": sen_common, "only_in": sen_unique},
            "measured_quantities": {"in_all": mea_common, "only_in": mea_unique},
            "note": NOTE}
