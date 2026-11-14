import { Globe, MapPin, Moon, Orbit, Sparkles } from "lucide-react";
import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { SourceChip } from "../components/SourceChip";
import { Card, cx, ErrorState, Skeleton } from "../components/ui";
import { useQuery } from "../lib/api";
import { client, PSI_PORTAL } from "../lib/client";
import type { GapCell } from "../lib/types";

import { heroTitle, PageHero } from "../components/PageHero";
const GRAVITY_ROWS = [
  { g: 1.0, label: "Earth", sub: "1 g", Icon: Globe },
  { g: 0.38, label: "Mars", sub: "0.38 g", Icon: Sparkles },
  { g: 0.166, label: "Moon", sub: "0.166 g", Icon: Moon },
  { g: 0.0, label: "Orbit (ISS)", sub: "~0 g", Icon: Orbit },
];

const missionToKey = (name: string) =>
  name.startsWith("ISS") ? "iss" : name.startsWith("Explor") ? "exploration" : name.startsWith("Lunar") ? "moon" : "mars";

export default function GapsPage() {
  const q = useQuery("gaps", client.gaps);
  const [focus, setFocus] = useState<GapCell | null>(null);

  const { o2Bins, pressures, maxN, summary } = useMemo(() => {
    const d = q.data ?? [];
    const o2Bins = [...new Set(d.map((c) => c.o2_range))];
    const pressures = [...new Set(d.map((c) => c.pressure))];
    const space = d.filter((c) => c.gravity_g !== 1.0);
    return {
      o2Bins, pressures,
      maxN: Math.max(1, ...d.map((c) => c.space_tests)),
      summary: {
        tested: space.filter((c) => c.space_tests > 0).length, total: space.length, tests: space.reduce((a, c) => a + c.space_tests, 0),
        flameOnly: d.filter((c) => !c.space_tests && c.gravity_g === 0 && ((c.gas_flame_tests ?? 0) + (c.droplet_tests ?? 0)) > 0).length,
      },
    };
  }, [q.data]);

  if (q.error) return <ErrorState message={q.error} onRetry={q.reload} />;

  return (
    <div className="space-y-6">
      <PageHero photo="orion" variant="band">
        <div className="space-y-1">
          <p className="kicker">Gaps map</p>
          <h1 className={heroTitle}>Where NASA has tested, and where it never has</h1>
          <p className="max-w-3xl text-lg text-muted">
            Each cell counts NASA solid-material fire tests run in space at that gravity, oxygen and pressure.
            {q.data && <> Only <b className="tnum text-ink">{summary.tested} of {summary.total}</b> space condition cells have a test in NASA's PSI tables
              {summary.flameOnly > 0 && <>; <b className="tnum text-signal">{summary.flameOnly}</b> more have droplet or gas flames (FLEX, CFI, ACME) but no solid material</>}.</>}
          </p>
        </div>
        <Legend />
      </PageHero>

      {!q.data ? <div className="grid gap-6 xl:grid-cols-2"><Skeleton className="h-96 rounded-card" /><Skeleton className="h-96 rounded-card" /></div> : (
        <div className="grid gap-6 xl:grid-cols-2">
          {pressures.map((p) => (
            <Card key={p} className="p-5">
              <div className="mb-4 flex items-baseline justify-between gap-2">
                <h2 className="text-h3">{p.includes("101") ? "ISS / sea-level pressure" : "Exploration pressure"}</h2>
                <span className="font-mono text-label uppercase text-faint">{p}</span>
              </div>
              <div role="grid" aria-label={`Space tests at ${p}`} className="grid gap-1.5" style={{ gridTemplateColumns: `6.5rem repeat(${o2Bins.length}, minmax(0, 1fr))` }}>
                <div role="row" className="contents">
                  <span />
                  {o2Bins.map((b) => <span key={b} role="columnheader" className="tnum pb-1 text-center text-sm text-muted">{b}<br /><span className="text-faint">O₂</span></span>)}
                </div>
                {GRAVITY_ROWS.map((row) => (
                  <div role="row" key={row.g} className="contents">
                    <span role="rowheader" className="flex items-center gap-2 pr-1 text-sm">
                      <row.Icon size={15} className="shrink-0 text-muted" aria-hidden />
                      <span><span className="text-ink">{row.label}</span><br /><span className="tnum text-faint">{row.sub}</span></span>
                    </span>
                    {o2Bins.map((b) => {
                      const c = q.data!.find((x) => x.gravity_g === row.g && x.o2_range === b && x.pressure === p)!;
                      return <Cell key={b} c={c} maxN={maxN} active={focus === c} onFocus={() => setFocus(c)} />;
                    })}
                  </div>
                ))}
              </div>
            </Card>
          ))}
        </div>
      )}

      <Card className="flex flex-col gap-3 p-5 text-sm text-muted lg:flex-row lg:items-center lg:justify-between" aria-live="polite">
        <div>
          {focus ? (
            <p>
              <b className="text-ink">{GRAVITY_ROWS.find((r) => r.g === focus.gravity_g)?.label}, {focus.o2_range} O₂, {focus.pressure}:</b>{" "}
              {focus.gravity_g === 1.0 ? focus.note : focus.space_tests ? `${focus.space_tests} solid-material space tests in PSI.` : "no solid-material test in PSI."}
              {(focus.droplet_tests ?? 0) > 0 && <> Also <b className="text-ink">{focus.droplet_tests}</b> FLEX fuel-droplet flames here (liquid fuel, not materials; see <a href="/experiments#flex">Experiments</a>).</>}
              {(focus.gas_flame_tests ?? 0) > 0 && <> Also <b className="text-ink">{focus.gas_flame_tests}</b> ACME gas flames here.</>}
              {focus.mission_design_points.length > 0 && <> Mission design point: <b className="text-ink">{focus.mission_design_points.join(", ")}</b>.</>}
            </p>
          ) : <p>Hover or tab to a cell for details. Click a mission pin to check that scenario.</p>}
          <p className="mt-1 text-faint">Pressure of ISS/Cygnus tests in PSI tables is assumed ~101 kPa (not recorded). Droplet and gas flames (FLEX, CFI, ACME) use the pressure NASA recorded. Earth row: certification tests (NASA-STD-6001 Test 1) are in MAPTIS, not in this dataset.</p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          <SourceChip href={`${PSI_PORTAL}/PSI-25`} label="NASA PSI · BASS-II" />
          <SourceChip href={`${PSI_PORTAL}/PSI-98`} label="NASA PSI · SAFFIRE" />
        </div>
      </Card>
    </div>
  );
}

function Cell({ c, maxN, active, onFocus }: { c: GapCell; maxN: number; active: boolean; onFocus: () => void }) {
  const earth = c.gravity_g === 1.0;
  const n = c.space_tests;
  const paper = (c.gas_flame_tests ?? 0) + (c.droplet_tests ?? 0); // liquid + gas flames in orbit (not solid materials)
  const pins = c.mission_design_points;
  const alpha = n ? 0.18 + 0.6 * Math.sqrt(n / maxN) : 0;
  const label = `${c.o2_range} O₂, ${c.pressure}, ${c.gravity_g} g: ${earth ? "not in this dataset" : n ? `${n} space tests` : paper ? `no solid-material test; ${paper} droplet or gas flames` : "no PSI test"}${pins.length ? `. Mission: ${pins.join(", ")}` : ""}`;
  const body = (
    <div
      role="gridcell" tabIndex={0} aria-label={label} title={label} onMouseEnter={onFocus} onFocus={onFocus}
      className={cx(
        "relative flex min-h-[4.6rem] flex-col items-center justify-center rounded-lg border p-1 text-center outline-none transition",
        n ? "border-signal/40" : earth ? "border-line bg-raised/40" : paper ? "border-2 border-dashed border-signal/70 bg-signal/5" : "border-danger/30",
        pins.length > 0 && !n && "border-danger ring-1 ring-danger/60",
        pins.length > 0 && n > 0 && "ring-1 ring-signal",
        active && "scale-[1.03] border-ink",
      )}
      style={n ? { background: `rgb(var(--signal) / ${alpha})` } : !earth && !paper ? {
        backgroundImage: "repeating-linear-gradient(135deg, rgb(var(--danger) / 0.10) 0 6px, transparent 6px 12px)",
      } : undefined}
    >
      {earth ? <span className="text-[11px] leading-tight text-faint">not in<br />dataset</span>
        : n ? <span className="tnum text-h3 text-ink">{n}</span>
        : paper ? <span className="text-[11px] font-semibold leading-tight text-signal">{paper} flames<br />no solids</span>
        : <span className="text-[11px] font-medium uppercase leading-tight tracking-wide text-danger/90">no PSI<br />test</span>}
      {n > 0 && paper > 0 && <span className="text-[10px] leading-tight text-ink/80">+{paper} flames</span>}
      {pins.map((m) => (
        <span key={m} className={cx("mt-1 inline-flex max-w-full items-center gap-0.5 truncate rounded px-1 text-[10px] font-semibold",
          n ? "bg-space/70 text-signal" : "bg-danger/20 text-danger")}>
          <MapPin size={10} aria-hidden className="shrink-0" />{m.split(" ")[0]}
        </span>
      ))}
    </div>
  );
  return pins.length ? (
    <Link to={`/scenario?mission=${missionToKey(pins[0])}`} className="no-underline hover:no-underline" aria-label={`Check scenario: ${pins[0]}`}>{body}</Link>
  ) : body;
}

function Legend() {
  return (
    <ul className="flex flex-wrap items-center gap-4 text-sm text-muted" aria-label="Legend">
      <li className="flex items-center gap-2"><span className="h-4 w-6 rounded border border-signal/40" style={{ background: "rgb(var(--signal) / 0.55)" }} />tested (count)</li>
      <li className="flex items-center gap-2"><span className="h-4 w-6 rounded border border-danger/40" style={{ backgroundImage: "repeating-linear-gradient(135deg, rgb(var(--danger) / 0.25) 0 4px, transparent 4px 8px)" }} />never tested</li>
      <li className="flex items-center gap-2"><span className="h-4 w-6 rounded border-2 border-dashed border-signal/70 bg-signal/5" />flames only (no solid material)</li>
      <li className="flex items-center gap-2"><MapPin size={14} className="text-danger" aria-hidden />mission design point</li>
    </ul>
  );
}
