# 5. Frontend and UI

## 5.1 The tools, simply explained

**🧒 Simple version.** The website is built from small reusable pieces ("components") like LEGO bricks: a verdict box, a badge,
a table. **React** snaps the bricks together and redraws them when data changes. **TypeScript** checks our code for mistakes
before it runs. **Tailwind** is a quick way to style things (colors, spacing). **Vite** packs everything into a few small files
the browser can load fast. **Recharts** draws the charts.

**🛠️ Engineer version.**

| Tool | Version | Role |
|---|---|---|
| React | 18.3.1 | UI components, state |
| React Router | 6.28 | Pages and URLs (`/scenario`, `/gaps`…) |
| TypeScript | 5.6 (strict) | Types for API data and props; build fails on type errors |
| Vite | 5.4 | Dev server (port 5173, proxies `/api` to 8000) and production build to `dist/` |
| Tailwind CSS | 3.4 | Utility classes; theme tokens in `tailwind.config.js` |
| Recharts | 2.13 | Scatter charts (Charts, Experiments) |
| lucide-react | 0.460 | Icons |
| Node | 20 (Docker) / 24 (this laptop) | Build only; not needed at runtime |

Commands (in `frontend-app/`): `npm install --legacy-peer-deps` once, `npm run dev` (hot reload), `npm run build` (type-check + bundle).

## 5.2 Folder map

```
frontend-app/
├─ index.html              page shell, favicon
├─ tailwind.config.js      color/type tokens → Tailwind names (bg-surface, text-burn, text-h1…)
├─ vite.config.ts          dev proxy, build output
└─ src/
   ├─ main.tsx             routes, page titles, lazy loading
   ├─ index.css            color tokens (CSS variables), base styles
   ├─ lib/
   │  ├─ api.ts            fetch helper with clear errors + cached useQuery hook
   │  ├─ client.ts         one typed function per API endpoint
   │  ├─ types.ts          TypeScript shapes of every API response
   │  └─ domain.ts         outcome / basis / verdict vocabulary
   ├─ components/          reusable bricks (see 5.4)
   └─ pages/               one file per screen (see 5.3)
```

## 5.3 Every screen

| Screen | File | What it shows | API used |
|---|---|---|---|
| **Home** `/` | `HomePage.tsx` | 263 solid tests vs habitat air; closest gas and droplet flames; 5 KPIs; one card per mission (nearby solid tests or the closest flame, never a "0"); "Why it matters" (Apollo 1, Mir, Apollo 13) | stats, overview, missions, scenario ×4 |
| **Scenario** `/scenario` | `ScenarioPage.tsx` | SRS order: inputs (material, mission preset, 4 sliders, "describe in words") → verdict → "X of Y burned" → blockers → flags → 9-column evidence table → why untested + closest flames. Click a test ID → evidence drawer | material-families, missions, scenario, scenario/parse |
| **Compare** `/compare` | `ComparePage.tsx` | 2–4 scenarios side by side; "differs" markers; change summary vs scenario A; presets | scenario per column |
| **Gaps** `/gaps` | `GapsPage.tsx` | Two grids (cabin pressure / exploration pressure): solid tests, flames-only cells, "no PSI test" cells, mission pins | gaps |
| **Charts** `/charts` | `ChartsPage.tsx` | Flammability map: O₂ × air flow by outcome, filter by material, table view | map, missions |
| **Experiments** `/experiments` | `ExperimentsPage.tsx` | All 24 investigations; FLEX/CFI chart; ACME chart; FLEX-2 matrix; session logs; smoke; SPICE; challenge resources | investigations, droplets, cool-flames, gas-flames, session-logs, smoke, gas-jets, experiments |
| **Materials** `/materials`, `/materials/:id` | `MaterialsPage.tsx` | Catalog, named vs unknown identity, samples, limitations, smoke runs | materials, materials/{id}, smoke |
| **Data quality** `/data` | `DataQualityPage.tsx` | Observed / inferred / not recorded per investigation, validation, quarantine | overview, data-quality, materials |
| **Design system** `/style` | `StylePage.tsx` | Every component with live data (for the team) | several |
| **Lite** `/lite/` | `frontend/` | Plain HTML/JS backup: Home, Scenario, Gaps | same API |

## 5.4 Reusable components

| Component | File | Purpose |
|---|---|---|
| `AppShell` | `components/AppShell.tsx` | Top navigation, skip link, footer |
| `VerdictBanner` | `components/VerdictBanner.tsx` | The verdict exactly as the API wrote it, colored by tone, with status and confidence |
| `OutcomeTag`, `BasisBadge`, `ConfidenceBadge` | `components/badges.tsx` | Icon + word + color: Burned / Went out / Blowoff; Observed / Inferred / Assumed |
| `SourceChip`, `FileRowChip` | `components/SourceChip.tsx` | Link to NASA PSI; copy the exact file#row |
| `KpiTile` | `components/KpiTile.tsx` | Big number with unit; shows "not available" instead of inventing |
| `Callout` | `components/ui.tsx` | Red blockers / amber flags |
| `EvidenceDrawer` | `components/EvidenceDrawer.tsx` | Slide-over with the full cleaned NASA row for one test |
| `WhyUntestedCard`, `AtmosphereEvidenceCard` | `components/EvidenceContext.tsx` | Why the gap exists; closest droplet/gas flames |
| `DescribeScenario` | `components/DescribeScenario.tsx` | Free-text input showing what was understood and defaulted |
| `WhyItMatters`, `ChallengeResources` | `components/WhyItMatters.tsx` | Accident cards and the 10 official resources |
| `Card`, `Button`, `Skeleton`, `EmptyState`, `ErrorState` | `components/ui.tsx` | Basic bricks, loading/empty/error states |

## 5.5 How data flows in the browser

1. A page calls `useQuery("key", client.something)` (`lib/api.ts`).
2. `client.ts` calls `fetch("/api/...")`; errors become readable messages ("The AstroFire API is not reachable…").
3. Results are **cached** by key, so going back to a page is instant.
4. TypeScript types (`lib/types.ts`) describe each response. They were written from real responses (`frontend-app/samples/`).
5. **Scenario state lives in the URL** (`?material=…&mission=mars&flow=5`), so any scenario can be shared by copying the link.
   The page waits 250 ms after a slider moves before calling the API (debounce).

## 5.6 Design system ("mission control")

- **Dark theme**, high contrast, sized for a 1366×768 laptop and a projector.
- **Color tokens** in `src/index.css` as CSS variables, mapped to Tailwind names in `tailwind.config.js`:
  `space` (background), `surface`, `raised`, `line`, `ink` (text), `muted`, `faint`, `signal` (cyan accent), `burn` (orange),
  `out` (blue), `blow` (magenta), `danger` (red), `caution` (amber), `ok` (green).
- **Outcome colors were tested for color blindness** with a palette validator: blue vs violet failed, so blowoff became magenta.
- **Never color alone:** outcomes also have an icon and a word; on charts also a shape (circle / triangle / diamond); inferred
  values are hollow.

## 5.7 Accessibility and performance
- Keyboard: visible focus ring, skip-to-content link, Escape closes the drawer, buttons are real `<button>`s.
- Screen readers: charts have `role="img"` with a text label; tables have headers; a "show as table" view for the flammability map.
- Phone width: no horizontal page scroll at 375 px; tables scroll inside their own box.
- Speed: heavy pages (charts, Experiments, Materials, Data quality, Compare, design page) are **lazy-loaded**, so the first download
  is about 249 KB instead of ~680 KB; the chart library (~397 KB) loads only on pages with charts.

## 5.8 The /lite backup app
`frontend/index.html`, `style.css`, `app.js`: no build step, no libraries, no internet. Uses the same API and rules. All API text is
HTML-escaped before display. Use it if the React build fails during a demo.

## 5.9 How to add or change a screen
1. Create `src/pages/NewPage.tsx`.
2. Add a route and a title in `src/main.tsx`, and a nav item in `components/AppShell.tsx`.
3. Add any new endpoint to `lib/client.ts` and its type to `lib/types.ts`.
4. `npm run build` (must pass type-check), then add the path to `tests/test_frontend.py`.
5. Keep the rules: no probability words (a test scans the code), icons + words for states, source links next to numbers.
