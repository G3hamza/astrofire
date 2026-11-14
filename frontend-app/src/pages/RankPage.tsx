import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { SourceChip } from "../components/SourceChip";
import { Card, CardHeader, ErrorState, Skeleton } from "../components/ui";
import { useQuery } from "../lib/api";
import { client, type RankResult, type RankRow } from "../lib/client";

/* Basic, functional UI on purpose: ranking logic and explanations live in /api/rank so a redesign keeps them. */

const ORDER = ["spacecraft", "iss", "exploration", "moon", "rover", "mars"];
const PILLARS = ["", "prevention", "detection", "suppression", "fundamental"];
const LABEL: Record<string, string> = { conditions: "Conditions", relevance: "Relevance", fuel: "Fuel", evidence: "Evidence" };

function Row({ r, weights }: { r: RankRow; weights: Record<string, number> }) {
  const [open, setOpen] = useState(false);
  return (
    <li className="border-t border-line/60 py-3">
      <div className="flex flex-wrap items-center gap-3">
        <span className="w-8 text-right font-mono text-muted">{r.rank}</span>
        <button className="text-left font-semibold text-ink hover:underline" onClick={() => setOpen(!open)} aria-expanded={open}>
          {r.acronym}
        </button>
        <span className="text-sm text-muted">{r.pillar}{r.pillar_secondary ? ` + ${r.pillar_secondary}` : ""} · {r.relevance_tier} · {r.fuel_phase}</span>
        <span className="ml-auto flex items-center gap-2">
          <span className="h-2 w-32 overflow-hidden rounded bg-raised" aria-hidden>
            <span className="block h-full bg-signal" style={{ width: `${r.score}%` }} />
          </span>
          <span className="w-12 text-right font-mono">{r.score.toFixed(0)}</span>
        </span>
      </div>
      <p className="ml-11 mt-1 text-sm text-muted">{r.reasons[0]}</p>
      {open && (
        <div className="ml-11 mt-2 space-y-2 text-sm">
          <p className="text-muted">{r.title}</p>
          <p>{Object.entries(r.components).map(([k, v]) => `${LABEL[k]} ${(v * weights[k]).toFixed(1)}/${weights[k]}`).join(" · ")}</p>
          <ul className="list-disc pl-5">{r.reasons.map((s) => <li key={s}>{s}</li>)}</ul>
          <SourceChip href={r.psi_url} label={`NASA PSI · ${r.investigation_id}`} />
        </div>
      )}
    </li>
  );
}

export default function RankPage() {
  const [sp, setSp] = useSearchParams();
  const habitat = sp.get("habitat") ?? "moon";
  const pillar = sp.get("pillar") ?? "";
  const habs = useQuery("habitats", client.habitats);
  const q = useQuery<RankResult>(`rank:${habitat}:${pillar}`, () => client.rank(habitat, pillar || undefined));
  const set = (k: string, v: string) => { const n = new URLSearchParams(sp); if (v) n.set(k, v); else n.delete(k); setSp(n, { replace: true }); };
  const h = q.data?.habitat;

  return (
    <div className="space-y-6">
      <header className="space-y-2">
        <p className="eyebrow">Habitat relevance</p>
        <h1 className="text-h1 text-ink">Which NASA investigations matter for my habitat?</h1>
        <p className="max-w-3xl text-muted">Pick a crew environment. All 24 PSI investigations are ranked by how close their tested conditions are,
          how directly they address fire safety, whether they burned cabin-type solids, and how much usable test data they have.</p>
      </header>
      <div className="flex flex-wrap gap-4">
        <label className="text-sm">Habitat{" "}
          <select className="rounded border border-line bg-raised px-2 py-1" value={habitat} onChange={(e) => set("habitat", e.target.value)}>
            {ORDER.filter((k) => habs.data?.[k]).map((k) => <option key={k} value={k}>{habs.data![k].name}</option>)}
          </select></label>
        <label className="text-sm">Pillar{" "}
          <select className="rounded border border-line bg-raised px-2 py-1" value={pillar} onChange={(e) => set("pillar", e.target.value)}>
            {PILLARS.map((x) => <option key={x} value={x}>{x || "all"}</option>)}
          </select></label>
      </div>
      {q.error && <ErrorState message={q.error} onRetry={q.reload} />}
      {!q.data && !q.error && <Skeleton className="h-80 rounded-card" />}
      {q.data && h && (
        <Card>
          <CardHeader eyebrow={h.kind} title={`${h.name}: ${h.o2_pct}% O₂ · ${h.pressure_kpa} kPa · ${h.gravity_g} g`}
            right={<span className="text-xs text-muted">Weights: {Object.entries(q.data.weights).map(([k, v]) => `${LABEL[k]} ${v}`).join(" · ")}</span>} />
          <div className="px-5 py-3">
            <p className="text-sm text-caution">{q.data.caveat}</p>
            {h.gravity_g > 0 && <p className="text-sm text-muted">PSI holds no partial-gravity combustion data; microgravity results can only bound this gravity.</p>}
            <ol className="mt-2">{q.data.ranked.map((r) => <Row key={r.investigation_id} r={r} weights={q.data!.weights} />)}</ol>
            <details className="mt-4 text-sm text-muted"><summary className="cursor-pointer">How the score is calculated</summary>
              <pre className="mt-2 whitespace-pre-wrap font-mono text-xs">{q.data.method}</pre></details>
          </div>
        </Card>
      )}
    </div>
  );
}
