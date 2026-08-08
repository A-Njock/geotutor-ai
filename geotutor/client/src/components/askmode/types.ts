// Answer contract returned by POST /ask-grounded (Mode 1 brain).

export interface StratumData {
  n: number;
  doc_type: "book" | "paper" | "thesis" | "exam" | "standard" | "other";
  title: string;
  section_path: string;
  authors: string | null;
  year: number | null;
  topic: string;
  weight: number; // 0..1, normalised within the answer
  excerpt: string;
  rel_path: string;
  parent_id: number;
  carried_over: boolean;
  sub_question: number; // index into sub_answers
}

export interface SubAnswer {
  label: string | null; // "a", "b" ... only when 2+ sub-questions
  question: string;
  answer_markdown: string; // contains [n] citation markers
  evidence: "strong" | "adequate" | "weak" | "none";
  strata_used: number[];
}

export interface DivergenceMethod {
  name: string;
  value: string;
  result: string;
}

export interface Divergence {
  agree: string[];
  methods: DivergenceMethod[];
  guidance: string;
}

export interface Passport {
  formula: string;
  source_n: number;
  variables: { symbol: string; meaning: string; units: string }[];
  valid: string[];
  not_valid: string[];
}

export interface GroundedResult {
  sub_answers: SubAnswer[];
  strata: StratumData[];
  divergence: Divergence | null;
  passports: Passport[];
  intent: string;
}
