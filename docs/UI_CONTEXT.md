# AstroFire — UI Context (brief for designing or rebuilding the interface)

Give this file (plus `docs/CONTEXT.md`) to a designer, a UI tool or an AI to redesign AstroFire without breaking it.
It lists every screen, what data each screen gets from the API, the components, states, design tokens and the rules
the UI must never break. Source of truth: `frontend-app/src/` (React 18 + Vite + TypeScript + Tailwind + Recharts).

---

## 1. Product in one line and the audience
"Evidence-first fire-safety analyst for Moon/Mars habitats, built only on NASA PSI combustion data."
Audience: hackathon judges, NASA engineers, students. Shown live on a **1366×768 laptop and a projector**, dark room.
Mood: mission control — dark, calm, precise, data-dense but readable. Every number is clickable back to its NASA source.

## 2. Hard rules (tests enforce several of them)
1. **No probability language in UI copy.** The words "probability", "% chance", "predict/prediction" must not appear,
   except in negations like "not a probability" (`tests/test_frontend.py`). Use "evidence suggests", "nearby burn share",
   "closest evidence".
2. **Verdicts are exactly these four strings** (from the API, never rewritten):
   `Evidence suggests it burns` · `Borderline in tested evidence` · `Evidence suggests it goes out` ·
   `Insufficient validated experimental evidence`.
3. **Outcome colors always come with an icon and a text label** (color-blind safe, NFR6). Never color alone.
4. **Every fact shows its source**: investigation id + `file#row` chip and/or a PSI link. Never hide citations.
5. **Separate NASA findings from AstroFire interpretation** visually (different headings / tone), and always show limits.
6. **Insufficient evidence is a first-class result**, not an error: it gets the strongest (danger) treatment and its
   blockers listed.
7. Observed vs inferred vs not recorded vs assumed must be visible on every outcome / pressure (BasisBadge).
8. The UI only calls `/api/*` and `/ai/*` on the same origin. No external scripts, no trackers, no secrets in the browser.
9. Ask AI must be reachable from every page.
10. Must work at 1366×768 without horizontal scroll; mobile is a nice-to-have (stacked layout).

## 3. Design tokens (current)
Colors are CSS variables (RGB channels) in `src/index.css`, mapped in `tailwind.config.js` (so `bg-surface/80` works).

| Token | Hex | Use |
|---|---|---|
| space | #05070D | page background |
| surface | #0B0F1A | cards |
| raised | #121828 | inputs, hover, nested cards |
| line | #222C44 | borders |
| ink | #ECF1F8 | primary text |
| muted | #A0ADC4 | secondary text |
| faint | #74819A | captions, disabled |
| signal | #5CE1E6 | scientific cyan: links, focus, data highlights |
| flare | #FFB84D | the one action accent: primary buttons, habitat design point |
| burn | #EA6624 | outcome: burned |
| out | #4B8FF7 | outcome: went out / extinction |
| blow | #E9479A | outcome: blowoff |
| unknown | #94A3B8 | outcome: not recorded |
| danger | #F85E6A | insufficient evidence, blockers |
| caution | #FBBF24 | flags, borderline, inferred, assumed |
| ok | #34D399 | observed / measured |

- Brand: **StarryNight** (logo: cyan four-point star with a flare core). Fonts: **IBM Plex Sans** (UI) and **IBM Plex Mono** (readouts, ids, file#row), self-hosted via @fontsource.
- Libraries: Radix UI (tabs, tooltip), Motion (section reveals), visx (evidence map on Home: `components/charts/AtmosphereMap.tsx`). NASA photos in `frontend-app/public/img/` with credits on screen.
- Type scale: label 12px uppercase tracking 0.08em · sm 13 · base 15 · lg 18 · h3 20 · h2 26 · h1 36 · display 56.
- Radius: cards 14px. Shadows: `card`, `glow` (signal ring), `danger` (red ring for insufficient verdict).
- Animations: `shimmer` (skeletons), `pulseDot` (live/loading dot). Respect `prefers-reduced-motion`.
- Live reference of all tokens and components: **`/style`**.

## 4. Layout shell
- `AppShell`: top bar with logo + nav (Home, Scenario, Compare, Gaps, Charts, Ask, Rank, Investigations, Experiments,
  Materials, Apply, Quality), content max-width container, footer (data: NASA PSI, CC0).
- `AskPanel`: floating **"Ask AI"** button bottom-right on every page except `/ask`; opens a side panel
  (`open ? "flex" : "hidden"` — do not rely on CSS transitions to show it) containing a lazy-loaded compact `AskChat`.

## 5. Screens (route → purpose → API → key UI)

| Route | Purpose | API calls | Key UI |
|---|---|---|---|
| `/` Home | Headline gap + entry points | `GET /api/stats`, `/api/analytics/overview`, `/api/missions` | Hero: "263 solid tests, all 13.6–22.2 % O₂, ~0 g"; KPI tiles; mission coverage; **Ask AstroFire box** (2 example chips → `/ask?q=`); WhyItMatters; ChallengeResources |
| `/scenario` | Material + conditions → verdict | `GET /api/missions`, `/api/material-families`; `POST /api/scenario/parse` (free text); `POST /api/scenario` | Mission presets, sliders (gravity 0–1 g, O₂ 0–100, pressure >0, flow), **"Describe it in your own words" (`<details open>`)**, VerdictBanner, blockers/flags callouts, evidence table → EvidenceDrawer, WhyUntestedCard, AtmosphereEvidenceCard, GravityBoundsCard, ComingNextCard |
| `/compare` | 2–4 scenarios side by side | `POST /api/scenario` ×N | Columns per scenario with verdict + key numbers |
| `/gaps` | Gravity × O₂ × pressure coverage | `GET /api/gaps` | Grid; cell = space tests / droplet / gas flame counts; mission pins (Moon/Mars) |
| `/charts` | Flammability map | `GET /api/map?material=` | Scatter O₂ vs flow, colored+shaped by outcome; filter by material; point → source |
| `/ask` | AI analyst chat | `GET /api/ask/status`; `POST /api/ask` | `AskChat` full size; reads `?q=` |
| `/rank` | Investigations ranked for a habitat | `GET /api/habitats`, `/api/rank?habitat=&pillar=` | Habitat picker, pillar filter, table 0–100 with 4-part breakdown and reasons |
| `/investigations` | Profiles + compare | `GET /api/investigations/profiles`, `/api/investigations/compare?ids=` | Card per investigation (objective, fuels, conditions ranges, what varied, sensors, not recorded); tick 2–6 → compare table |
| `/experiments` | Per-investigation charts | `/api/investigations`, `/api/droplets`, `/api/cool-flames`, `/api/gas-flames`, `/api/smoke`, `/api/gas-jets`, `/api/experiments?investigation_id=` | Tabs per investigation, Recharts plots |
| `/materials`, `/materials/:id` | Material catalogue | `GET /api/materials`, `/api/materials/{id}` | Table (named vs inferred, tests, observed outcomes); detail with samples, properties, limitations |
| `/applications` (Apply) | Use the results | `GET /api/datasets`, `/api/datasets/{name}.csv`, `/api/equipment-insights`, `/api/earth-applications` | Download cards with caveats; detection / suppression / materials insights; Earth spinoffs |
| `/data` (Quality) | Trust in the data | `GET /api/data-quality` | Tables valid %, quarantine by rule, outcome basis bar |
| `/style` | Design system page | — | All tokens/components |
| `/lite/` | No-JS-framework fallback | same API | Must stay plain and dependable |

## 6. Main data shapes the UI renders (from `src/lib/types.ts`)
```ts
ScenarioRequest = { material; mission?: "iss"|"exploration"|"moon"|"mars"; gravity_g?; o2_pct?; pressure_kpa?; flow_cm_s? }
ScenarioResult = { scenario; verdict; evidence_status; confidence; nearby_tendency;
  nearby_burn_share: number|null; nearby_burn_share_note; evidence_distance; blockers: string[]; flags: string[];
  evidence: EvidenceRow[]; why_untested: {topic,text,source_url}[]; atmosphere_evidence: AtmosphereTest[];
  gravity_bounds?: GravityBounds|null }
EvidenceRow = { test_id; investigation; material; same_material; o2_pct; flow_cm_s; gravity_g; pressure_kpa;
  pressure_status; outcome; outcome_basis; distance; biggest_difference; source_file; source_row; psi_url; doi }
GravityBounds = { requested_gravity_g; bounds_cover_request: boolean; applies; basis;
  lower_bound{tests, outcomes, o2_range, pressure, note}; upper_bound{tests, pairs[{test_id, microgravity_burn_length,
  one_g_burn_length, ...}]}; partial_gravity_mimic{investigation,url,text}; coming_next[{name,status}] }
GapCell = { gravity_g; o2_range; pressure; space_tests; mission_design_points: string[]; droplet_tests; gas_flame_tests; note }
RankResult = { habitat; weights; method; caveat; ranked: RankRow[] }   // score 0-100 + parts + reasons
```
**Ask (`POST /api/ask`, body `{question, habitat?, history?: [{role, content}] (last 6)}`)**:
```ts
{ answer; findings: string[]; interpretation: string[]; limits: string[]; followups: string[]; tools_used: string[];
  mode: "ai"|"template"; model: string|null; intent; evidence: {id:"E1", kind, text, acronym?, investigation_id?,
  source_file?, source_row?, psi_url?, url?, title?, level?}[]; insufficient_evidence: boolean; latency_ms; request_id }
```
Errors: `422` invalid input (show field message), `429` rate limit (20/min per visitor — show "wait a moment"),
`500` `{detail, request_id}` (show ErrorState with retry and the request id).

## 7. Components (reuse; keep the contracts)
| Component | Props / role |
|---|---|
| `Card`, `CardHeader{eyebrow,title,right}` | base container |
| `Button{variant,icon}` | primary / ghost |
| `Callout{tone,title,items}` | blockers (danger), flags (caution), notes |
| `Skeleton`, `EmptyState{title,hint}`, `ErrorState{message,onRetry}`, `NotAvailable` | states |
| `KpiTile{label,value,unit,caption,source,tone,loading}` | headline numbers with source |
| `VerdictBanner{verdict,confidence,evidenceStatus,size}` | tone from `verdictTone()`: burn / caution / out / danger |
| `OutcomeTag{outcome}` | icon + text + color via `outcomeKind()` (burned / out / blowoff / unknown) |
| `BasisBadge{basis}` | observed (ok) / inferred (caution) / assumed (caution) / not_recorded (unknown) |
| `ConfidenceBadge`, `EvidenceStatusBadge` | small status pills |
| `SourceChip{href,label}`, `FileRowChip{file,row}` | citations (mono font) |
| `EvidenceDrawer{row,onClose}` | side drawer with the full NASA record + raw row |
| `WhyUntestedCard`, `AtmosphereEvidenceCard`, `GravityBoundsCard`, `ComingNextCard` | scenario context |
| `DescribeScenario{onParsed,compact}` | free-text → parsed scenario (shows what was understood/assumed) |
| `AskChat{compact,initialQuestion}` | chat; renders answer + Findings / Interpretation / Limits sections, `[E#]` as buttons opening the evidence, follow-up chips, footer "Written by {model} from the evidence" or "Template answer from NASA records (not AI-written)" |
| `WhyItMatters`, `ChallengeResources` | storytelling on Home |

## 8. States every screen must design
- **Loading**: skeletons in the final layout shape (no layout jump); Ask shows a "thinking" pulse (answers take 2–10 s).
- **Empty**: e.g. no tests for a material filter → EmptyState with a hint.
- **Error**: ErrorState with retry; show `request_id` small; data screens must still work if AI fails.
- **Insufficient evidence**: danger banner + blockers + "closest evidence" still shown below + bounds card.
- **Template mode**: AI unavailable → same layout, footer says template; never looks broken.
- **Off-topic**: answer "No data in the NASA papers provided." shown as a neutral note with example questions.

## 9. Accessibility and quality
- Contrast ≥ 4.5:1 for text on `space`/`surface`; focus ring = `signal`; full keyboard use (drawer and panel close on Esc).
- Charts: outcome encoded by color **and** marker shape; tooltips with test id and source.
- Numbers in mono with units; O₂ as `%`, pressure `kPa` (psi on hover), gravity `g`.
- Big-screen legibility: base 15px min, verdict at h1/display size.

## 10. Copy voice
Short, factual, sourced. "Evidence suggests…", "NASA never tested…", "Closest evidence:", "Not recorded by NASA".
Never "safe", "guaranteed", "AI predicts". Label interpretation as "AstroFire interpretation".

## 11. Where to change things
Tokens `frontend-app/src/index.css` + `tailwind.config.js` · routes `src/main.tsx` · nav `components/AppShell.tsx` ·
API client `src/lib/client.ts` · shapes `src/lib/types.ts` · vocabulary `src/lib/domain.ts`.
Build: `cd frontend-app && npm run build` (FastAPI serves `dist/`). Check: `pytest -q tests/test_frontend.py tests/test_journeys.py`.
