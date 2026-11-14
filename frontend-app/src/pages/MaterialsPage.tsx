import { ArrowLeft, BadgeCheck, CircleHelp, FlaskConical, Rocket } from "lucide-react";
import { useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { FileRowChip, SourceChip } from "../components/SourceChip";
import { Callout, Card, CardHeader, cx, EmptyState, ErrorState, NotAvailable, Skeleton } from "../components/ui";
import { useQuery } from "../lib/api";
import { client } from "../lib/client";
import type { MaterialOverview } from "../lib/types";

const isUnknown = (basis: string | null | undefined) => (basis ?? "") !== "explicit_name";
const split = (s: string | null | undefined) => (s ?? "").split("|").map((x) => x.trim()).filter(Boolean);

/** Identity is always shown in words: "Named by NASA" or "Identity unknown". */
export function IdentityBadge({ basis, candidate }: { basis: string | null | undefined; candidate?: string | null }) {
  return isUnknown(basis) ? (
    <span className="inline-flex items-center gap-1.5 whitespace-nowrap rounded-full border border-dashed border-caution/70 px-2.5 py-0.5 text-sm font-medium text-caution"
      title="NASA's table gives only a shape or color. The family is a low-confidence guess from the investigation.">
      <CircleHelp size={13} aria-hidden /> Identity unknown{candidate ? ` · maybe ${candidate}` : ""}
    </span>
  ) : (
    <span className="inline-flex items-center gap-1.5 whitespace-nowrap rounded-full bg-ok/15 px-2.5 py-0.5 text-sm font-medium text-ok ring-1 ring-ok/45">
      <BadgeCheck size={13} aria-hidden /> Named by NASA
    </span>
  );
}

/* =============================== list =============================== */

export function MaterialsList() {
  const q = useQuery("materials", client.materials);
  const [solidOnly, setSolidOnly] = useState(true);
  const rows = useMemo(() => {
    const r = (q.data ?? []).filter((m) => !solidOnly || Number(m.solid_flame_tests) > 0);
    return r.sort((a, b) => Number(b.solid_flame_tests) - Number(a.solid_flame_tests) || Number(b.samples) - Number(a.samples));
  }, [q.data, solidOnly]);
  const unknown = (q.data ?? []).filter((m) => isUnknown(m.classification_basis)).length;

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div className="space-y-1">
          <p className="eyebrow">Materials</p>
          <h1 className="text-h1">What NASA actually burned</h1>
          <p className="max-w-3xl text-lg text-muted">
            {q.data ? <><b className="tnum text-ink">{q.data.length}</b> materials in the NASA tables. <b className="tnum text-caution">{unknown}</b> were never named by NASA, only described by shape or color.</> : "Loading…"}
          </p>
        </div>
        <label className="flex cursor-pointer items-center gap-2 text-sm text-muted">
          <input type="checkbox" checked={solidOnly} onChange={(e) => setSolidOnly(e.target.checked)} className="h-4 w-4 accent-[rgb(var(--signal))]" />
          Only solids with space fire tests
        </label>
      </header>

      {q.error ? <ErrorState message={q.error} onRetry={q.reload} /> : !q.data ? <Skeleton className="h-96 rounded-card" /> : (
        <Card>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="eyebrow">
                <tr className="border-b border-line/60">
                  {["Material", "Identity", "Investigations", "Space fire tests", "Outcome written by NASA", "Burned / went out", "Missing data"].map((h) => (
                    <th key={h} scope="col" className="whitespace-nowrap px-4 py-3 font-medium">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.map((m) => <Row key={m.material_id} m={m} />)}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
}

function Row({ m }: { m: MaterialOverview }) {
  return (
    <tr className={cx("border-b border-line/40 align-top hover:bg-raised/50", isUnknown(m.classification_basis) && "bg-caution/[0.04]")}>
      <td className="px-4 py-3">
        <Link to={`/materials/${m.material_id}`} className="font-semibold">{m.material}</Link>
        <div className="text-faint">{m.family}</div>
      </td>
      <td className="px-4 py-3">
        <IdentityBadge basis={m.classification_basis} />
        {isUnknown(m.classification_basis) && m.candidate_family && <div className="mt-1 text-faint">candidate: {m.candidate_family}</div>}
      </td>
      <td className="px-4 py-3 text-muted">{split(m.investigations).join(", ")}</td>
      <td className="tnum px-4 py-3 text-ink">{m.solid_flame_tests}</td>
      <td className="tnum px-4 py-3">{m.observed_outcomes}</td>
      <td className="tnum whitespace-nowrap px-4 py-3"><span className="text-burn">{m.burned}</span> / <span className="text-out">{m.went_out}</span></td>
      <td className="max-w-[16rem] px-4 py-3 text-faint">{m.properties_missing || "—"}</td>
    </tr>
  );
}

/* =============================== detail =============================== */

export function MaterialDetail() {
  const { id = "" } = useParams();
  const q = useQuery(`material:${id}`, () => client.material(id));
  const fam = useQuery("families", client.materialFamilies);
  const smoke = useQuery(`smoke:${id}`, () => client.smoke(id));

  if (q.error) return <div className="space-y-4"><Back /><ErrorState message={q.error} onRetry={q.reload} /></div>;
  if (!q.data) return <div className="space-y-4"><Back /><Skeleton className="h-40 rounded-card" /><Skeleton className="h-72 rounded-card" /></div>;

  const { material: m, overview: ov, samples, sample_count, properties, evidence_limitations } = q.data;
  const family = m.material_family ?? "";
  const scenarioFamily = isUnknown(m.classification_basis) ? null : fam.data?.find((f) => f.material === family);
  const name = ov.material ?? m.material_normalized_name ?? id;

  return (
    <div className="space-y-6">
      <Back />
      <header className="flex flex-wrap items-start justify-between gap-4">
        <div className="space-y-2">
          <p className="eyebrow flex items-center gap-2"><FlaskConical size={13} aria-hidden /> Material · {id}</p>
          <h1 className="text-h1">{name}</h1>
          <div className="flex flex-wrap items-center gap-2">
            <IdentityBadge basis={m.classification_basis} candidate={m.candidate_family} />
            <span className="text-muted">{family}</span>
            {m.classification_confidence && <span className="text-sm text-faint">· classification confidence: {m.classification_confidence}</span>}
          </div>
        </div>
        {scenarioFamily && (
          <Link to={`/scenario?material=${encodeURIComponent(scenarioFamily.material)}&mission=iss`}
            className="inline-flex h-10 items-center gap-2 rounded-lg bg-signal px-4 font-semibold text-space no-underline hover:bg-signal/90 hover:no-underline">
            <Rocket size={16} aria-hidden /> Check it in a scenario
          </Link>
        )}
      </header>

      {isUnknown(m.classification_basis) && (
        <Callout tone="caution" title="NASA never named this material">
          <p className="mt-2 text-ink/90">
            The test table only says <b>{split(m.original_names).join(" · ") || "a shape"}</b>. AstroFire lists it as
            {" "}<b>{m.candidate_family || "an unknown family"}</b> only as a low-confidence candidate, and does not use it as same-material evidence.
          </p>
        </Callout>
      )}

      <div className="grid gap-4 md:grid-cols-4">
        <Stat label="Space fire tests" value={ov.solid_flame_tests} />
        <Stat label="Outcome written by NASA" value={ov.observed_outcomes} />
        <Stat label="Burned" value={ov.burned} tone="text-burn" />
        <Stat label="Went out" value={ov.went_out} tone="text-out" />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader eyebrow="Identity" title="What NASA wrote" />
          <dl className="divide-y divide-line/50 text-sm">
            <Pair k="Names in NASA tables" v={split(m.original_names).join(" · ")} />
            <Pair k="Investigations" v={split(m.investigations).join(", ")} />
            <Pair k="Physical form" v={m.physical_form} />
            <Pair k="Composition" v={m.material_composition} />
            <Pair k="Manufacturer" v={m.manufacturer} />
            <Pair k="Properties available" v={ov.properties_available} />
          </dl>
          <div className="flex flex-wrap gap-2 border-t border-line/60 px-5 py-3">
            {split(m.source_reference).map((u) => <SourceChip key={u} href={u} />)}
          </div>
        </Card>
        <Card>
          <CardHeader eyebrow="Evidence limitations" title="What this data can't tell you" />
          <ul className="space-y-2 p-5 text-ink/90">
            {evidence_limitations.map((t) => <li key={t} className="ml-5 list-disc marker:text-caution">{t}</li>)}
          </ul>
        </Card>
      </div>

      <Card>
        <CardHeader eyebrow="Samples" title={`${sample_count} samples in NASA tables`} right={sample_count > samples.length && <span className="text-sm text-faint">showing first {samples.length}</span>} />
        {samples.length === 0 ? <div className="p-5"><EmptyState title="No samples recorded" /></div> : (
          <div className="max-h-96 overflow-auto">
            <table className="w-full text-left text-sm">
              <thead className="eyebrow sticky top-0 bg-surface"><tr>{["Record", "Name in NASA table", "Geometry", "Source"].map((h) => <th key={h} className="px-4 py-2 font-medium">{h}</th>)}</tr></thead>
              <tbody>
                {samples.slice(0, 100).map((s) => (
                  <tr key={s.sample_id} className="border-t border-line/40">
                    <td className="whitespace-nowrap px-4 py-2 font-mono">{s.record_id}</td>
                    <td className="px-4 py-2">{s.material_original_name}</td>
                    <td className="px-4 py-2 text-muted">{s.geometry || <NotAvailable />}</td>
                    <td className="px-4 py-2"><FileRowChip file={s.source_file} row={s.source_row} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {(smoke.data?.length ?? 0) > 0 && (
        <Card>
          <CardHeader eyebrow="Smoke tests (SAME / SAME-R)" title={`Heated (not burned) in ${smoke.data!.length} smoke runs on the ISS`} />
          <div className="space-y-2 p-5 text-sm text-muted">
            <p>NASA overheated this material to measure the smoke it gives off, for smoke detectors. The PSI table lists the run conditions; particle results are in NASA's raw data files.</p>
            <p className="tnum text-ink">Air flow: {[...new Set(smoke.data!.map((r) => r.flow_cm_s).filter(Boolean))].join(", ") || "not recorded"} cm/s · runs: {smoke.data!.filter((r) => r.investigation === "SAME").length} SAME, {smoke.data!.filter((r) => r.investigation === "SAME-R").length} SAME-R</p>
            <Link to="/experiments#smoke">All smoke tests</Link>
          </div>
        </Card>
      )}

      {properties.length > 0 && (
        <Card>
          <CardHeader eyebrow="Properties" title="Measured properties" />
          <div className="max-h-80 overflow-auto">
            <table className="w-full text-left text-sm">
              <thead className="eyebrow sticky top-0 bg-surface"><tr>{Object.keys(properties[0]).filter((k) => !["material_id", "source_file", "source_row"].includes(k)).map((h) => <th key={h} className="px-4 py-2 font-medium">{h}</th>)}<th className="px-4 py-2 font-medium">source</th></tr></thead>
              <tbody>
                {properties.slice(0, 200).map((p, i) => (
                  <tr key={i} className="border-t border-line/40">
                    {Object.entries(p).filter(([k]) => !["material_id", "source_file", "source_row"].includes(k)).map(([k, v]) => <td key={k} className="px-4 py-2">{v || <NotAvailable />}</td>)}
                    <td className="px-4 py-2"><FileRowChip file={p.source_file} row={p.source_row} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
}

function Back() {
  return <Link to="/materials" className="inline-flex items-center gap-1.5 text-sm"><ArrowLeft size={14} aria-hidden /> All materials</Link>;
}

function Stat({ label, value, tone }: { label: string; value?: string; tone?: string }) {
  return (
    <div className="rounded-card border border-line bg-surface/90 p-4">
      <p className="eyebrow">{label}</p>
      <p className={cx("tnum mt-1 text-h2", tone ?? "text-ink")}>{value ?? <NotAvailable />}</p>
    </div>
  );
}

function Pair({ k, v }: { k: string; v?: string | null }) {
  return (
    <div className="grid grid-cols-[11rem_1fr] gap-3 px-5 py-2.5">
      <dt className="text-faint">{k}</dt>
      <dd className="text-ink">{v ? v : <NotAvailable />}</dd>
    </div>
  );
}
