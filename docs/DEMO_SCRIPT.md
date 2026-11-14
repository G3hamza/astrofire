# AstroFire — 2-minute demo (PSI data only)

Start: `uvicorn backend.app:app` → open http://127.0.0.1:8000/ . Backup: http://127.0.0.1:8000/lite/ (no build, works offline).
The data behind every step is checked by `tests/test_demo_flow.py`.

| # | Screen / link | Say | On screen |
|---|---|---|---|
| 1 | Home `/` | "NASA ran 263 solid-material fire tests in space, all at 13.6–22.2% oxygen and ~0 g. Moon and Mars habitats will run at 34% oxygen and 56.5 kPa." | Big 263, the habitat atmosphere, the two "closest space flames" cards (ACME 34.08% O₂ / 50.7 kPa, FLEX 34% / 71 kPa) |
| 2 | `/scenario?material=Aramid+fabric+%28Nomex%29&mission=iss` | "Nomex on the ISS: NASA has tests near this; they're mixed, so the honest answer is borderline, and here are the 5 closest tests, each linked to NASA." | Verdict "Borderline in tested evidence", "2 of 5 burned", evidence table with PSI link + file#row; click a test ID for the full NASA record |
| 3 | Click **Mars** | "Same material on Mars: AstroFire refuses to guess. Three reasons: no test at Mars gravity, 34% oxygen is outside what solids were tested at, and the pressure was never tested." | Red verdict, blockers, then "More context": why the gap exists, and the closest space flames at 34% O₂ |
| 4 | Compare `/compare` | "Side by side: ISS, Exploration, Moon, Mars. This is exactly where the evidence stops." | 4 columns, "differs" markers, change summary |
| 5 | Gaps `/gaps` | "Only 2 of 30 space condition cells have a solid-material test. Seven others had droplet or gas flames, but no cabin material." | Tested / flames-only / no-PSI-test cells, mission pins |
| 6 | Experiments `/experiments#acme` | "We used all 24 combustion investigations in NASA's PSI repository. ACME even burned gas flames at habitat-like air." | ACME chart with the habitat point |
| 7 | (back to Home) | "AstroFire shows NASA where to test next." | — |

Optional: type *"Nomex on Mars at 34% oxygen and 8.2 psi"* under "Or describe it in words" on Scenario; `/materials`; `/data`.

Rehearsal log (fill in): 1 ☐ 2 ☐ 3 ☐
