// Shared palette and helpers for the design-mode figures.
export const FIG = {
  SOIL_FILL: "#f3e9dd",
  SOIL_HATCH: "#9a6b3f",
  SAND: "#c9bb8e",
  INK: "#334155",
  DIM: "#64748b",
  WATER: "#2272b5",
  SLIP: "#b91c1c",
  HL: "#f59e0b",
  AMBER: "#b45309",
};

import { DesignStep, VizOp } from "./types";

export function activeTargets(steps: DesignStep[], current: number): Set<string> {
  const set = new Set<string>();
  (steps[current]?.viz || []).forEach((v) => {
    if (v.op === "highlight" && v.target) set.add(v.target);
  });
  return set;
}

export function activeNotes(steps: DesignStep[], current: number): string[] {
  return (steps[current]?.viz || [])
    .filter((v) => v.op === "note" && v.text)
    .map((v) => v.text as string);
}

export function compareOp(steps: DesignStep[], current: number): VizOp | undefined {
  return (steps[current]?.viz || []).find((v) => v.op === "compare");
}

// accumulating op: once shown, stays shown when scrubbing forward
export function accumulated(steps: DesignStep[], current: number, op: string): VizOp | undefined {
  for (let i = current; i >= 0; i--) {
    const found = (steps[i]?.viz || []).find((v) => v.op === op);
    if (found) return found;
  }
  return undefined;
}
