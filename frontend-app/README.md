# AstroFire app (Gate 2)

React 18 + Vite 5 + TypeScript + Tailwind 3, Recharts for charts. Talks only to `/api/*` (NFR8).

```bash
npm install --legacy-peer-deps   # once
npm run build                    # -> dist/, served by FastAPI at "/"
npm run dev                      # optional hot reload on :5173 (proxies /api to :8000)
```

Then from the project root: `uvicorn backend.app:app` and open http://127.0.0.1:8000/.

| Path | What |
|---|---|
| `/style` | Design system: tokens, type, outcomes, evidence badges, source chips, KPI tiles, verdicts, callouts, states (live data) |
| `src/index.css` | Color tokens (CSS variables) |
| `tailwind.config.js` | Token → Tailwind names, type scale |
| `src/components/` | `ui.tsx` (Card, Button, Callout, states), `badges.tsx`, `SourceChip.tsx`, `KpiTile.tsx`, `VerdictBanner.tsx`, `AppShell.tsx` |
| `src/lib/domain.ts` | Outcome / basis / verdict vocabulary from `docs/DATA_CONTRACTS.md` |
| `samples/` | Real JSON from every endpoint (reference for field names) |

Rules: no probability / % chance / prediction wording (checked by `tests/test_frontend.py`); outcomes and evidence quality always use icon + text, not color alone; every number carries a source chip; missing values show "not available".
