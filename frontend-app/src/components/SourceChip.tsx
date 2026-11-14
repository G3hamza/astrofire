import { Check, Copy, Database, ExternalLink, FileSpreadsheet, FileText, Link2 } from "lucide-react";
import { useState } from "react";
import { cx } from "./ui";

/* Traceability (NFR2): every number or claim gets one of these next to it. */

type Kind = "psi" | "ntrs" | "doi" | "url";

function kindOf(href: string): Kind {
  if (href.includes("psi.nasa.gov")) return "psi";
  if (href.includes("ntrs.nasa.gov")) return "ntrs";
  if (href.startsWith("10.") || href.includes("doi.org")) return "doi";
  return "url";
}

function autoLabel(href: string, kind: Kind) {
  if (kind === "psi") return `NASA PSI · ${href.split("/").pop()}`;
  if (kind === "ntrs") return `NTRS ${href.split("/").pop()}`;
  if (kind === "doi") return `DOI ${href.replace(/^https?:\/\/(dx\.)?doi\.org\//, "")}`;
  try { return new URL(href).hostname; } catch { return href; }
}

const ICON = { psi: Database, ntrs: FileText, doi: Link2, url: ExternalLink };

const chip = "inline-flex h-7 max-w-full items-center gap-1.5 rounded-md border border-line bg-raised px-2 font-mono text-[12px] text-muted transition-colors";

/** Link to a NASA source (PSI investigation, NTRS paper, DOI). */
export function SourceChip({ href, label }: { href: string | null | undefined; label?: string }) {
  if (!href) return <span className={cx(chip, "italic text-faint")}>source not available</span>;
  const kind = kindOf(href);
  const url = kind === "doi" && !href.startsWith("http") ? `https://doi.org/${href}` : href;
  const Icon = ICON[kind];
  return (
    <a href={url} target="_blank" rel="noopener noreferrer" title={url}
       className={cx(chip, "no-underline hover:border-signal/60 hover:text-signal hover:no-underline")}>
      <Icon size={13} aria-hidden className="shrink-0" />
      <span className="truncate">{label ?? autoLabel(href, kind)}</span>
      <ExternalLink size={11} aria-hidden className="shrink-0 opacity-60" />
    </a>
  );
}

/** Exact NASA file + row inside the repo's Bronze layer. Not a web link: click copies the full path#row. */
export function FileRowChip({ file, row }: { file: string | null | undefined; row: string | number | null | undefined }) {
  const [copied, setCopied] = useState(false);
  if (!file) return <span className={cx(chip, "italic text-faint")}>file not available</span>;
  const ref = `${file}#${row ?? "?"}`;
  const short = `${file.split("/").pop()}#${row ?? "?"}`;
  return (
    <button type="button" title={`${ref}\n(click to copy)`}
      onClick={() => { navigator.clipboard?.writeText(ref).then(() => { setCopied(true); setTimeout(() => setCopied(false), 1200); }); }}
      className={cx(chip, "hover:border-signal/60 hover:text-ink")}>
      <FileSpreadsheet size={13} aria-hidden className="shrink-0" />
      <span className="truncate">{short}</span>
      {copied ? <Check size={12} className="shrink-0 text-ok" aria-label="copied" /> : <Copy size={11} aria-hidden className="shrink-0 opacity-60" />}
    </button>
  );
}
