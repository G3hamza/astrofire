import { CircleHelp, Droplets, Gauge, Orbit, Wind } from "lucide-react";
import type { AtmosphereTest, GravityBounds, WhyUntested } from "../lib/types";
import { Link } from "react-router-dom";
import { FileRowChip, SourceChip } from "./SourceChip";
import { Card, CardHeader } from "./ui";

const WHY_ICON = { gravity: Orbit, oxygen: Wind, pressure: Gauge } as const;
const WHY_TITLE = { gravity: "Gravity", oxygen: "Oxygen", pressure: "Pressure" } as const;

/** Explains WHY a condition was never tested (physics + operations), each reason with a NASA source. */
export function WhyUntestedCard({ items }: { items: WhyUntested[] }) {
  if (!items.length) return null;
  return (
    <Card>
      <CardHeader eyebrow="Why this gap exists" title="Why NASA hasn't run this test in space" right={<CircleHelp className="text-muted" size={22} aria-hidden />} />
      <ul className="divide-y divide-line/50">
        {items.map((w) => {
          const Icon = WHY_ICON[w.topic];
          return (
            <li key={w.topic} className="flex gap-4 px-5 py-4">
              <Icon size={20} className="mt-0.5 shrink-0 text-signal" aria-hidden />
              <div className="space-y-2">
                <p className="text-ink/90"><b className="text-ink">{WHY_TITLE[w.topic]}.</b> {w.text}</p>
                <SourceChip href={w.source_url} />
              </div>
            </li>
          );
        })}
      </ul>
    </Card>
  );
}

/** Closest FLEX/CFI droplet flames and ACME gas flames at this oxygen + pressure. Different experiment kinds:
    shown apart, never counted as material evidence, never change the verdict. */
export function AtmosphereEvidenceCard({ rows }: { rows: AtmosphereTest[] }) {
  if (!rows.length) return null;
  return (
    <Card>
      <CardHeader eyebrow="Same atmosphere, different fuel (FLEX · CFI · ACME)"
        title="Closest space flames at this oxygen and pressure"
        right={<Droplets className="text-signal" size={22} aria-hidden />} />
      <div className="space-y-3 p-5">
        <p className="text-sm text-muted">
          These are fuel droplets and gas-jet flames burned on the ISS (~0 g). They show how flames behaved at this
          oxygen and pressure, not whether a cabin material burns. <Link to="/experiments#flex">About these experiments</Link>
        </p>
        <ul className="divide-y divide-line/50 rounded-lg border border-line">
          {rows.map((t) => (
            <li key={t.test_id} className="flex flex-wrap items-center gap-x-4 gap-y-1 px-4 py-3 text-sm">
              <span className="w-20 font-mono text-ink">{t.test_id}</span>
              <span className="text-ink">{t.kind === "gas flame" ? t.fuel : `${t.fuel} droplet${t.droplet_initial_diameter_mm ? ` (${t.droplet_initial_diameter_mm} mm)` : ""}`}</span>
              <span className="tnum text-ink"><b>{t.o2_pct}% O₂</b> · <b>{t.pressure_kpa} kPa</b>{t.kind === "gas flame" ? " (approx.)" : " (measured)"}</span>
              <span className="text-muted">{t.outcome_basis === "not_recorded"
                ? <>{t.investigation}: <b className="text-ink">NASA did not record how the test ended</b></>
                : t.kind === "gas flame"
                  ? <>{t.investigation}: <b className="text-ink">{t.test_end_raw === "SE" ? "self-extinguished" : t.test_end_raw === "FT" ? "burned until flow stopped" : t.outcome.toLowerCase()}</b>{t.burn_time_s != null ? ` after ${t.burn_time_s} s` : ""}</>
                  : <>test ended by: <b className="text-ink">{t.outcome === "Burned" ? "completion" : t.outcome.toLowerCase()}</b>{t.burn_time_s != null ? ` after ${t.burn_time_s} s` : ""}</>}</span>
              <span className="ml-auto flex gap-2"><SourceChip href={t.psi_url} /><FileRowChip file={t.source_file} row={t.source_row} /></span>
            </li>
          ))}
        </ul>
        <p className="text-[12px] text-faint">"Test ended by" uses NASA's own words from the FLEX table: extinction, disruption, or completion. The CFI table has no outcome column. ACME codes: SE = self-extinguished, FT = flow terminated while burning.</p>
      </div>
    </Card>
  );
}


/** Moon / Mars: what PSI shows at the two ends of the gravity range (0 g in orbit, NASA's own 1 g comparison in Saffire-II).
    Never a value for the requested gravity; says plainly when the ends were measured at a different atmosphere. */
export function GravityBoundsCard({ b }: { b: GravityBounds | null | undefined }) {
  if (!b) return null;
  const lo = b.lower_bound, up = b.upper_bound;
  return (
    <Card>
      <CardHeader eyebrow={`Bounding ${b.requested_gravity_g} g between 0 g and 1 g`} title="What NASA measured at each end of the gravity range"
        right={<Orbit className="text-muted" size={22} aria-hidden />} />
      <div className="grid gap-4 px-5 py-4 text-sm md:grid-cols-2">
        <div className="space-y-1">
          <p className="eyebrow">0 g: microgravity (ISS / Cygnus)</p>
          {lo.tests ? <p>{lo.tests} tests · outcomes {Object.entries(lo.outcomes).map(([k, v]) => `${k} ${v}`).join(", ")}
            {lo.o2_range ? ` · O₂ ${lo.o2_range[0]}–${lo.o2_range[1]}%` : ""} · {lo.pressure}</p> : <p className="text-muted">{lo.note}</p>}
          {lo.outcome_basis && <p className="text-xs text-muted">Outcome basis: {Object.entries(lo.outcome_basis).map(([k, v]) => `${k} ${v}`).join(", ")}</p>}
        </div>
        <div className="space-y-1">
          <p className="eyebrow">1 g: NASA's normal-gravity comparison (Saffire-II)</p>
          {up.pairs.length ? <ul className="space-y-1">{up.pairs.map((p) => (
            <li key={p.test_id}>{p.material} at {p.o2_pct}% O₂: burned {p.microgravity_burn_length} in 0 g vs {p.one_g_burn_length} at 1 g{" "}
              <FileRowChip file={p.source_file} row={p.source_row} /></li>))}</ul> : <p className="text-muted">{up.note}</p>}
        </div>
      </div>
      <div className="space-y-2 border-t border-line/60 px-5 py-4 text-sm">
        <p className={b.bounds_cover_request ? "text-ink" : "text-caution"}>{b.applies}</p>
        <p className="text-muted">{b.partial_gravity_mimic.text} <SourceChip href={b.partial_gravity_mimic.url} label={b.partial_gravity_mimic.investigation} /></p>
        <p className="text-xs text-muted">{b.basis}</p>
      </div>
    </Card>
  );
}

/** Partial-gravity data the challenge says will come to PSI. */
export function ComingNextCard({ items }: { items: { name: string; status: string }[] }) {
  if (!items.length) return null;
  return (
    <Card>
      <CardHeader eyebrow="Coming next to PSI" title="Partial-gravity fire data on the way" />
      <ul className="space-y-1 px-5 py-4 text-sm">
        {items.map((i) => <li key={i.name}><b className="text-ink">{i.name}</b> · {i.status}</li>)}
        <li className="text-xs text-muted">Not in PSI yet, so AstroFire does not use it as evidence. Background: NASA Combustion Science{" "}
          <SourceChip href="https://www.nasa.gov/glenn/glenn-expertise-space-exploration/physical-sciences-program/combustion-science/" label="nasa.gov" /></li>
      </ul>
    </Card>
  );
}
