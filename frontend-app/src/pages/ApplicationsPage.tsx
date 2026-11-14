import { Download } from "lucide-react";
import { SourceChip } from "../components/SourceChip";
import { Card, CardHeader, ErrorState, Skeleton } from "../components/ui";
import { api, useQuery } from "../lib/api";

/* Basic, functional UI on purpose: content comes from /api/datasets, /api/equipment-insights, /api/earth-applications. */

type Dataset = { name: string; file: string; description: string; rows: number; columns: { name: string; filled: number }[];
  caveats: string[]; download: string; license: string };
type Catalog = { datasets: Dataset[]; ml_readme: string | null; data_dictionary: string };
type Pillar = { pillar: string; interpretation: string; interpretation_label: string;
  investigations: { investigation_id: string; acronym: string; relevance_tier: string; nasa_says: string[]; psi_url: string }[] };
type Earth = { caveat: string; spinoffs: { id: string; title: string; url: string; summary: string }[];
  from_psi_investigations: { investigation_id: string; acronym: string; nasa_says: string[]; psi_url: string }[] };

const PILLAR_TITLE: Record<string, string> = { prevention: "Prevention: materials and fire growth", detection: "Detection: smoke and sensors",
  suppression: "Suppression: putting fires out" };

export default function ApplicationsPage() {
  const cat = useQuery<Catalog>("datasets", () => api("/api/datasets"));
  const eq = useQuery<Pillar[]>("equipment", () => api("/api/equipment-insights"));
  const earth = useQuery<Earth>("earth", () => api("/api/earth-applications"));

  return (
    <div className="space-y-8">
      <header className="space-y-2">
        <p className="eyebrow">From research to use</p>
        <h1 className="text-h1 text-ink">Data, equipment and Earth applications</h1>
        <p className="max-w-3xl text-muted">Download the cleaned NASA data for modeling, see what NASA says its research means for fire detection,
          suppression and material selection, and where it already helps on Earth. NASA's words are quoted with their source; StarryNight's reading is labelled.</p>
      </header>

      <section className="space-y-3" aria-labelledby="data-h">
        <h2 id="data-h" className="text-h2">Data for flammability modeling</h2>
        {cat.error && <ErrorState message={cat.error} onRetry={cat.reload} />}
        {!cat.data && !cat.error && <Skeleton className="h-40 rounded-card" />}
        <div className="grid gap-4 md:grid-cols-2">
          {cat.data?.datasets.map((d) => (
            <Card key={d.name} as="article">
              <CardHeader eyebrow={`${d.rows} rows · ${d.columns.length} columns · ${d.license}`} title={d.name}
                right={<a href={d.download} download className="inline-flex items-center gap-1 text-sm"><Download size={16} aria-hidden /> CSV</a>} />
              <div className="space-y-2 px-5 py-4 text-sm">
                <p>{d.description}</p>
                <ul className="list-disc pl-5 text-caution">{d.caveats.map((c) => <li key={c}>{c}</li>)}</ul>
                <details><summary className="cursor-pointer text-muted">Columns (rows with a value)</summary>
                  <p className="mt-1 font-mono text-xs text-muted">{d.columns.map((c) => `${c.name} (${c.filled})`).join(" · ")}</p></details>
                <p className="text-xs text-muted">{d.file}</p>
              </div>
            </Card>))}
        </div>
        {cat.data?.ml_readme && <details className="text-sm text-muted"><summary className="cursor-pointer">Read before training (ML table notes)</summary>
          <pre className="mt-2 whitespace-pre-wrap font-mono text-xs">{cat.data.ml_readme}</pre></details>}
      </section>

      <section className="space-y-3" aria-labelledby="eq-h">
        <h2 id="eq-h" className="text-h2">What the research means for fire safety equipment</h2>
        {eq.error && <ErrorState message={eq.error} onRetry={eq.reload} />}
        {!eq.data && !eq.error && <Skeleton className="h-40 rounded-card" />}
        {eq.data?.map((p) => (
          <Card key={p.pillar}>
            <CardHeader eyebrow={p.pillar} title={PILLAR_TITLE[p.pillar] ?? p.pillar} />
            <div className="space-y-3 px-5 py-4 text-sm">
              <p className="rounded border border-signal/40 p-2"><span className="eyebrow">{p.interpretation_label} </span>{p.interpretation}</p>
              <ul className="space-y-2">{p.investigations.map((i) => (
                <li key={i.investigation_id}><b className="text-ink">{i.acronym}</b> <span className="text-xs text-muted">({i.relevance_tier})</span>:{" "}
                  “{i.nasa_says[0]}” <SourceChip href={i.psi_url} label={`NASA PSI · ${i.investigation_id}`} /></li>))}</ul>
            </div>
          </Card>))}
      </section>

      <section className="space-y-3" aria-labelledby="earth-h">
        <h2 id="earth-h" className="text-h2">Fire safety on Earth</h2>
        {earth.error && <ErrorState message={earth.error} onRetry={earth.reload} />}
        {earth.data && (<>
          <p className="text-sm text-caution">{earth.data.caveat}</p>
          <div className="grid gap-4 md:grid-cols-2">
            {earth.data.spinoffs.map((s) => (
              <Card key={s.id} as="article"><CardHeader eyebrow="Listed in the challenge resources" title={s.title} />
                <div className="space-y-2 px-5 py-4 text-sm"><p>{s.summary}</p><SourceChip href={s.url} /></div></Card>))}
          </div>
          <Card><CardHeader eyebrow="In NASA's own words (PSI research impacts)" title="Earth benefits named by the investigations" />
            <ul className="space-y-2 px-5 py-4 text-sm">{earth.data.from_psi_investigations.map((i) => (
              <li key={i.investigation_id}><b className="text-ink">{i.acronym}</b>: “{i.nasa_says[0]}” <SourceChip href={i.psi_url} label={i.investigation_id} /></li>))}</ul>
          </Card>
        </>)}
      </section>
    </div>
  );
}
