import * as Tabs from "@radix-ui/react-tabs";
import * as Tooltip from "@radix-ui/react-tooltip";
import { ArrowRight, ArrowUpRight, Info, MessageSquareText, Orbit, TriangleAlert } from "lucide-react";
import { motion } from "motion/react";
import { useMemo, useState, type CSSProperties, type ReactNode } from "react";
import { Link, useNavigate } from "react-router-dom";
import { AtmosphereMap, type AtmPoint } from "../components/charts/AtmosphereMap";
import { SourceChip } from "../components/SourceChip";
import { cx, ErrorState, Skeleton } from "../components/ui";
import { WhyItMatters } from "../components/WhyItMatters";
import { useQuery } from "../lib/api";
import { client, PSI_PORTAL } from "../lib/client";
import type { AtmosphereTest, CsvRow, MissionKey, Overview, ScenarioResult } from "../lib/types";

/* Home: a narrative (problem -> evidence -> research base -> how to use it -> missions -> mission statement).
   Every number comes from NASA's PSI combustion repository via /api/*. Photos: NASA, public domain, credited. */

const MISSIONS: MissionKey[] = ["iss", "exploration", "moon", "mars"];
const num = (v: string | number | null | undefined) => { const n = Number(v); return v === "" || v == null || !Number.isFinite(n) ? null : n; };
const fade = { initial: { opacity: 0, y: 14 }, whileInView: { opacity: 1, y: 0 }, viewport: { once: true, margin: "-60px" }, transition: { duration: 0.5, ease: "easeOut" } } as const;

function SectionHead({ n, kicker, title, children }: { n: string; kicker: string; title: string; children?: ReactNode }) {
  return (
    <motion.header {...fade} className="max-w-3xl space-y-3">
      <p className="kicker">{n} · {kicker}</p>
      <h2 className="text-[1.9rem] font-semibold leading-tight tracking-tight text-ink sm:text-[2.3rem]">{title}</h2>
      {children && <p className="text-lg text-muted">{children}</p>}
    </motion.header>
  );
}

function Readout({ label, value, unit, hint, tone }: { label: string; value: ReactNode; unit?: string; hint: string; tone?: "flare" | "danger" }) {
  return (
    <Tooltip.Root delayDuration={150}>
      <Tooltip.Trigger asChild>
        <div tabIndex={0} className="cursor-help border-l border-line pl-4 outline-none focus-visible:border-signal">
          <p className="flex items-center gap-1.5 font-mono text-[0.7rem] uppercase tracking-[0.16em] text-faint">{label}<Info size={11} className="opacity-60" aria-hidden /></p>
          <p className={cx("readout mt-1 text-[1.9rem] font-medium leading-none", tone === "flare" ? "text-flare" : tone === "danger" ? "text-danger" : "text-ink")}>
            {value}{unit && <span className="ml-1 text-base text-muted">{unit}</span>}
          </p>
        </div>
      </Tooltip.Trigger>
      <Tooltip.Portal>
        <Tooltip.Content sideOffset={8} className="z-50 max-w-xs rounded-lg border border-line bg-surface px-3 py-2 text-sm text-ink shadow-card">
          {hint}<Tooltip.Arrow className="fill-line" />
        </Tooltip.Content>
      </Tooltip.Portal>
    </Tooltip.Root>
  );
}

export default function HomePage() {
  const ov = useQuery("overview", client.overview);
  const st = useQuery("stats", client.stats);
  const ms = useQuery("missions", client.missions);
  const map = useQuery("map:all", () => client.map());
  const drops = useQuery("droplets", client.droplets);
  const gases = useQuery("gas-flames", client.gasFlames);
  const sc = {
    iss: useQuery<ScenarioResult>("home:iss", () => client.scenario({ material: "PMMA (acrylic)", mission: "iss" })),
    exploration: useQuery<ScenarioResult>("home:exploration", () => client.scenario({ material: "PMMA (acrylic)", mission: "exploration" })),
    moon: useQuery<ScenarioResult>("home:moon", () => client.scenario({ material: "PMMA (acrylic)", mission: "moon" })),
    mars: useQuery<ScenarioResult>("home:mars", () => client.scenario({ material: "PMMA (acrylic)", mission: "mars" })),
  };

  const points = useMemo<AtmPoint[]>(() => {
    const out: AtmPoint[] = [];
    for (const r of map.data ?? []) if (r.o2_pct != null) out.push({ id: r.test_id, kind: "solid", o2: r.o2_pct, p: 101.3, label: `${r.investigation} · ${r.material}`, outcome: r.outcome, url: r.psi_url });
    const add = (rows: CsvRow[] | null | undefined, kind: AtmPoint["kind"], name: (r: CsvRow) => string) => {
      for (const r of rows ?? []) {
        const o2 = num(r.o2_pct), p = num(r.pressure_kpa);
        if (o2 != null && p != null) out.push({ id: r.test_id, kind, o2, p, label: name(r), outcome: r.outcome_basis === "not_recorded" ? "" : r.outcome_class, url: r.psi_url });
      }
    };
    add(drops.data, "droplet", (r) => `FLEX droplet · ${r.fuel}`);
    add(gases.data, "gas", (r) => `${r.investigation} gas flame · ${r.fuel}`);
    return out;
  }, [map.data, drops.data, gases.data]);

  if (ov.error) return <ErrorState message={ov.error} onRetry={ov.reload} />;
  const k = (name: string) => ov.data?.kpis.find((x) => x.kpi === name)?.value ?? null;
  const mars = ms.data?.mars;
  const gas = (sc.exploration.data?.atmosphere_evidence ?? []).find((a) => a.kind === "gas flame");
  const chartReady = map.data && drops.data && gases.data;

  return (
    <Tooltip.Provider>
      <div className="space-y-28">
        <Hero tests={k("solid_flame_tests_total")} />

        {/* 01 · The problem */}
        <section aria-label="The problem" className="space-y-10">
          <SectionHead n="01" kicker="The problem" title="Habitats will breathe air NASA has never burned a cabin material in.">
            Moon and Mars habitats are planned at {mars ? `${mars.o2_pct}% oxygen and ${mars.pressure_kpa} kPa` : "high oxygen and low pressure"} so crews can
            suit up faster. Every solid material NASA burned in space ran in ordinary cabin air, at about zero gravity.
          </SectionHead>
          <motion.div {...fade} className="grid grid-cols-2 gap-6 lg:grid-cols-4">
            <Readout label="Solid tests in space" value={k("solid_flame_tests_total") ?? "…"} hint="Solid-material fire tests in NASA PSI: BASS, BASS-II and Saffire I-III." />
            <Readout label="Oxygen tested" value={k("o2_tested_min_pct") ? `${k("o2_tested_min_pct")}–${k("o2_tested_max_pct")}` : "…"} unit="%" hint="Range of oxygen in every solid-material test. Earth air is 21%." />
            <Readout label="Habitat plan" value={mars ? `${mars.o2_pct}` : "…"} unit={mars ? `% · ${mars.pressure_kpa} kPa` : undefined} tone="flare" hint="NASA's exploration atmosphere for Moon and Mars habitats (8.2 psia, 34% O2)." />
            <Readout label="Tests at Moon/Mars g" value="0" tone="danger" hint="Every combustion test in NASA PSI ran at about 0 g. None at Moon (0.166 g) or Mars (0.38 g) gravity." />
          </motion.div>
          <motion.figure {...fade} className="rounded-card border border-line bg-surface p-5 sm:p-7">
            <figcaption className="mb-5 flex flex-wrap items-end justify-between gap-3">
              <div>
                <p className="kicker">Evidence map</p>
                <p className="mt-1 text-h3 text-ink">Where NASA's space flames burned: oxygen vs pressure</p>
              </div>
              <p className="max-w-md text-sm text-muted">Each mark is one NASA test. Hover for its id and outcome. Click a legend chip to hide a series.</p>
            </figcaption>
            {chartReady ? <AtmosphereMap points={points} /> : <Skeleton className="h-[380px] w-full rounded-card" />}
            <div className="mt-5 flex flex-wrap items-center gap-x-6 gap-y-2 border-t border-line/60 pt-4 text-sm text-muted">
              {gas && <span>Closest space flame to habitat air: <b className="readout text-ink">{gas.o2_pct}% O₂ · {gas.pressure_kpa} kPa</b> ({gas.investigation} gas flame, not a cabin material)</span>}
              <SourceChip href={`${PSI_PORTAL}/PSI-25`} label="NASA PSI · BASS-II" />
              <SourceChip href={`${PSI_PORTAL}/PSI-69`} label="NASA PSI · FLEX" />
              <SourceChip href={`${PSI_PORTAL}/PSI-159`} label="NASA PSI · ACME" />
            </div>
          </motion.figure>
        </section>

        {/* 02 · Why it matters */}
        <section aria-label="Why it matters" className="space-y-10">
          <SectionHead n="02" kicker="Why it matters" title="In a sealed cabin, there is nowhere to run.">
            Three NASA accidents shaped spacecraft fire safety. Help from Earth is days away on the Moon and months away on Mars.
          </SectionHead>
          <motion.div {...fade}><WhyItMatters bare /></motion.div>
        </section>

        {/* 03 · The research base */}
        <section aria-label="The research base" className="space-y-10">
          <SectionHead n="03" kicker="The research base" title="Powered by real space research.">
            NASA's Physical Sciences Informatics repository holds {st.data?.investigations_total ?? 24} combustion investigations flown on the ISS and the
            Cygnus cargo spacecraft. StarryNight organizes and connects them.
          </SectionHead>
          <ResearchBase droplets={st.data?.droplet_flame_tests} gases={st.data?.gas_flame_tests} solids={k("solid_flame_tests_total")} />
        </section>

        {/* 04 · The experience */}
        <section aria-label="The experience" className="grid gap-12 lg:grid-cols-[1fr_1.05fr] lg:items-center">
          <div className="space-y-8">
            <SectionHead n="04" kicker="The experience" title="From a research question to meaningful insight." />
            <Steps />
          </div>
          <motion.div {...fade}><AskCard /></motion.div>
        </section>

        {/* 05 · Mission readout */}
        <section aria-label="Mission readout" className="space-y-10">
          <SectionHead n="05" kicker="Mission readout" title="What NASA's space data covers for each mission.">
            Solid tests counted when gravity matches, oxygen is within 2 points and pressure within 15 kPa.
          </SectionHead>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {MISSIONS.map((key) => <MissionCard key={key} mkey={key} ov={ov.data} r={sc[key as keyof typeof sc].data} />)}
          </div>
        </section>

        <Closing />
      </div>
    </Tooltip.Provider>
  );
}

/* ---------------- Hero ---------------- */
function Hero({ tests }: { tests: string | null }) {
  return (
    <section className="grid items-center gap-10 lg:min-h-[calc(100vh-7rem)] lg:grid-cols-[1.05fr_1fr]">
      <motion.div initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, ease: "easeOut" }} className="space-y-7">
        <p className="kicker">NASA Space Apps 2026 · Flame in Freefall</p>
        <h1 className="text-[2.6rem] font-semibold leading-[1.04] tracking-[-0.025em] text-ink sm:text-[3.6rem]">
          Fire behaves differently beyond Earth.
          <span className="block text-muted">We show what NASA has actually tested.</span>
        </h1>
        <p className="max-w-xl text-lg text-muted">
          StarryNight turns NASA's space combustion experiments into fire-safety answers for spacecraft, the ISS, and Moon and Mars bases.
          Every answer cites the NASA test behind it, and when no test covers a case, it says so.
        </p>
        <div className="flex flex-wrap gap-3">
          <Link to="/scenario" className="inline-flex h-12 items-center gap-2 rounded-full bg-flare px-6 font-semibold text-space no-underline hover:bg-flare/90 hover:no-underline">
            Check a scenario <ArrowRight size={18} aria-hidden />
          </Link>
          <Link to="/ask" className="inline-flex h-12 items-center gap-2 rounded-full border border-line px-6 font-medium text-ink no-underline hover:border-ink/40 hover:no-underline">
            <MessageSquareText size={18} aria-hidden /> Ask the analyst
          </Link>
        </div>
        <p className="flex flex-wrap items-center gap-x-4 gap-y-1 font-mono text-[0.75rem] text-faint">
          <span>{tests ?? "263"} solid-material space fire tests</span><span aria-hidden>•</span>
          <span>24 NASA investigations</span><span aria-hidden>•</span><span>every answer cited</span>
        </p>
      </motion.div>

      <motion.figure initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.9, delay: 0.15 }} className="relative">
        <div className="relative overflow-hidden rounded-[22px] border border-line bg-black">
          <img src="/img/flame-0g.jpg" alt="A candle flame in microgravity: a dim blue sphere around the wick instead of a tall teardrop."
            className="aspect-[4/5] w-full object-cover object-center" width={855} height={1326} />
          <span className="hud-cross" style={{ left: "50%", top: "50%" }} />
          <span className="hud-cross" style={{ left: "16%", top: "40%" }} /><span className="hud-cross" style={{ left: "86%", top: "16%" }} />
          <HudLabel style={{ left: "6%", top: "7%" }} title="Gravity" value="~0 g" />
          <HudLabel style={{ right: "6%", top: "28%" }} title="Shape" value="Sphere, no plume" align="right" />
          <HudLabel style={{ left: "6%", bottom: "22%" }} title="Oxygen supply" value="Diffusion only" />
          <svg className="pointer-events-none absolute inset-0 h-full w-full" aria-hidden>
            <line x1="27%" y1="12%" x2="46%" y2="44%" stroke="rgb(var(--ink) / 0.4)" strokeDasharray="3 4" />
            <line x1="74%" y1="33%" x2="62%" y2="46%" stroke="rgb(var(--ink) / 0.4)" strokeDasharray="3 4" />
          </svg>
          <div className="absolute bottom-4 right-4 w-[30%] overflow-hidden rounded-xl border border-line/80 bg-black">
            <img src="/img/flame-1g.jpg" alt="The same candle on Earth: a tall yellow teardrop flame." className="aspect-[3/4] w-full object-cover" width={816} height={1326} />
            <p className="absolute left-2 top-2 rounded-full bg-black/70 px-2 py-0.5 font-mono text-[0.65rem] text-ink">1 g · Earth</p>
          </div>
        </div>
        <figcaption className="mt-3 flex justify-between gap-3 font-mono text-[0.7rem] text-faint">
          <span>Candle flame in microgravity vs on Earth</span><span>NASA Glenn · C-1998-485</span>
        </figcaption>
      </motion.figure>
    </section>
  );
}

function HudLabel({ title, value, style, align }: { title: string; value: string; style: CSSProperties; align?: "right" }) {
  return (
    <div className={cx("absolute rounded-lg border border-ink/15 bg-black/60 px-3 py-2", align === "right" && "text-right")} style={style}>
      <p className="font-mono text-[0.62rem] uppercase tracking-[0.18em] text-muted">{title}</p>
      <p className="font-mono text-sm text-ink">{value}</p>
    </div>
  );
}

/* ---------------- Research base (Radix tabs) ---------------- */
function ResearchBase({ droplets, gases, solids }: { droplets?: number; gases?: number; solids: string | null }) {
  const items = [
    { v: "saffire", tab: "Solid materials", img: "/img/saffire-cygnus.jpg", credit: "Saffire-II stowed in the Cygnus OA-7 cargo vehicle · NASA ISS051E039882",
      title: "BASS, BASS-II and Saffire", stat: solids ?? "263", unit: "solid tests", url: `${PSI_PORTAL}/PSI-25`,
      text: "How cabin materials ignite, spread and go out at about 0 g. Saffire burned large samples inside uncrewed Cygnus vehicles after they left the ISS; BASS and BASS-II burned small samples on the station.",
      tag: "Pressure not recorded · cabin air assumed", warn: true },
    { v: "acme", tab: "Gas flames", img: "/img/acme-chamber.jpg", credit: "ACME chamber insert at NASA Glenn · GRC-2016-C-05051",
      title: "ACME (Advanced Combustion via Microgravity Experiments)", stat: gases != null ? String(gases) : "…", unit: "gas flame tests", url: `${PSI_PORTAL}/PSI-159`,
      text: "Gas-jet flames in the ISS Combustion Integrated Rack, across a range of oxygen and pressure. They come closest to the habitat atmosphere, but they burn gas, not cabin materials.",
      tag: "Measured oxygen and pressure", warn: false },
    { v: "flex", tab: "Fuel droplets", img: "/img/candle-shuttle.jpg", credit: "Candle Flames in Microgravity, Space Shuttle STS-50 · NASA",
      title: "FLEX (Flame Extinguishment Experiment)", stat: droplets != null ? String(droplets) : "…", unit: "droplet flame tests", url: `${PSI_PORTAL}/PSI-69`,
      text: "Burning fuel droplets in different oxygen, pressure and diluent mixes, to learn how gases such as CO₂ and helium put flames out. The photo shows the same spherical flame shape in an earlier Shuttle experiment.",
      tag: "Suppression research", warn: false },
  ];
  return (
    <Tabs.Root defaultValue="saffire" className="space-y-6">
      <Tabs.List aria-label="NASA investigation families" className="flex flex-wrap gap-2">
        {items.map((i) => (
          <Tabs.Trigger key={i.v} value={i.v}
            className="rounded-full border border-line px-4 py-2 text-sm text-muted transition-colors hover:text-ink data-[state=active]:border-ink/30 data-[state=active]:bg-ink/[0.07] data-[state=active]:text-ink">
            {i.tab}
          </Tabs.Trigger>
        ))}
      </Tabs.List>
      {items.map((i) => (
        <Tabs.Content key={i.v} value={i.v} className="outline-none">
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.35 }}
            className="grid overflow-hidden rounded-card border border-line bg-surface lg:grid-cols-[1.15fr_1fr]">
            <figure className="relative min-h-[280px] bg-black">
              <img src={i.img} alt={i.credit} className="absolute inset-0 h-full w-full object-cover opacity-90" loading="lazy" />
              <figcaption className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/85 to-transparent px-4 pb-3 pt-10 font-mono text-[0.68rem] text-ink/80">{i.credit}</figcaption>
            </figure>
            <div className="flex flex-col gap-5 p-6 sm:p-8">
              <p className="kicker">Investigation family</p>
              <h3 className="text-h2 text-ink">{i.title}</h3>
              <p className="text-muted">{i.text}</p>
              <p className="readout text-[2.6rem] leading-none text-ink">{i.stat}<span className="ml-2 font-sans text-base text-muted">{i.unit}</span></p>
              <span className={cx("inline-flex w-fit items-center gap-2 rounded-full px-3 py-1 text-sm", i.warn ? "bg-caution/10 text-caution" : "bg-signal/10 text-signal")}>
                {i.warn ? <TriangleAlert size={14} aria-hidden /> : <Info size={14} aria-hidden />} {i.tag}
              </span>
              <div className="mt-auto flex flex-wrap items-center gap-3 pt-2">
                <Link to="/investigations" className="inline-flex items-center gap-1 text-sm">Open the profiles <ArrowRight size={14} aria-hidden /></Link>
                <SourceChip href={i.url} label="NASA PSI page" />
              </div>
            </div>
          </motion.div>
        </Tabs.Content>
      ))}
    </Tabs.Root>
  );
}

/* ---------------- Steps (pitch deck: "from a research question to meaningful insights") ---------------- */
const STEPS = [
  { t: "Build a scenario", d: "Pick a material and a place, or describe it in your own words.", to: "/scenario" },
  { t: "Discover relevant NASA experiments", d: "All 24 investigations ranked for your habitat, with reasons.", to: "/rank" },
  { t: "Compare similarities and differences", d: "Fuels, oxygen, air flow, sensors, what varied.", to: "/investigations" },
  { t: "Explore where research stops", d: "Gravity × oxygen × pressure cells never tested.", to: "/gaps" },
  { t: "Ask questions, get cited answers", d: "An analyst that only speaks from NASA evidence.", to: "/ask" },
];
function Steps() {
  const [active, setActive] = useState(0);
  return (
    <ol className="relative space-y-1 border-l border-line pl-6">
      {STEPS.map((s, i) => (
        <li key={s.t} className="relative" onMouseEnter={() => setActive(i)} onFocus={() => setActive(i)}>
          <span className={cx("absolute -left-[29px] top-[18px] h-[9px] w-[9px] rounded-full border transition-colors",
            i === active ? "border-flare bg-flare" : "border-line bg-space")} aria-hidden />
          <Link to={s.to} className="group block rounded-lg px-3 py-3 no-underline hover:bg-raised/60 hover:no-underline">
            <p className="flex items-center gap-3"><span className="font-mono text-xs text-faint">0{i + 1}</span>
              <span className={cx("font-medium", i === active ? "text-ink" : "text-ink/80")}>{s.t}</span>
              <ArrowUpRight size={15} className="text-faint opacity-0 transition-opacity group-hover:opacity-100" aria-hidden /></p>
            <p className="ml-8 mt-0.5 text-sm text-muted">{s.d}</p>
          </Link>
        </li>
      ))}
    </ol>
  );
}

/* ---------------- Ask card (live) ---------------- */
function AskCard() {
  const [q, setQ] = useState("");
  const nav = useNavigate();
  const go = (text: string) => { const t = text.trim(); if (t) nav(`/ask?q=${encodeURIComponent(t)}`); };
  const examples = ["Would Nomex burn at 34% oxygen and 56.5 kPa on the Moon?", "Which investigations matter most for a Mars base?", "How do SAME and SAME-R differ?"];
  return (
    <div className="rounded-[20px] border border-line bg-surface p-2 shadow-card">
      <div className="flex items-center justify-between gap-3 border-b border-line/70 px-4 py-3">
        <p className="flex items-center gap-2 text-sm font-medium text-ink"><MessageSquareText size={16} className="text-signal" aria-hidden /> Ask the analyst</p>
        <span className="font-mono text-[0.68rem] text-faint">NASA PSI evidence only · cited [E#]</span>
      </div>
      <form className="space-y-3 p-4" onSubmit={(e) => { e.preventDefault(); go(q); }}>
        <label htmlFor="home-ask" className="text-sm text-muted">Your question, or a scenario in your own words (English or Arabic)</label>
        <textarea id="home-ask" rows={3} maxLength={1000} value={q} onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); go(q); } }}
          placeholder="e.g. I'm designing a Moon base at 34% oxygen. Would Nomex seat covers burn?"
          className="w-full resize-none rounded-xl border border-line bg-raised/60 px-4 py-3 text-ink placeholder:text-faint focus:border-signal/60 focus:outline-none" />
        <div className="flex items-center justify-between gap-3">
          <p className="text-xs text-faint">Verdicts come from fixed rules, never from the AI.</p>
          <button type="submit" disabled={!q.trim()} className="inline-flex h-10 items-center gap-2 rounded-full bg-flare px-5 font-semibold text-space disabled:opacity-40">Ask <ArrowRight size={16} aria-hidden /></button>
        </div>
      </form>
      <div className="space-y-1 border-t border-line/70 p-4">
        <p className="font-mono text-[0.68rem] uppercase tracking-[0.16em] text-faint">Try</p>
        {examples.map((e) => (
          <button key={e} type="button" onClick={() => go(e)} className="flex w-full items-center justify-between gap-3 rounded-lg px-2 py-2 text-left text-sm text-ink/90 hover:bg-raised">
            {e}<ArrowUpRight size={14} className="shrink-0 text-faint" aria-hidden />
          </button>
        ))}
      </div>
    </div>
  );
}

/* ---------------- Mission card ---------------- */
function MissionCard({ mkey, ov, r }: { mkey: MissionKey; ov?: Overview | null; r?: ScenarioResult | null }) {
  const cov = ov?.mission_coverage.find((c) => c.mission.toLowerCase().startsWith(mkey === "moon" ? "lunar" : mkey === "iss" ? "iss" : mkey));
  const n = Number(cov?.space_solid_tests_near ?? 0);
  const g: AtmosphereTest | undefined = (r?.atmosphere_evidence ?? []).find((a) => a.kind === "gas flame");
  const grav = r?.scenario.gravity_g ?? 0;
  return (
    <Link to={`/scenario?mission=${mkey}`} className="group flex flex-col gap-4 rounded-card border border-line bg-surface p-5 no-underline transition-colors hover:border-ink/30 hover:no-underline">
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="flex items-center gap-1.5 font-mono text-[0.68rem] uppercase tracking-[0.16em] text-faint"><Orbit size={12} aria-hidden /> {grav > 0.01 ? `${grav} g` : "microgravity"}</p>
          <p className="mt-1 text-h3 text-ink">{cov?.mission ?? mkey}</p>
        </div>
        <span className="grid h-8 w-8 shrink-0 place-items-center rounded-full border border-line text-muted transition-colors group-hover:border-ink/40 group-hover:text-ink"><ArrowUpRight size={15} aria-hidden /></span>
      </div>
      <dl className="grid grid-cols-2 gap-2 rounded-lg bg-raised/50 p-3 font-mono text-sm">
        <div><dt className="text-[0.65rem] uppercase tracking-[0.14em] text-faint">O₂</dt><dd className="text-ink">{cov?.o2_pct ?? "…"}%</dd></div>
        <div><dt className="text-[0.65rem] uppercase tracking-[0.14em] text-faint">Pressure</dt><dd className="text-ink">{cov?.pressure_kpa ?? "…"} kPa</dd></div>
      </dl>
      {!r || !cov ? <Skeleton className="h-12" /> : n ? (
        <p className="mt-auto text-sm text-muted"><b className="readout text-[1.6rem] font-medium text-ink">{n}</b> solid tests nearby · {cov.space_tests_near_observed_outcome} with outcome written by NASA</p>
      ) : (
        <div className="mt-auto space-y-2">
          <span className="inline-flex items-center gap-1.5 rounded-full bg-caution/10 px-2.5 py-1 text-xs text-caution">
            <TriangleAlert size={13} aria-hidden /> {grav > 0.01 ? "No space test at this gravity" : "No solid test at this atmosphere"}
          </span>
          {g && <p className="text-xs text-muted">Closest space flame: <span className="readout text-ink">{g.o2_pct}% · {g.pressure_kpa} kPa</span> (ACME gas, ~0 g)</p>}
        </div>
      )}
    </Link>
  );
}

/* ---------------- Closing band ---------------- */
function Closing() {
  return (
    <motion.section {...fade} className="relative overflow-hidden rounded-[24px] border border-line">
      <img src="/img/earth-limb-iss.jpg" alt="Earth's limb and the station's robotic arm, photographed from the International Space Station." loading="lazy"
        className="absolute inset-0 h-full w-full object-cover" />
      <div className="absolute inset-0 bg-gradient-to-r from-space via-space/85 to-space/20" aria-hidden />
      <div className="relative max-w-2xl space-y-6 px-6 py-16 sm:px-12 sm:py-20">
        <p className="kicker">The mission</p>
        <p className="text-[2rem] font-semibold leading-tight tracking-tight text-ink sm:text-[2.6rem]">
          Better research.<br />Better understanding.<br /><span className="text-flare">A safer future beyond Earth.</span>
        </p>
        <div className="flex flex-wrap gap-3">
          <Link to="/scenario" className="inline-flex h-11 items-center gap-2 rounded-full bg-flare px-5 font-semibold text-space no-underline hover:no-underline">Check a scenario <ArrowRight size={16} aria-hidden /></Link>
          <Link to="/about" className="inline-flex h-11 items-center rounded-full border border-ink/25 px-5 text-ink no-underline hover:no-underline">About the project</Link>
        </div>
        <p className="font-mono text-[0.68rem] text-faint">Photo: NASA, Expedition 40 · ISS040-E-062704</p>
      </div>
    </motion.section>
  );
}
