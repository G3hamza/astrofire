import { useMemo, useState } from "react";
import { SourceChip } from "../components/SourceChip";
import { Button, Card, CardHeader, cx, ErrorState, Skeleton } from "../components/ui";
import { useQuery } from "../lib/api";
import { client, type InvestigationCompare, type InvestigationProfile, type ProfileCondition } from "../lib/client";

/* Basic, functional UI on purpose: the logic lives in /api/investigations/* so a later redesign keeps it. */

const PILLARS = ["all", "prevention", "detection", "suppression", "fundamental"] as const;
const TIERS = ["all", "direct", "related", "background"] as const;
const TIER_HINT: Record<string, string> = {
  direct: "Named by the challenge as a flammability, detection or suppression study",
  related: "Named by the challenge as relevant (DAFT, BRE, CFI-G, E-FIELD)",
  background: "Other PSI combustion work: relevant to fire safety, less directly",
};

function cond(c: ProfileCondition) {
  if (c.kind === "range") {
    const v = c.min === c.max ? `${c.min}` : `${c.min} – ${c.max}`;
    return `${v}${c.unit ? " " + c.unit : ""}`;
  }
  const vals = (c.values ?? []).slice(0, 4).map((v) => v.value).join(", ");
  return c.distinct > 4 ? `${vals} … (${c.distinct} values)` : vals;
}

function Chip({ children, tone }: { children: React.ReactNode; tone?: "ok" | "muted" | "signal" }) {
  return (
    <span className={cx("inline-block rounded-full border px-2 py-0.5 text-xs",
      tone === "ok" ? "border-ok/50 text-ok" : tone === "signal" ? "border-signal/50 text-signal" : "border-line text-muted")}>
      {children}
    </span>
  );
}

function Profile({ p, selected, onToggle }: { p: InvestigationProfile; selected: boolean; onToggle: () => void }) {
  const [open, setOpen] = useState(false);
  return (
    <Card as="article">
      <CardHeader eyebrow={`${p.investigation_id} · ${p.hardware_family}`} title={`${p.acronym} — ${p.title}`}
        right={<label className="flex items-center gap-2 text-sm text-muted">
          <input type="checkbox" checked={selected} onChange={onToggle} aria-label={`Select ${p.acronym} to compare`} /> Compare
        </label>} />
      <div className="space-y-3 px-5 py-4 text-sm">
        <div className="flex flex-wrap gap-2">
          <Chip tone="signal">{p.pillar}{p.pillar_secondary ? ` + ${p.pillar_secondary}` : ""}</Chip>
          <Chip tone={p.relevance_tier === "direct" ? "ok" : "muted"}>{p.relevance_tier} relevance</Chip>
          <Chip>{p.fuel_phase}</Chip>
          <Chip>{p.study_type}</Chip>
          <Chip>{p.records} records</Chip>
        </div>
        {p.partial_gravity_note && <p className="rounded border border-caution/50 p-2 text-caution">{p.partial_gravity_note}</p>}
        <p><span className="eyebrow">Objective (NASA) </span>{p.objective.slice(0, open ? undefined : 320)}{!open && p.objective.length > 320 ? "…" : ""}</p>
        {p.conditions.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[420px] text-left">
              <thead><tr className="text-muted"><th className="py-1 pr-3">Factor</th><th className="py-1 pr-3">Values in NASA table</th><th className="py-1">Between tests</th></tr></thead>
              <tbody>
                {p.conditions.map((c) => (
                  <tr key={c.factor} className="border-t border-line/60">
                    <td className="py-1 pr-3">{c.factor}</td><td className="py-1 pr-3">{cond(c)}</td>
                    <td className="py-1">{c.distinct > 1 ? "varied" : "same"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {p.not_recorded_factors.length > 0 && <p className="text-muted">Not recorded in NASA table: {p.not_recorded_factors.join(", ")}</p>}
        {p.sensors.length > 0 && <p><span className="eyebrow">Sensors </span>{p.sensors.map((s) => s.sensor).join(" · ")}</p>}
        {p.measured_quantities.length > 0 && <p><span className="eyebrow">Measured </span>{p.measured_quantities.map((s) => s.sensor).join(" · ")}</p>}
        {open && (
          <div className="space-y-3">
            {p.hypothesis && <p><span className="eyebrow">Hypothesis (NASA) </span>{p.hypothesis}</p>}
            {p.approach && <p><span className="eyebrow">Approach (NASA) </span>{p.approach}</p>}
            {p.research_impacts && <p><span className="eyebrow">Research impacts (NASA) </span>{p.research_impacts}</p>}
            {p.data_files && <p><span className="eyebrow">Data files in PSI </span>
              {p.data_files.files} files, {p.data_files.total_gb} GB · {Object.entries(p.data_files.file_types).map(([k, v]) => `${v} ${k}`).join(", ")}</p>}
            {p.publications.length > 0 && <div><p className="eyebrow">Publications ({p.publications_count})</p>
              <ul className="list-disc pl-5">{p.publications.map((x) => <li key={x.title}>{x.title}{x.doi ? ` (doi ${x.doi})` : ""}</li>)}</ul></div>}
            <p className="text-muted"><span className="eyebrow">Why this classification </span>{p.curation_basis}</p>
            <ul className="text-xs text-muted">{p.sensors.map((s) => <li key={s.sensor}>{s.sensor}: {s.evidence}</li>)}</ul>
          </div>
        )}
        <div className="flex flex-wrap items-center gap-3">
          <Button variant="secondary" onClick={() => setOpen(!open)} aria-expanded={open}>{open ? "Show less" : "Full profile"}</Button>
          <SourceChip href={p.psi_url} label={`NASA PSI · ${p.investigation_id}`} />
        </div>
      </div>
    </Card>
  );
}

function CompareView({ ids, profiles }: { ids: string[]; profiles: Map<string, InvestigationProfile> }) {
  const key = ids.join(",");
  const q = useQuery<InvestigationCompare>(`inv-compare:${key}`, () => client.investigationsCompare(ids));
  if (q.error) return <ErrorState message={q.error} />;
  if (!q.data) return <Skeleton className="h-40 rounded-card" />;
  const d = q.data;
  const same = Object.entries(d.same).filter(([, v]) => v).map(([k]) => k.replace("_", " "));
  const diff = Object.entries(d.same).filter(([, v]) => !v).map(([k]) => k.replace("_", " "));
  return (
    <Card tone="signal">
      <CardHeader eyebrow="Compare investigations" title={ids.map((i) => profiles.get(i)?.acronym ?? i).join(" vs ")} />
      <div className="space-y-2 px-5 py-4 text-sm">
        <p><span className="eyebrow">Same </span>{same.join(", ") || "nothing in pillar, hardware, fuel, study type or tier"}</p>
        <p><span className="eyebrow">Different </span>{diff.join(", ") || "—"}</p>
        <p><span className="eyebrow">Factors recorded by all </span>{d.factors.in_all.join(", ") || "none in common"}</p>
        {Object.entries(d.factors.only_in).map(([id, f]) => f.length > 0 && (
          <p key={id}><span className="eyebrow">Only {profiles.get(id)?.acronym ?? id} </span>{f.join(", ")}</p>))}
        <p><span className="eyebrow">Sensors in all </span>{d.sensors.in_all.join(", ") || "none in common"}</p>
        <p><span className="eyebrow">Measured by all </span>{d.measured_quantities.in_all.join(", ") || "none in common"}</p>
        <p className="text-xs text-muted">{d.note}</p>
      </div>
    </Card>
  );
}

export default function InvestigationsPage() {
  const q = useQuery<InvestigationProfile[]>("inv-profiles", client.investigationProfiles);
  const [pillar, setPillar] = useState<(typeof PILLARS)[number]>("all");
  const [tier, setTier] = useState<(typeof TIERS)[number]>("all");
  const [sel, setSel] = useState<string[]>([]);
  const byId = useMemo(() => new Map((q.data ?? []).map((p) => [p.investigation_id, p])), [q.data]);
  const shown = (q.data ?? []).filter((p) => (pillar === "all" || p.pillar === pillar || p.pillar_secondary === pillar)
    && (tier === "all" || p.relevance_tier === tier));
  const toggle = (id: string) => setSel((s) => s.includes(id) ? s.filter((x) => x !== id) : s.length >= 6 ? s : [...s, id]);

  return (
    <div className="space-y-6">
      <header className="space-y-2">
        <p className="eyebrow">NASA PSI combustion investigations</p>
        <h1 className="text-h1 text-ink">Investigations</h1>
        <p className="max-w-3xl text-muted">All 24 investigations: what NASA set out to learn, the fuels and conditions, what varied between tests,
          the sensors used, and the data files. Grouped by fire-safety pillar: prevention, detection, suppression.</p>
      </header>
      <div className="flex flex-wrap gap-4">
        <label className="text-sm">Pillar{" "}
          <select className="rounded border border-line bg-raised px-2 py-1" value={pillar} onChange={(e) => setPillar(e.target.value as typeof pillar)}>
            {PILLARS.map((x) => <option key={x}>{x}</option>)}
          </select></label>
        <label className="text-sm">Relevance{" "}
          <select className="rounded border border-line bg-raised px-2 py-1" value={tier} onChange={(e) => setTier(e.target.value as typeof tier)}>
            {TIERS.map((x) => <option key={x}>{x}</option>)}
          </select></label>
        {tier !== "all" && <p className="self-center text-sm text-muted">{TIER_HINT[tier]}</p>}
        {sel.length > 0 && <Button variant="ghost" onClick={() => setSel([])}>Clear compare ({sel.length})</Button>}
      </div>
      {sel.length === 1 && <p className="text-sm text-muted">Select one more investigation to compare (up to 6).</p>}
      {sel.length >= 2 && <CompareView ids={sel} profiles={byId} />}
      {q.error && <ErrorState message={q.error} onRetry={q.reload} />}
      {!q.data && !q.error && <Skeleton className="h-80 rounded-card" />}
      {q.data && shown.length === 0 && <p className="text-muted">No investigation matches these filters.</p>}
      <div className="grid gap-4">
        {shown.map((p) => <Profile key={p.investigation_id} p={p} selected={sel.includes(p.investigation_id)} onToggle={() => toggle(p.investigation_id)} />)}
      </div>
    </div>
  );
}
