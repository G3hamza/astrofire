# AstroFire — UI stack for a hand-crafted (not "AI-generated") interface

Goal: a mission-control instrument that looks designed by people who care about the data, not a template.
Keep the current base (it already works, is tested and deploys), and add a few precise tools on top.
Pair this file with `docs/UI_CONTEXT.md` (screens, API shapes, rules) and the reference prompt + images.

## 1. The stack

| Layer | Choice | Why |
|---|---|---|
| Framework | **React 18 + TypeScript + Vite** (keep) | Already wired to the API, tests and Vercel |
| Styling | **Tailwind CSS** (keep) + CSS variables tokens in `src/index.css` | Tokens already defined; change look by editing tokens, not every page |
| Primitives | **Radix UI** (`@radix-ui/react-dialog`, `-tabs`, `-tooltip`, `-popover`, `-slider`, `-toggle-group`) — styled by us | Accessible behavior (focus, keyboard, Esc) without someone else's look. Avoid stock shadcn styling: copy the components, then restyle them to our tokens |
| Motion | **Motion** (`motion` package, formerly Framer Motion) | Purposeful motion only: verdict reveal, panel slide, number count-up; respect `prefers-reduced-motion` |
| Charts | **visx** (`@visx/scale`, `@visx/axis`, `@visx/shape`, `@visx/heatmap`) for the flammability map and gaps grid; keep Recharts for simple bars | Bespoke, instrument-like charts with our own axes, ticks and annotations — the biggest "not generated" signal |
| Icons | **Phosphor Icons** (thin/regular weights) or keep Lucide at 1.5 stroke | Consistent line weight; one icon family only |
| Type | **IBM Plex Sans** + **IBM Plex Mono** (or **Geist** + **Geist Mono**), via `@fontsource` self-hosted | Engineering feel, excellent numerals; self-hosted = no external calls |
| Imagery | **NASA public-domain photos** (images.nasa.gov: flame balls, ISS, Saffire) with credit line | Real flames beat stock gradients |
| Tables | **TanStack Table** (headless) | Sorting/filtering the evidence tables with our own markup |
| State / data | keep `useQuery` in `src/lib/api.ts` (or **TanStack Query** if caching gets complex) | Already handles loading/error |
| Quality | **Storybook** (optional) or the existing `/style` page; **axe** / Lighthouse for a11y; **Playwright** screenshots at 1366×768 | Catch regressions; the projector size is the real target |

Install (when ready):
```bash
cd frontend-app
npm i @radix-ui/react-dialog @radix-ui/react-tabs @radix-ui/react-tooltip @radix-ui/react-slider motion @visx/scale @visx/axis @visx/shape @visx/group @visx/heatmap @tanstack/react-table @fontsource/ibm-plex-sans @fontsource/ibm-plex-mono --legacy-peer-deps
```

## 2. Design rules that stop it looking generated
1. **No purple-blue gradient blobs, no glassmorphism everywhere, no emoji headings, no "✨".** One accent (signal cyan) used sparingly.
2. **A real grid**: 12 columns, 8 px spacing scale, aligned baselines. Dense where data lives, airy around the verdict.
3. **Data is the decoration**: the flame map, the gaps grid and the gravity bounds are the hero visuals, drawn with care
   (labeled axes, units, tick marks, the 34 % / 56.5 kPa habitat line annotated directly on the chart).
4. **Technical detailing**: mono numerals with units, thin 1 px rules, small uppercase labels, record IDs and `file#row`
   chips like an instrument readout.
5. **Restrained color**: outcomes (burn orange, out blue, blowoff magenta, grey unknown) only on data; UI chrome stays neutral.
6. **Copy with a voice**: short, factual sentences ("NASA never tested this."), not marketing filler.
7. **Motion with meaning**: verdict appears after evidence loads; no bouncing cards.
8. **Real NASA photos** with credits, cropped tight, desaturated behind text only if contrast stays ≥ 4.5:1.
9. **Every state designed**: loading skeletons in the final shape, insufficient-evidence as a strong designed result, errors with retry.

## 3. How to apply a reference prompt + pictures
1. Extract tokens from the pictures (background, surface, line, text, accent, radius, type) → update `src/index.css` and `tailwind.config.js`.
2. Rebuild primitives (`components/ui.tsx`, badges, VerdictBanner) to match; check `/style`.
3. Rebuild pages one at a time in the order judges see them: Home → Scenario → Ask panel → Rank → Gaps → About.
4. After each page: `npm run build`, `pytest -q tests/test_frontend.py tests/test_journeys.py`, look at 1366×768.
5. Keep the hard rules in `docs/UI_CONTEXT.md` §2 (no probability wording, exact verdict strings, icon + text with color, citations visible).
