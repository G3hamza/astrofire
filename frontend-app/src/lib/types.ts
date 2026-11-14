/** API types, written from the real responses saved in frontend-app/samples/.
 *  (The FastAPI app declares no response models, so /openapi.json only has request schemas.)
 *  CSV-backed endpoints return every field as a string; engine endpoints return numbers. */

export type MissionKey = "iss" | "exploration" | "moon" | "mars";
export type Mission = { name: string; gravity_g: number; o2_pct: number; pressure_kpa: number };
export type Missions = Record<MissionKey, Mission>;

export type Stats = {
  tests: number; with_conditions: number; outcomes_observed: number;
  investigations_with_tables: number; investigations_total: number;
  droplet_flame_tests: number; gas_flame_tests: number; o2_range_tested: [number, number];
};

export type Kpi = { kpi: string; formula: string; value: string; unit: string; refreshed_at: string };
export type MissionCoverage = {
  mission: string; gravity_g: string; o2_pct: string; pressure_kpa: string;
  space_solid_tests_near: string; space_tests_near_observed_outcome: string; rule: string;
};
export type OutcomeSummary = { investigation: string; outcome_class: string; outcome_basis: string; tests: string };
export type Overview = { kpis: Kpi[]; mission_coverage: MissionCoverage[]; outcomes: OutcomeSummary[] };

export type MaterialFamily = { material: string; tests: number; tests_material_named: number; tests_material_inferred: number };

export type ScenarioRequest = {
  material: string; mission?: MissionKey | null;
  gravity_g?: number; o2_pct?: number; pressure_kpa?: number; flow_cm_s?: number;
};
export type EvidenceRow = {
  test_id: string; investigation: string; material: string; material_family: string; material_identity: string;
  same_material: boolean; o2_pct: number | null; flow_cm_s: number | null; gravity_g: number; pressure_kpa: number | null;
  pressure_status: string; outcome: string; outcome_basis: string; distance: number; biggest_difference: string;
  raw: string; source_file: string; source_row: string; psi_url: string; doi: string | null;
};
export type PartialGravityRef = {
  material: string; o2_margin_vs_1g_points: number; pressure_psia: string; meaning: string; source_url: string;
};
export type SupportingTest = {
  test_id: string; program: string; platform: string; evidence_tier: string; material: string; material_family: string;
  same_material: boolean; gravity_g: number; gravity_status: string; o2_pct: number; o2_status: string;
  pressure_kpa: number; pressure_status: string; flow_cm_s: number | null; flow_direction: string;
  outcome: string; outcome_basis: string; outcome_note: string; distance: number; biggest_difference: string;
  source_url: string; source_location: string;
};
export type AtmosphereTest = {
  test_id: string; investigation: string; kind: "droplet flame" | "gas flame"; test_end_raw?: string;
  fuel: string; o2_pct: number; pressure_kpa: number; diluent: string; gravity_g: number;
  outcome: string; outcome_basis: string; burn_time_s: number | null; droplet_initial_diameter_mm: number | null;
  distance: number; source_file: string; source_row: string; psi_url: string; note: string;
};
export type WhyUntested = { topic: "gravity" | "oxygen" | "pressure"; text: string; source_url: string };
export type LiteratureTest = Record<string, string>;

export type ScenarioResult = {
  scenario: { material: string; gravity_g: number; o2_pct: number; pressure_kpa: number; flow_cm_s: number };
  verdict: string; evidence_status: string; confidence: string;
  nearby_tendency: string; nearby_burn_share: number | null; nearby_burn_share_note: string;
  evidence_distance: number | null; blockers: string[]; flags: string[];
  evidence: EvidenceRow[]; why_untested: WhyUntested[]; atmosphere_evidence: AtmosphereTest[];
  gravity_bounds?: GravityBounds | null;
};
export type GravityBounds = {
  requested_gravity_g: number; bounds_cover_request: boolean; applies: string; basis: string;
  lower_bound: { tests: number; outcomes: Record<string, number>; outcome_basis?: Record<string, number>; o2_range: [number, number] | null; pressure: string; note: string | null };
  upper_bound: { tests: number; note: string | null; pairs: { test_id: string; material: string; o2_pct: number | null; microgravity_burn_length: string;
    one_g_burn_length: string; microgravity_outcome: string; source_file: string; source_row: string; psi_url: string }[] };
  partial_gravity_mimic: { investigation: string; url: string; text: string };
  coming_next: { name: string; status: string }[];
};

export type GapCell = {
  gravity_g: number; o2_range: string; pressure: string; space_tests: number;
  mission_design_points: string[]; note: string; droplet_tests: number; gas_flame_tests: number;
};

export type Passage = {
  chunk_id: string; document_id: string; chunk_index: number; page: number | null;
  title: string; year: string; url: string; topic: string; related_investigations: string[];
  content_type: string; text: string; score: number;
};
export type AskSource = { n: number; title: string; year: string; url: string; text: string };
export type AskResult = {
  mode: "ai" | "extractive"; answer: string | null; uncited_sentences?: string[]; error?: string; model?: string; sources: AskSource[];
};

export type MapPoint = {
  test_id: string; investigation: string; material: string; material_identity: string;
  o2_pct: number; flow_cm_s: number; outcome: "burned" | "went out" | "blowoff"; outcome_class: string;
  outcome_basis: string; raw: string; source_file: string; source_row: string; psi_url: string;
};

export type PartialGravityRow = {
  material: string; pressure_psia: string;
  g1_uloi: string; g1_moc: string; mars_uloi: string; mars_moc: string; moon_uloi: string; moon_moc: string;
  zero_g_uloi: string; zero_g_moc: string;
  mars_margin_o2: string; moon_margin_o2: string; zero_g_margin_o2: string;
  source_ntrs_id: string; source_url: string; source_table: string; source_paper: string; value_status: string; units: string;
};

export type MaterialOverview = {
  material_id: string; material: string; family: string; candidate_family: string; classification_basis: string;
  investigations: string; samples: string; solid_flame_tests: string; observed_outcomes: string;
  burned: string; went_out: string; properties_available: string; properties_missing: string;
};
export type MaterialDetail = {
  material: Record<string, string | null>; overview: Partial<MaterialOverview>;
  samples: Record<string, string>[]; sample_count: number; properties: Record<string, string>[];
  evidence_limitations: string[];
};

export type DataQuality = {
  tables: { table: string; records: string; valid: string; warnings: string; pct_valid: string }[];
  quarantine: { investigation: string; rule: string; severity: string; records: number }[];
};

export type CsvRow = Record<string, string>;
