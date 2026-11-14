# 07 · Insights and solution

**Final problem statement:** Mission engineers can't quickly tell which cabin materials are fire-safe on the Moon, Mars or in orbit, because NASA's microgravity fire results are scattered and Earth certification runs in 1 g — and materials can burn at lower oxygen in microgravity.

**How Might We** help engineers trust a fire-safety answer for conditions nobody has fully tested?

**Value proposition:** For mission and habitat engineers who need to choose safe cabin materials, AstroFire is an AI fire-safety evidence tool that answers *will it burn, what proves it, and how sure are we* in minutes. Unlike reading papers or asking a chatbot, every answer is built from NASA experiments and shows how close that evidence is to your mission.

## Solution ideas considered (scored impact × feasibility × judge appeal × originality, 1–5 each)
| Idea | Score |
|---|---|
| Scenario risk check with cited evidence + confidence | **5×4×5×4 = 400** ✅ core |
| Hidden-risk list (passes Earth test, fails in space) | **5×4×5×5 = 500** ✅ wow moment |
| Research gap map + next experiment | 4×4×4×5 = 320 ✅ |
| Skeptic agent reviewing answers | 4×3×4×5 = 240 ✅ (Should) |
| Fan control advisor | 4×3×4×4 = 192 (Could) |
| Fire FMEA + crew card (Arabic/English) | 3×3×3×4 = 108 (Could) |
| ESP32 live cabin node | 3×1×4×4 = 48 ❌ cut |
| 3D flame simulation | 2×1×4×3 = 24 ❌ cut |

## The ONE wow moment
Pick **Lunar habitat (34% O₂, 8.2 psia)** → the hidden-risk list lights up a fabric that passes the Earth test → click it → cited NASA evidence + "confidence: low — no experiments at 0.17 g" → gap map recommends the exact next experiment.
