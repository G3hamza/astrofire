/** Domain vocabulary shared by every screen. Values come from the API contract
 *  (docs/DATA_CONTRACTS.md); unknown values fall through to a neutral style. */

export type OutcomeKind = "burned" | "out" | "blowoff" | "unknown";

/** Accepts both engine spellings: outcome ("burned" / "went out" / "blowoff")
 *  and outcome_class ("Burned" / "Extinction" / "No Ignition" / "Not Sustained" / "Blowoff"). */
export function outcomeKind(raw: string | null | undefined): OutcomeKind {
  const s = (raw ?? "").toLowerCase().trim();
  if (s === "burned") return "burned";
  if (s === "blowoff") return "blowoff";
  if (["went out", "extinction", "no ignition", "not sustained"].includes(s)) return "out";
  return "unknown";
}

export const OUTCOME_LABEL: Record<OutcomeKind, string> = {
  burned: "Burned",
  out: "Went out",
  blowoff: "Blowoff",
  unknown: "Not recorded",
};

export type BasisKind = "observed" | "inferred" | "assumed" | "not_recorded";

/** outcome_basis is observed / inferred / not_recorded; pressure_status starts with "assumed" or "measured". */
export function basisKind(raw: string | null | undefined): BasisKind {
  const s = (raw ?? "").toLowerCase();
  if (s.startsWith("observed") || s.startsWith("measured")) return "observed";
  if (s.startsWith("inferred")) return "inferred";
  if (s.startsWith("assumed")) return "assumed";
  return "not_recorded";
}

export const VERDICTS = [
  "Evidence suggests it burns",
  "Borderline in tested evidence",
  "Evidence suggests it goes out",
  "Insufficient validated experimental evidence",
] as const;

export type VerdictTone = "burn" | "caution" | "out" | "danger";

export function verdictTone(verdict: string): VerdictTone {
  if (verdict.startsWith("Insufficient")) return "danger";
  if (verdict.includes("burns")) return "burn";
  if (verdict.includes("goes out")) return "out";
  return "caution";
}
