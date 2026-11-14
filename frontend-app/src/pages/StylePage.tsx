import { ArrowRight, Grid3x3, MessageSquareText, Rocket, Search } from "lucide-react";
import type { ReactNode } from "react";
import { BasisBadge, ConfidenceBadge, EvidenceStatusBadge, OutcomeTag } from "../components/badges";
import { KpiTile } from "../components/KpiTile";
import { FileRowChip, SourceChip } from "../components/SourceChip";
import { Button, Callout, Card, CardHeader, EmptyState, ErrorState, Skeleton } from "../components/ui";
import { VerdictBanner } from "../components/VerdictBanner";
import { useApi } from "../lib/api";
import { VERDICTS } from "../lib/domain";

/* G2-P1 deliverable: every design-system component on one page.
   Numbers shown here are LIVE from the API (never invented); strings are the API contract values. */

type Kpi = { kpi: string; value: string; unit: string };
type Overview = { kpis: Kpi[] };
type Stats = { gas_flame_tests: number };
type Evidence = {
  test_id: string; investigation: string; material: string; o2_pct: number; flow_cm_s: number;
  outcome: string; outcome_basis: string; pressure_status: string; source_file: string; source_row: string; psi_url: string; doi?: string;
};
type ScenarioResp = { verdict: string; confidence: string; evidence_status: string; blockers: string[]; flags: string[]; evidence: Evidence[] };

const MARS_NOMEX = JSON.stringify({ material: "Aramid fabric (Nomex)", mission: "mars" });
const ISS_NOMEX = JSON.stringify({ material: "Aramid fabric (Nomex)", mission: "iss" });

const TOKENS: { name: string; cls: string; hex: string; use: string }[] = [
  { name: "space", cls: "bg-space", hex: "#060A13", use: "Page background" },
  { name: "surface", cls: "bg-surface", hex: "#0D1423", use: "Cards" },
  { name: "raised", cls: "bg-raised", hex: "#151F34", use: "Inputs, chips, hover" },
  { name: "line", cls: "bg-line", hex: "#24324E", use: "Borders" },
  { name: "ink", cls: "bg-ink", hex: "#E8EEF8", use: "Primary text" },
  { name: "muted", cls: "bg-muted", hex: "#9CACC7", use: "Secondary text" },
  { name: "faint", cls: "bg-faint", hex: "#6E7E9B", use: "Captions" },
  { name: "signal", cls: "bg-signal", hex: "#38D6F5", use: "Accent, links, focus" },
  { name: "burn", cls: "bg-burn", hex: "#EA6624", use: "Outcome: burned" },
  { name: "out", cls: "bg-out", hex: "#4B8FF7", use: "Outcome: went out" },
  { name: "blow", cls: "bg-blow", hex: "#E9479A", use: "Outcome: blowoff" },
  { name: "unknown", cls: "bg-unknown", hex: "#94A3B8", use: "Outcome: not recorded" },
  { name: "danger", cls: "bg-danger", hex: "#F85E6A", use: "Insufficient evidence, blockers" },
  { name: "caution", cls: "bg-caution", hex: "#FBBF24", use: "Flags, borderline, inferred" },
  { name: "ok", cls: "bg-ok", hex: "#34D399", use: "Observed" },
];

function Section({ id, title, note, children }: { id: string; title: string; note?: string; children: ReactNode }) {
  return (
    <section id={id} aria-labelledby={`${id}-h`} className="scroll-mt-20">
      <div className="mb-4 flex items-baseline justify-between gap-4 border-b border-line/60 pb-2">
        <h2 id={`${id}-h`} className="text-h2">{title}</h2>
        {note && <p className="text-sm text-faint">{note}</p>}
      </div>
      {children}
    </section>
  );
}

export default function StylePage() {
  const ov = useApi<Overview>("/api/analytics/overview");
  const st = useApi<Stats>("/api/stats");
  const mars = useApi<ScenarioResp>("/api/scenario", { method: "POST", body: MARS_NOMEX });
  const iss = useApi<ScenarioResp>("/api/scenario", { method: "POST", body: ISS_NOMEX });

  const k = (name: string) => ov.data?.kpis.find((x) => x.kpi === name)?.value ?? null;
  const loadingKpi = ov.loading || !ov.data;
  const row = iss.data?.evidence[0];

  return (
    <div className="space-y-14">
      <header className="space-y-3">
        <p className="eyebrow">G2-P1 · Design system</p>
        <h1 className="text-h1">AstroFire mission-control UI kit</h1>
        <p className="max-w-3xl text-lg text-muted">
          Every component the product uses, on one page. Every number on this page comes live from <code className="font-mono text-ink">/api/*</code>.
          Outcomes and evidence quality always use an icon and a word, not just a color.
        </p>
        <nav aria-label="Sections" className="flex flex-wrap gap-2 pt-2">
          {["colors", "type", "outcomes", "evidence", "sources", "kpis", "verdicts", "callouts", "buttons", "states", "row"].map((s) => (
            <a key={s} href={`#${s}`} className="rounded-md border border-line bg-raised px-2.5 py-1 font-mono text-label uppercase text-muted no-underline hover:border-signal/60 hover:text-signal hover:no-underline">{s}</a>
          ))}
        </nav>
      </header>

      <Section id="colors" title="Color tokens" note="CSS variables in src/index.css → Tailwind names">
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
          {TOKENS.map((t) => (
            <div key={t.name} className="overflow-hidden rounded-card border border-line bg-surface">
              <div className={`h-14 ${t.cls} border-b border-line`} />
              <div className="p-3">
                <p className="font-mono text-sm text-ink">{t.name}</p>
                <p className="font-mono text-[12px] text-faint">{t.hex}</p>
                <p className="mt-1 text-sm text-muted">{t.use}</p>
              </div>
            </div>
          ))}
        </div>
      </Section>

      <Section id="type" title="Type scale" note="Sized for 1366×768 and projectors">
        <Card className="divide-y divide-line/60">
          {[
            ["display · 56", "text-display", "0 tests"],
            ["h1 · 36", "text-h1", "Will it burn on Mars?"],
            ["h2 · 26", "text-h2", "Insufficient validated experimental evidence"],
            ["h3 · 20", "text-h3", "Closest NASA tests"],
            ["lg · 18", "text-lg", "AstroFire shows NASA where to test next."],
            ["base · 15", "text-base", "Body text for reasons, notes and notes from NASA test tables."],
            ["sm · 13", "text-sm text-muted", "Captions and table cells."],
            ["eyebrow · 12 mono", "eyebrow", "Section label"],
          ].map(([name, cls, sample]) => (
            <div key={name} className="flex items-baseline gap-6 px-5 py-3">
              <span className="w-36 shrink-0 font-mono text-[12px] text-faint">{name}</span>
              <span className={cls}>{sample}</span>
            </div>
          ))}
        </Card>
      </Section>

      <Section id="outcomes" title="Outcomes" note="NASA's own term kept as a suffix + tooltip">
        <Card className="flex flex-wrap items-center gap-3 p-5">
          <OutcomeTag outcome="Burned" />
          <OutcomeTag outcome="Extinction" />
          <OutcomeTag outcome="Not Sustained" />
          <OutcomeTag outcome="No Ignition" />
          <OutcomeTag outcome="Blowoff" />
          <OutcomeTag outcome="Unknown" />
        </Card>
      </Section>

      <Section id="evidence" title="Evidence quality" note="observed = NASA wrote it · inferred = from notes · assumed = stated assumption">
        <Card className="space-y-5 p-5">
          <div className="flex flex-wrap items-center gap-3">
            <BasisBadge basis="observed" />
            <BasisBadge basis="inferred" />
            <BasisBadge basis="assumed (ISS cabin; not in NASA table)" />
            <BasisBadge basis="not_recorded" />
          </div>
          <div className="flex flex-wrap items-center gap-6">
            <EvidenceStatusBadge status="evidence-based" />
            <EvidenceStatusBadge status="exploratory" />
            <ConfidenceBadge level="High" />
            <ConfidenceBadge level="Medium" />
            <ConfidenceBadge level="Low" />
          </div>
        </Card>
      </Section>

      <Section id="sources" title="Source chips" note="Live values from /api/scenario">
        <Card className="flex flex-wrap items-center gap-3 p-5">
          {row ? (
            <>
              <SourceChip href={row.psi_url} />
              {row.doi && <SourceChip href={row.doi} />}
              <FileRowChip file={row.source_file} row={row.source_row} />
            </>
          ) : <Skeleton className="h-7 w-72" />}
          <SourceChip href={null} />
        </Card>
      </Section>

      <Section id="kpis" title="KPI tiles" note="Live from /api/analytics/overview + /api/stats">
        {ov.error ? <ErrorState message={ov.error} onRetry={ov.reload} /> : (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <KpiTile loading={loadingKpi} label="Space solid-material fire tests" value={k("solid_flame_tests_total")} unit="tests" caption="BASS, BASS-II, SAFFIRE I–III" />
            <KpiTile loading={loadingKpi} label="Outcome written by NASA" value={k("pct_outcomes_observed")} unit="%" caption="share of tests with an observed outcome" />
            <KpiTile loading={loadingKpi} label="Oxygen range tested" value={k("o2_tested_min_pct") && `${k("o2_tested_min_pct")}–${k("o2_tested_max_pct")}`} unit="% O₂" caption="Moon/Mars design point is 34%" />
            <KpiTile loading={loadingKpi} tone="danger" label="Space tests at Moon/Mars conditions" value={k("space_tests_at_moon_mars_design_point")} unit="tests" caption="34% O₂ · 56.5 kPa · 0.166 / 0.38 g" />
            <KpiTile loading={st.loading} tone="signal" label="ACME gas flames" value={st.data?.gas_flame_tests} unit="tests" source={<SourceChip href="https://psi.nasa.gov/physci/repo/data/investigations/PSI-159" label="NASA PSI · ACME" />} />
            <KpiTile label="Not available example" value={null} caption="Shown when the API has no value. We never invent one." />
          </div>
        )}
      </Section>

      <Section id="verdicts" title="Verdict banners" note="The four verdict strings from the API contract, shown word for word">
        <div className="space-y-3">
          {VERDICTS.map((v, i) => (
            <VerdictBanner key={v} verdict={v} confidence={["High", "Medium", "Medium", "Low"][i]}
              evidenceStatus={v.startsWith("Insufficient") ? "exploratory" : "evidence-based"} />
          ))}
        </div>
      </Section>

      <Section id="callouts" title="Blockers & flags" note="Live: Nomex on Mars (POST /api/scenario)">
        {mars.error ? <ErrorState message={mars.error} onRetry={mars.reload} /> : mars.data ? (
          <div className="grid gap-4 lg:grid-cols-2">
            <Callout tone="danger" title="Why NASA can't answer this yet" items={mars.data.blockers} />
            <Callout tone="caution" title="Notes on the evidence" items={mars.data.flags} />
          </div>
        ) : <div className="grid gap-4 lg:grid-cols-2"><Skeleton className="h-36" /><Skeleton className="h-36" /></div>}
      </Section>

      <Section id="buttons" title="Buttons">
        <Card className="flex flex-wrap items-center gap-3 p-5">
          <Button icon={<Rocket size={16} />}>Check a scenario</Button>
          <Button variant="secondary" icon={<Grid3x3 size={16} />}>See the gaps</Button>
          <Button variant="secondary" icon={<MessageSquareText size={16} />}>Ask NASA</Button>
          <Button variant="ghost">Ghost <ArrowRight size={16} /></Button>
          <Button disabled icon={<Search size={16} />}>Disabled</Button>
        </Card>
      </Section>

      <Section id="states" title="Loading, empty, error">
        <div className="grid gap-4 lg:grid-cols-3">
          <Card className="space-y-3 p-5">
            <p className="eyebrow">Skeleton</p>
            <Skeleton className="h-6 w-2/3" /><Skeleton className="h-4" /><Skeleton className="h-4 w-5/6" /><Skeleton className="h-4 w-1/2" />
          </Card>
          <EmptyState title="Never tested" hint="No NASA space test exists for these conditions. That gap is the finding." />
          <ErrorState message="The AstroFire API is not reachable. Is the server running?" onRetry={() => undefined} />
        </div>
      </Section>

      <Section id="row" title="Evidence row" note="Live: closest NASA test for Nomex on the ISS">
        <Card>
          <CardHeader eyebrow="Closest NASA tests" title="Evidence table row" right={iss.data && <span className="text-sm text-muted">{iss.data.evidence.length} tests</span>} />
          {iss.error ? <div className="p-5"><ErrorState message={iss.error} onRetry={iss.reload} /></div> : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="eyebrow">
                  <tr className="border-b border-line/60">
                    {["Test", "Investigation", "Material", "O₂ %", "Flow cm/s", "Outcome", "Basis", "Pressure", "Source"].map((h) => (
                      <th key={h} scope="col" className="whitespace-nowrap px-4 py-3 font-medium">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {(iss.data?.evidence.slice(0, 3) ?? []).map((e) => (
                    <tr key={e.test_id} className="border-b border-line/40 hover:bg-raised/50">
                      <td className="whitespace-nowrap px-4 py-3 font-mono text-ink">{e.test_id}</td>
                      <td className="px-4 py-3">{e.investigation}</td>
                      <td className="max-w-[16rem] truncate px-4 py-3" title={e.material}>{e.material}</td>
                      <td className="tnum px-4 py-3">{e.o2_pct}</td>
                      <td className="tnum px-4 py-3">{e.flow_cm_s}</td>
                      <td className="px-4 py-3"><OutcomeTag outcome={e.outcome} /></td>
                      <td className="px-4 py-3"><BasisBadge basis={e.outcome_basis} /></td>
                      <td className="px-4 py-3"><BasisBadge basis={e.pressure_status} /></td>
                      <td className="px-4 py-3"><div className="flex gap-2"><SourceChip href={e.psi_url} /><FileRowChip file={e.source_file} row={e.source_row} /></div></td>
                    </tr>
                  ))}
                  {iss.loading && [0, 1, 2].map((i) => (
                    <tr key={i}><td colSpan={9} className="px-4 py-3"><Skeleton className="h-6" /></td></tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      </Section>
    </div>
  );
}
