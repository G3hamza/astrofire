# 1. Domain knowledge: fire in space

> Background science that explains *why* StarryNight exists and what its numbers mean. General combustion knowledge is marked
> as background; numbers that come from our data are marked with their source.

## 1.1 What a fire needs

**🧒 Simple version.** A fire needs three things: **fuel** (something that burns, like fabric or plastic), **oxygen** (from the
air) and **heat** (to keep it going). Take one away and the fire goes out. That's the "fire triangle".

**🛠️ Engineer version.** A flame is a fast chemical reaction between fuel vapour and oxygen. For a *solid* (a seat cover, a cable
jacket), heat from the flame warms the solid, which releases gas (pyrolysis); that gas mixes with oxygen and burns, which heats more
solid. The flame survives only while the heat it makes is larger than the heat it loses (to the surroundings, by radiation, and to
the cold solid). If losses win, the flame **extinguishes**.

## 1.2 Why fire behaves differently in space

**🧒 Simple version.** On Earth, hot air rises. That pulls fresh air into a candle flame from below and pushes smoke up, which
is why flames are pointy. In space there's no "up": hot air doesn't rise. The flame becomes a round, dim ball. It can starve
itself of oxygen and go out, **or** it can keep burning slowly where you don't expect it, especially if a fan blows air at it.

**🛠️ Engineer version.**
- On Earth, **buoyancy** (hot gas rising) creates a natural airflow of tens of cm/s around a flame. In **microgravity (~0 g)**
  that natural flow disappears, so the only airflow is what the spacecraft's **ventilation** provides (a few cm/s).
- That's why NASA's space experiments control **air flow speed** (cm/s): it replaces buoyancy as the main driver.
- **Low flow:** not enough oxygen arrives → the flame can go out (*quenching*). **High flow:** the flame can be **blown off**
  (*blowoff*). In between, a material can burn steadily. Space flammability is a map of oxygen vs flow, which StarryNight draws
  on the **Charts** page.
- **Flow direction matters.** *Opposed flow*: air comes against the direction the flame spreads. *Concurrent flow*: air goes
  the same way as the flame, which usually makes flames spread faster.

## 1.3 Oxygen and pressure

**🧒 Simple version.** More oxygen = things burn more easily. Moon and Mars habitats are planned with **34% oxygen** (Earth air is
21%) but at **lower pressure** (about half of Earth's). So the air is "thinner" but "richer" in oxygen.

**🛠️ Engineer version.**
- **Oxygen concentration (% O₂ by volume)** is the main lever on flammability. Many materials that don't burn at 21% will burn at
  higher oxygen.
- **Total pressure (kPa)** also matters: lower pressure means fewer oxygen molecules per volume, which can make some flames weaker,
  but raised oxygen fraction can more than compensate.
- **The exploration atmosphere** in StarryNight is **34% O₂ at 56.5 kPa (8.2 psia)** (`backend/engine.py → MISSIONS`).
  *Background:* NASA studied this atmosphere so astronauts can go on spacewalks with less pre-breathing time; the trade-off is a
  higher fire risk, which is exactly what this challenge is about.
- **ISS cabin air**: about **21% O₂ at 101.3 kPa** (sea-level pressure).

## 1.4 Gravity on the Moon and Mars

**🧒 Simple version.** The Moon has about 1/6 of Earth's gravity and Mars about 3/8. That's enough for some hot air to rise, but
only a little. Scientists suspect this "in-between" gravity can make some materials *more* flammable than on Earth or in orbit.

**🛠️ Engineer version.**
- StarryNight uses **0.166 g (Moon)** and **0.38 g (Mars)**.
- Partial gravity gives weak buoyant flow: enough to feed a flame, not enough to cool it as strongly as on Earth.
- **Data reality:** every combustion test in NASA's PSI repository ran at **~0 g** (ISS or the uncrewed Cygnus spacecraft).
  Nothing in orbit runs at partial gravity. So for Moon and Mars, StarryNight correctly says *there is no test at this gravity*.

## 1.5 How NASA approves materials today

**🧒 Simple version.** Before a material goes on a spacecraft, NASA sets a small strip of it on fire **on Earth**, holding it
upright, to see if the flame climbs. If it doesn't climb, the material passes.

**🛠️ Engineer version.**
- The standard is **NASA-STD-6001, Test 1 (upward flame propagation)**. It runs in normal gravity, in a chosen atmosphere.
- Because it's done in 1 g, it may not represent how a material behaves at ~0 g or at Moon/Mars gravity. BASS-II's own goal
  (on its PSI page) was to "bridge the gap" between Test 1 and real flammability in microgravity.
- Test 1 results live in NASA's **MAPTIS** database, which is **not** part of our data. The Earth row on the Gaps map says so.

## 1.6 The words you'll see for outcomes

| Word in StarryNight | Meaning |
|---|---|
| **Burned** | The flame kept going (or NASA's notes imply it did) |
| **Went out / Extinction** | The flame died by itself |
| **Blowoff** | The airflow was too strong and blew the flame away |
| **No ignition** | It never lit |
| **Not sustained** | It lit but didn't keep burning |
| **Disruption** (droplets, FLEX) | The burning droplet broke apart; NASA's own word for how the test ended |
| **SE / FT** (gas flames, ACME CFI-G) | **SE** = self-extinguished; **FT** = flow terminated: the flame was still burning when the fuel flow was stopped |

## 1.7 Three kinds of fire experiments (and why we keep them apart)

**🧒 Simple version.** NASA burned three different kinds of things in space: **solid materials** (like a piece of fabric), **tiny
balls of liquid fuel** (droplets), and **gas coming out of a small burner** (like a mini gas stove). They behave differently, so we
never mix them up. Only the solid ones can answer "will this cabin material burn?". The other two tell us how *flames in general*
behave at a given oxygen and pressure.

**🛠️ Engineer version.**
| Kind | Investigations | Used for |
|---|---|---|
| Solid materials | BASS, BASS-II, SAFFIRE I–III | The verdict (evidence table) |
| Liquid droplets | FLEX, CFI (and FLEX-2 matrix) | "Closest space flames at this oxygen and pressure" (never changes the verdict) |
| Gas-jet flames | ACME CFI-G, ACME Flame Design (and ACME logs) | Same as droplets |
| Smoke / soot | SAME, SAME-R, SPICE | Smoke tables per material; soot context |

## 1.8 Real accidents that show why this matters (from the challenge resources)

- **Apollo 1 (1967):** a fire in a cabin of 100% oxygen during a ground test; the crew died from toxic gases. NASA then restricted
  flammable materials in spacecraft.
- **Mir (1997):** an oxygen generator caught fire on a space station and filled it with smoke.
- **Apollo 13 (1970):** an oxygen tank exploded on the way to the Moon.

These are on the Home page under "Why it matters", each linked to its NASA page.
