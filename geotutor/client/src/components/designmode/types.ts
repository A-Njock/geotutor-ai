// Contracts for Mode 2 (Geotech Design). Mirrors src/designmode/solver.py.

export interface ClarifyOption {
  value: string;
  label: string;
}

export interface ClarifyQuestion {
  id: string;
  question: string;
  options: ClarifyOption[];
  allow_custom: boolean;
  custom_hint?: string;
}

export interface DesignAnalysis {
  ok: boolean;
  message?: string;
  frame: Record<string, unknown>;
  givens: Record<string, number>;
  repairs: string[];
  violations: string[];
  skeptic: { agrees: boolean; reason: string } | null;
  methods: { id: string; label: string; method: string }[];
  rejections: string[];
  questions: ClarifyQuestion[];
  missing: string[];
  ready: boolean;
}

export interface Provenance {
  symbol: string;
  value: number | string;
  means: string;
  source: string;
  arguments: string[];
  whyApplies: string;
}

export interface VizOp {
  op: string;
  target?: string;
  text?: string;
  Bp?: number;
  methods?: { method: string; q_ult: number }[];
}

export interface DesignStep {
  id: string;
  kind: "assume" | "lookup" | "compute" | "conclude" | "explain";
  title: string;
  scene: string;
  narration: string;
  equation_tex?: string;
  substitution_tex?: string;
  result?: { sym: string; value: number; unit: string; display: string; method?: string };
  provenance?: Provenance[];
  viz?: VizOp[];
  augmented?: boolean;
  figure_caption?: string;
}

export interface FigureParams {
  template: string;
  shape?: string;
  B?: number;
  L?: number | null;
  Df?: number;
  Dw?: number | null;
  soil_type?: string;
  gamma?: number | null;
  phi?: number | null;
  c?: number | null;
  su?: number | null;
  load_label?: string | null;
  methods?: { method: string; q_ult: number }[];
  // domain figures carry their own parameters (H, dA..dC, beta, z, V, ...)
  [key: string]: unknown;
}

export interface DesignSolution {
  ok: boolean;
  message?: string;
  statement: string;
  frame_summary: Record<string, string>;
  givens_tex: string;
  steps: DesignStep[];
  results: { method: string; label: string; q_ult: number }[];
  conclusions: { quantity: string; value: number; unit: string; governing: string; FS?: number }[];
  comparison: {
    low?: number; high?: number; spread_pct?: number; explanation: string;
    unit?: string;
    rows: { method: string; label: string; q_ult: number }[];
  } | null;
  figure: FigureParams;
  audit: Record<string, unknown>;
}

