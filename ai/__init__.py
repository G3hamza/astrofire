"""AstroFire AI layer: evidence-grounded answers over NASA PSI combustion data.

Verdicts and numbers come from deterministic code over the Gold tables and the existing engines (backend/engine.py,
backend/ranking.py). The LLM only writes explanations from evidence it is given; guardrails check every output.
Works without any API key (template mode). See docs/AI_LAYER.md.
"""
