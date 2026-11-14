# StarryNight AI layer (`ai/`)

An evidence-grounded analyst over NASA PSI combustion data. **Verdicts and numbers come from deterministic code**
(`backend/engine.py`, `backend/ranking.py`, the Gold tables). **The LLM only explains** evidence it is given, and every
output passes guardrails. Without an API key everything still works in **template mode** (labelled "not AI-written").

## Architecture

```
question ─► chat.py router (rules first, LLM fallback) ─► tools.py (controlled tools over existing engines)
                 │  entities: investigations, habitat, material, O2, pressure, gravity; last 6 turns of history
                 ▼
          evidence.py Registry (E1, E2 … each with source file + row, PSI URL or passage id)
                 ▼
          template answer (deterministic)  ──or──  llm.py (LLM writes from evidence only)
                 ▼
          guardrails.py: no probability · numbers must be in evidence · citations must exist · injection sanitized · secrets redacted
                 ▼
          /api/ask contract: answer, findings[], interpretation[], limits[], followups[], tools_used[], mode, model
```

| File | Role |
|---|---|
| `config.py` | `.env` loading, provider-agnostic LLM (`init_chat_model`), retry, optional fallback provider, offline-first embeddings |
| `retrieval.py` | BM25 (`rank_bm25`) over `data/gold/rag/chunks.jsonl` (cached); hybrid BM25 + Chroma with RRF when embeddings exist |
| `ingest.py` | Optional Chroma ingest (idempotent, `--rebuild`); says "BM25-only mode" when no embeddings |
| `tables.py` | Cached Gold tables + the existing engines (no second engine) |
| `tools.py` | search_investigations, get_investigation, search_records, rank_habitat, run_scenario, compare_investigations, research_gaps, search_passages, list_datasets |
| `guardrails.py` | no-probability filter, number validator, injection sanitizer, off-topic detector (`No data in the NASA papers provided.`) |
| `features.py` | `ask`, `scenario`, `compare`, `gaps`, `experiment_summary` |
| `chat.py` | `analyze()` / `chat()`: router + analyst |
| `api.py` | FastAPI router, cache, rate limit, optional API key |
| `prompts/*.txt` | system, analyst, ask, scenario_reasons, compare, gap, experiment_summary, router |
| `eval/` | 26 questions + `python -m ai.eval.run` |

## Knowledge base (PSI only)
`data/gold/rag/chunks.jsonl` is rebuilt by the pipeline (`pipelines/transformation/rag.py`) from the 24 investigation
profiles: NASA's own text (objective, hypothesis, approach, research impacts) = `nasa_text`; summaries computed from the
Gold tables and a cross-investigation overview = `computed_summary`; the challenge's resources tab (Earth applications,
incidents, habitat atmosphere, partial-gravity status) = `challenge_resource`. The earlier 307 NTRS papers are no longer
used (outside the challenge's data scope). Fields keep contract (B): `chunk_id, document_id, chunk_index, char_start,
char_end, page (null), title, year, url, topic, related_investigations[], content_type, text`.

## Environment (`.env`, see `.env.example`)
| Variable | Default | Meaning |
|---|---|---|
| `LLM_PROVIDER` | `groq` | `groq` \| `anthropic` \| `openai` \| `google_genai` |
| `LLM_MODEL` | `openai/gpt-oss-120b` | model id for that provider |
| `GROQ_API_KEY` / `ANTHROPIC_API_KEY` / … | empty | empty = template mode |
| `LLM_FALLBACK_PROVIDER`, `LLM_FALLBACK_MODEL` | empty | used automatically on rate-limit or provider errors |
| `AI_API_KEY` | empty | if set, `/ai/*` requires header `X-API-Key` (the app's own `/api/ask` stays open for the UI) |
| `AI_RATE_LIMIT` | `20` | AI requests per client per minute |
| `EMBEDDINGS_BACKEND` | auto | `local_folder` (if `./models/all-MiniLM-L6-v2` exists) \| `huggingface` \| `fastembed` \| `none` |

**Failover chain** (`LLM_FALLBACKS`, default `groq:qwen/qwen3.8-27b,groq:openai/gpt-oss-20b,anthropic:claude-haiku-5-5`):
`ai/config.py` `ModelChain` tries the primary, then each fallback in order; every link but the last has no client retries,
so a 429 / outage / missing credits moves on in about a second. Each skipped link is reported in `guardrails`
(e.g. `skipped:openai/gpt-oss-120b:RateLimitError`) and `model` names the model that answered. Groq limits are per model
(free tier: 200,000 tokens/day for gpt-oss-120b), so other Groq models are useful free fallbacks.

**Failover (Groq → Claude Haiku 5.5):** with `LLM_FALLBACK_PROVIDER=anthropic`, `LLM_FALLBACK_MODEL=claude-haiku-5-5` and
`ANTHROPIC_API_KEY` set, the primary model is called with no client retries, so a rate limit (429) or outage switches to Claude
in about a second. The response's `model` field says which model answered. If both fail, the template answer is returned.
If only the fallback key is set, it is used alone. `GET /api/ask/status` shows `fallback_ready`.

Switch provider: change `LLM_PROVIDER` + `LLM_MODEL` + the matching key, restart. Example for Claude:
`LLM_PROVIDER=anthropic`, `LLM_MODEL=claude-haiku-5-5`, `ANTHROPIC_API_KEY=…` (temperature is omitted for Claude models).

## Retrieval modes
- **BM25-only (default here):** no downloads, nothing to ingest. The tokenizer keeps `BASS-II`, `SAME-R`, `CFI-G` whole and as parts.
- **Hybrid:** put `all-MiniLM-L6-v2` in `./models/`, `pip install chromadb langchain-chroma langchain-huggingface sentence-transformers`,
  run `python -m ai.ingest`. Retrieval then fuses Chroma + BM25 with reciprocal rank fusion. Nothing is downloaded automatically.

## Endpoints
| Method + path | Body | Returns |
|---|---|---|
| `POST /api/ask` | `{question, habitat?, history?}` | answer, findings[], interpretation[], limits[], followups[], tools_used[], mode, model, intent, evidence[], sources[], insufficient_evidence, request_id, latency_ms |
| `GET /api/ask/status` | | ai_enabled, provider, model, retrieval, knowledge_base_chunks (never keys) |
| `POST /ai/chat` | same as /api/ask | same |
| `POST /ai/ask` | `{question, investigation?}` | `{answer, sources[]}` |
| `POST /ai/scenario` | `{environment, o2, pressure, material?, fuel_type?, gravity_g?, flow_cm_s?}` | verdict (Scenario contract values), coverage (Directly tested / Closest evidence / Gap), reasons[2-4], evidence[], blockers, caveats |
| `POST /ai/compare` | `{ids: [2-3]}` | table[] (attribute, values, differs), narrative, sources |
| `POST /ai/gaps` | `{scenario?}` | gaps[] (fuel × O2 band × pressure band × gravity with 0 space tests, high priority), covered[], cells[] (Gaps map), narrative |
| `GET /ai/summary/{id}` | | objective, materials, conditions, outcome_summary, caveats, sources (written on first request, then cached) |
| `GET /ai/health` | | ok + status |

```bash
curl -s -X POST localhost:8000/api/ask -H "content-type: application/json" -d '{"question":"Would Nomex burn at 30% oxygen and 71 kPa on the Moon?"}'
curl -s -X POST localhost:8000/ai/scenario -H "content-type: application/json" -d '{"environment":"moon","o2":30,"pressure":71,"material":"Aramid fabric (Nomex)"}'
curl -s -X POST localhost:8000/ai/compare -H "content-type: application/json" -d '{"ids":["SAME","SAME-R"]}'
curl -s localhost:8000/ai/summary/BASS-II
```

## Guardrails (inside every feature)
1. **No probability:** chance / probability / likelihood / odds / confidence wording → regenerate once, then strip the sentence. "30% oxygen" is allowed.
2. **Number validator:** every number in generated text must appear in the evidence (rounding and kPa/psi/atm tolerance) → regenerate once, then the deterministic template.
3. **Citations:** the LLM may cite only `[E#]` ids in the evidence; unknown ids are removed and the finding is dropped (and the drop is reported in `limits`).
4. **Verdict lock:** scenario verdicts come from the engine; if it says "Insufficient validated experimental evidence", the answer starts with that sentence whatever the LLM wrote.
5. **Injection:** instruction-like text in questions or retrieved text is removed and reported; evidence is wrapped as untrusted data.
6. **Off-topic / rockets:** exact string `No data in the NASA papers provided.`
7. **Secrets:** keys are read only from `.env`, never returned; outputs are scanned for key patterns.

## Tests and evaluation
```bash
pytest -q                          # all data, API and AI tests (AI tests use a fake LLM: offline, free)
python -m ai.eval.run --template   # deterministic mode
python -m ai.eval.run              # AI mode if a key is configured -> ai/eval/report.md
```

## Known limitations
- Retrieval is lexical (BM25) unless a local embedding model is added.
- Template answers quote evidence; they are accurate but less fluent than AI mode.
- AI mode with Groq has not been run in this environment until a key is placed in `.env` (tests use a scripted fake LLM).
- One eval citation miss: cross-investigation facts (e.g. highest oxygen tested) come from a computed overview passage not tied to one investigation.
- No streaming yet; the UI shows a progress line while the request runs.
