import { ArrowRight, Droplets, Flame, Grid3x3, MessageSquareText, Orbit, Rocket, GitCompare } from "lucide-react";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { KpiTile } from "../components/KpiTile";
import { SourceChip } from "../components/SourceChip";
import { cx, ErrorState, Skeleton } from "../components/ui";
import { WhyItMatters } from "../components/WhyItMatters";
import { useQuery } from "../lib/api";
import { client, PSI_PORTAL } from "../lib/client";
import type { AtmosphereTest, MissionKey, ScenarioResult } from "../lib/types";

/* Home: every number comes from NASA's PSI combustion repository via /api/*. No paper data, no invented values.
   Instead of showing "0 tests" for the habitat atmosphere, it shows the closest real space data that exists. */

const MISSIONS: MissionKey[] = ["iss", "exploration", "moon", "mars"];
const END = (t: AtmosphereTest) => t.outcome_basis === "not_recorded" ? "outcome not recorded"
  : t.kind === "gas flame" ? ({ SE: "self-extinguished", FT: "burned until flow stopped" }[t.test_end_raw ?? ""] ?? t.outcome.toLowerCase())
  : `ended by ${t.outcome === "Burned" ? "completion" : t.outcome.toLowerCase()}`;

export default function HomePage() {
  const ov = useQuery("overview", client.overview);
  const st = useQuery("stats", client.stats);
  const ms = useQuery("missions", client.missions);
  const sc = {
    iss: useQuery<ScenarioResult>("home:iss", () => client.scenario({ material: "PMMA (acrylic)", mission: "iss" })),
    exploration: useQuery<ScenarioResult>("home:exploration", () => client.scenario({ material: "PMMA (acrylic)", mission: "exploration" })),
    moon: useQuery<ScenarioResult>("home:moon", () => client.scenario({ material: "PMMA (acrylic)", mission: "moon" })),
    mars: useQuery<ScenarioResult>("home:mars", () => client.scenario({ material: "PMMA (acrylic)", mission: "mars" })),
  };

  if (ov.error) return <ErrorState message={ov.error} onRetry={ov.reload} />;

  const k = (name: string) => ov.data?.kpis.find((x) => x.kpi === name)?.value ?? null;
  const mars = ms.data?.mars; const moon = ms.data?.moon;
  const atm = sc.exploration.data?.atmosphere_evidence ?? [];
  const gas = atm.find((a) => a.kind === "gas flame");
  const drop = atm.find((a) => a.kind === "droplet flame");
  const loading = ov.loading || !ov.data;

  return (
    <div className="space-y-10">
      {/* ---------- Hero ---------- */}
      <section className="relative overflow-hidden rounded-card border border-line bg-surface/80 px-6 py-9 shadow-card sm:px-10">
        <div className="grid-bg pointer-events-none absolute inset-0 opacity-40 [mask-image:radial-gradient(ellipse_at_top_right,black,transparent_70%)]" aria-hidden />
        <div className="relative grid items-center gap-8 lg:grid-cols-[auto_1fr]">
          <div className="text-center lg:text-left">
            {loading ? <Skeleton className="h-24 w-40" /> : (
              <p className="tnum text-[5.5rem] font-extrabold leading-none tracking-tighter text-signal">{k("solid_flame_tests_total")}</p>
            )}
            <p className="eyebrow mt-2">solid-material fire tests in space</p>
          </div>
          <div className="space-y-4">
            <p className="eyebrow text-burn">The gap</p>
            <h1 className="text-h1 sm:text-[2.4rem] sm:leading-tight">
              All of them ran at <span className="text-signal">{k("o2_tested_min_pct") ?? "…"}–{k("o2_tested_max_pct") ?? "…"}% oxygen</span> and ~0 g.
              Moon and Mars habitats will run at <span className="text-burn">{mars ? `${mars.o2_pct}% oxygen and ${mars.pressure_kpa} kPa` : "…"}</span>.
            </h1>
            <p className="max-w-3xl text-lg text-muted">
              No solid cabin material in NASA's PSI combustion data has been burned at that atmosphere or at Moon / Mars gravity.
              {gas && <> The closest space flames are ACME gas flames on the ISS at <b className="tnum text-ink">{gas.o2_pct}% O₂ and {gas.pressure_kpa} kPa</b>.</>}
            </p>
            <div className="flex flex-wrap gap-2">
              <SourceChip href={`${PSI_PORTAL}/PSI-25`} label="NASA PSI · BASS-II" />
              <SourceChip href={`${PSI_PORTAL}/PSI-159`} label="NASA PSI · ACME CFI-G" />
              <SourceChip href="https://psi.nasa.gov/physci/repo/search?q=combustion" label="NASA PSI · combustion repository" />
            </div>
          </div>
        </div>
        <div className="relative mt-7 flex flex-wrap gap-3">
          <CTA to="/scenario" primary Icon={Rocket}>Check a scenario</CTA>
          <CTA to="/compare" Icon={GitCompare}>Compare missions</CTA>
          <CTA to="/gaps" Icon={Grid3x3}>See the gaps</CTA>
        </div>
        <AskBox />
      </section>

      {/* ---------- Closest real space data to habitat air ---------- */}
      {(gas || drop) && (
        <section aria-label="Closest real space data" className="grid gap-4 md:grid-cols-2">
          {gas && <ClosestCard Icon={Flame} title="Closest gas flames" t={gas} what="gas-jet flames burned on the ISS" />}
          {drop && <ClosestCard Icon={Droplets} title="Closest droplet flames" t={drop} what="fuel droplets burned on the ISS" />}
        </section>
      )}

      {/* ---------- KPIs ---------- */}
      <section aria-label="Key numbers" className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
        <KpiTile loading={loading} label="Solid fire tests in space" value={k("solid_flame_tests_total")} unit="tests" caption="BASS, BASS-II, SAFFIRE I–III" />
        <KpiTile loading={loading} label="Outcome written by NASA" value={k("pct_outcomes_observed")} unit="%" caption={`${k("pct_outcomes_inferred") ?? "…"}% inferred from notes`} />
        <KpiTile loading={loading} label="Oxygen in solid tests" value={k("o2_tested_min_pct") && `${k("o2_tested_min_pct")}–${k("o2_tested_max_pct")}`} unit="%" caption={mars ? `habitats plan ${mars.o2_pct}%` : undefined} />
        <KpiTile loading={!gas} tone="signal" label="Closest flame to habitat air" value={gas ? `${gas.o2_pct}%` : null} unit={gas ? `· ${gas.pressure_kpa} kPa` : undefined} caption="ACME gas flame, ISS" />
        <KpiTile loading={st.loading} label="Space flames in PSI" value={st.data ? st.data.droplet_flame_tests + st.data.gas_flame_tests : null} unit="tests" caption={st.data ? `${st.data.droplet_flame_tests} droplet · ${st.data.gas_flame_tests} gas` : undefined} />
      </section>

      {/* ---------- Mission coverage ---------- */}
      <section aria-labelledby="cov-h" className="space-y-4">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h2 id="cov-h" className="text-h2">What NASA's space data covers for each mission</h2>
          <p className="text-sm text-faint">Solid tests counted when gravity matches, O₂ within 2 points, pressure within 15 kPa</p>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {MISSIONS.map((key) => {
            const cov = ov.data?.mission_coverage.find((c) => c.mission.toLowerCase().startsWith(key === "moon" ? "lunar" : key === "iss" ? "iss" : key));
            const r = sc[key as keyof typeof sc].data;
            const n = Number(cov?.space_solid_tests_near ?? 0);
            const g = (r?.atmosphere_evidence ?? []).find((a) => a.kind === "gas flame");
            const partial = (r?.scenario.gravity_g ?? 0) > 0.01;
            return (
              <Link key={key} to={`/scenario?mission=${key}`}
                className={cx("group flex flex-col gap-3 rounded-card border bg-surface/90 p-5 no-underline shadow-card transition hover:no-underline",
                  n ? "border-line hover:border-signal/60" : "border-burn/40 hover:border-burn")}>
                <div className="flex items-center gap-2 text-muted"><Orbit size={16} aria-hidden /><span className="eyebrow">{partial ? `${r?.scenario.gravity_g} g` : "microgravity"}</span></div>
                <p className="text-h3 text-ink">{cov?.mission ?? key}</p>
                <p className="tnum text-sm text-muted">{cov?.o2_pct}% O₂ · {cov?.pressure_kpa} kPa</p>
                {!r || !cov ? <Skeleton className="h-12" /> : n ? (
                  <p className="tnum mt-auto text-h2 text-ink">{n}<span className="ml-2 text-base font-medium text-muted">solid tests nearby · {cov.space_tests_near_observed_outcome} with outcome written</span></p>
                ) : (
                  <div className="mt-auto space-y-1">
                    <p className="font-semibold text-burn">{partial ? "No space test at this gravity" : "No solid-material test at this atmosphere"}</p>
                    {g && <p className="tnum text-sm text-ink">Closest space flame: <b>{g.o2_pct}% O₂ · {g.pressure_kpa} kPa</b> <span className="text-muted">(ACME, ~0 g)</span></p>}
                  </div>
                )}
                <span className="flex items-center gap-1 text-sm text-signal">Check this mission <ArrowRight size={14} className="transition group-hover:translate-x-0.5" aria-hidden /></span>
              </Link>
            );
          })}
        </div>
        {moon && <p className="text-sm text-faint">Moon {moon.gravity_g} g and Mars {mars?.gravity_g} g: every combustion test in NASA's PSI repository ran at ~0 g.</p>}
      </section>

      <WhyItMatters />

      <p className="text-center text-lg text-muted">AstroFire answers <b className="text-ink">Will it burn? What proves it? How sure are we?</b> from NASA's own data, and says plainly where that data stops.</p>
    </div>
  );
}

function ClosestCard({ Icon, title, t, what }: { Icon: typeof Flame; title: string; t: AtmosphereTest; what: string }) {
  return (
    <div className="rounded-card border border-dashed border-signal/60 bg-signal/5 p-5">
      <p className="eyebrow flex items-center gap-2 text-signal"><Icon size={14} aria-hidden /> {title} to habitat air</p>
      <p className="mt-2 text-lg text-ink">
        <b className="tnum">{t.o2_pct}% O₂ at {t.pressure_kpa} kPa</b>: {t.investigation} {what} ({t.fuel}); {END(t)}
        {t.burn_time_s != null && t.outcome_basis !== "not_recorded" ? ` after ${t.burn_time_s} s` : ""}.
      </p>
      <div className="mt-3 flex flex-wrap items-center gap-2 text-sm text-faint">
        Not a cabin material: shows how flames behave at this oxygen and pressure. <SourceChip href={t.psi_url} label={`NASA PSI · ${t.test_id}`} />
      </div>
    </div>
  );
}

function CTA({ to, children, Icon, primary }: { to: string; children: string; Icon: typeof Rocket; primary?: boolean }) {
  return (
    <Link to={to} className={cx(
      "inline-flex h-11 items-center gap-2 rounded-lg px-5 text-base font-semibold no-underline transition hover:no-underline",
      primary ? "bg-signal text-space hover:bg-signal/90" : "border border-line bg-raised text-ink hover:border-signal/60",
    )}>
      <Icon size={18} aria-hidden /> {children}
    </Link>
  );
}


/** "Ask AstroFire" on Home: type a question (or a scenario in your own words) and get a cited answer on /ask. */
function AskBox() {
  const [q, setQ] = useState("");
  const nav = useNavigate();
  const go = (text: string) => { const t = text.trim(); if (t) nav(`/ask?q=${encodeURIComponent(t)}`); };
  const examples = ["Would Nomex burn at 30% oxygen and 71 kPa on the Moon?", "Which investigations matter most for a Mars base?"];
  return (
    <div className="relative mt-6 max-w-3xl space-y-2">
      <form className="flex flex-wrap gap-2 rounded-card border border-signal/40 bg-surface/90 p-2 shadow-glow" onSubmit={(e) => { e.preventDefault(); go(q); }}>
        <MessageSquareText size={20} className="ml-2 self-center text-signal" aria-hidden />
        <input aria-label="Ask AstroFire a question" maxLength={1000} value={q} onChange={(e) => setQ(e.target.value)}
          placeholder="Ask AstroFire anything, or describe a scenario in your own words…"
          className="min-w-0 flex-1 bg-transparent px-2 py-2 text-base text-ink placeholder:text-faint focus:outline-none" />
        <button type="submit" disabled={!q.trim()} className="rounded-lg bg-signal px-4 py-2 font-semibold text-space disabled:opacity-50">Ask</button>
      </form>
      <p className="text-sm text-muted">Try:{" "}
        {examples.map((e, i) => <span key={e}>{i > 0 && " · "}<button type="button" className="text-signal underline-offset-2 hover:underline" onClick={() => go(e)}>{e}</button></span>)}
      </p>
    </div>
  );
}
