import { useEffect, useMemo, useState } from "react";
import { Streamdown, defaultRemarkPlugins } from "streamdown";
import { Button } from "@/components/ui/button";
import { ChevronLeft, ChevronRight, BookOpen, Calculator, Lightbulb, Flag } from "lucide-react";
import { DesignSolution, DesignStep, FigureParams } from "./types";
import { FootingFigure } from "./FootingFigure";
import { PhaseFigure } from "./PhaseFigure";
import { SlopeFigure, CulmannFigure } from "./SlopeFigure";
import { BracedCutFigure } from "./BracedCutFigure";
import { PileFigure } from "./PileFigure";
import { SheetPileFigure, CantileverWallFigure, WallThrustFigure } from "./WallFigure";
import { CircleSlopeFigure } from "./CircleSlopeFigure";
import { ConsolidationFigure } from "./ConsolidationFigure";
import { activeNotes, compareOp } from "./figShared";

// one router: every domain gets its own parametric figure component
function DesignFigure({ figure, steps, current }: {
  figure: FigureParams; steps: DesignStep[]; current: number;
}) {
  switch (figure.template) {
    case "phase_diagram":
      return <PhaseFigure params={figure} steps={steps} current={current} />;
    case "infinite_slope":
      return <SlopeFigure params={figure} steps={steps} current={current} />;
    case "culmann":
      return <CulmannFigure params={figure} steps={steps} current={current} />;
    case "braced_cut":
      return <BracedCutFigure params={figure} steps={steps} current={current} />;
    case "pile":
      return <PileFigure params={figure} steps={steps} current={current} />;
    case "sheet_pile":
      return <SheetPileFigure params={figure} steps={steps} current={current} />;
    case "cantilever_wall":
      return <CantileverWallFigure params={figure} steps={steps} current={current} />;
    case "lateral_wall":
      return <WallThrustFigure params={figure} steps={steps} current={current} />;
    case "consolidation":
      return <ConsolidationFigure params={figure} steps={steps} current={current} />;
    case "circular_slope":
      return <CircleSlopeFigure params={figure} steps={steps} current={current} />;
    default:
      return <FootingFigure params={figure} steps={steps} current={current} />;
  }
}

// values and comparisons live ON the figure for every template: chips at the
// top right, the comparison bars at the bottom right
function FigureOverlay({ steps, current }: { steps: DesignStep[]; current: number }) {
  const notes = activeNotes(steps, current);
  const cmp = compareOp(steps, current);
  const rows = cmp?.methods && cmp.methods.length > 1 ? cmp.methods : null;
  const maxQ = rows ? Math.max(...rows.map((r) => r.q_ult)) : 1;
  return (
    <>
      <div className="absolute top-2 right-2 flex flex-col items-end gap-1.5 pointer-events-none">
        {notes.map((n) => (
          <span key={n}
            className="rounded-full border border-primary/40 bg-white/95 px-3 py-1 font-mono text-[13px] text-foreground shadow-sm">
            {n}
          </span>
        ))}
      </div>
      {rows && (
        <div className="absolute bottom-2 right-2 rounded-lg border border-border bg-white/80 px-3 py-2 backdrop-blur-[2px] pointer-events-none">
          <p className="m-0 mb-1 text-[12px] font-semibold text-foreground">
            Result by method
          </p>
          {rows.map((r) => (
            <div key={r.method} className="flex items-center gap-2 py-0.5">
              <span className="w-20 text-[12px] text-foreground">{r.method}</span>
              <span className="h-3 rounded-sm bg-primary"
                style={{ width: `${Math.max((r.q_ult / maxQ) * 90, 5)}px`, opacity: 0.5 + 0.5 * (r.q_ult / maxQ) }} />
              <span className="text-[12px] font-mono text-muted-foreground">{r.q_ult}</span>
            </div>
          ))}
        </div>
      )}
    </>
  );
}

// Step-synchronised player: the step roll on the left, the figure on the
// right, both driven by one cursor. The event stream is the single source of
// truth; text, maths and drawing are three renderers of it.

const REMARK_PLUGINS = [
  defaultRemarkPlugins.gfm,
  [(defaultRemarkPlugins.math as unknown as [unknown, object])[0], { singleDollarTextMath: true }],
] as never[];

function Md({ children }: { children: string }) {
  return <Streamdown remarkPlugins={REMARK_PLUGINS}>{children}</Streamdown>;
}

function Tex({ tex, block = true }: { tex: string; block?: boolean }) {
  // multi-line TeX (aligned blocks) breaks the markdown math fence; KaTeX
  // does not need the newlines, so collapse them.
  const t = tex.replace(/\n/g, " ");
  return <Md>{block ? `$$${t}$$` : `$${t}$`}</Md>;
}

const KIND_META: Record<string, { label: string; icon: typeof Calculator; cls: string }> = {
  assume: { label: "Assumption", icon: Lightbulb, cls: "bg-chart-2/10 text-chart-2 border-chart-2/20" },
  lookup: { label: "Looked up", icon: BookOpen, cls: "bg-primary/10 text-primary border-primary/20" },
  compute: { label: "Computed", icon: Calculator, cls: "bg-primary/10 text-primary border-primary/20" },
  conclude: { label: "Conclusion", icon: Flag, cls: "bg-foreground/10 text-foreground border-foreground/20" },
  explain: { label: "Explanation", icon: Lightbulb, cls: "bg-muted text-muted-foreground border-border" },
};

// pretty-print a conclusion quantity: known symbols first, then a generic
// base + subscript split on "_" (P_A -> P with subscript A), Greek spelled out
const GREEK: Record<string, string> = {
  beta: "β", phi: "φ", gamma: "γ", alpha: "α", sigma: "σ", delta: "δ",
};
const QUANTITY_LABELS: Record<string, string> = {
  q_all: "qₐₗₗ", Q_all: "Qₐₗₗ", q_ult: "qᵤ", Q_ult: "Qᵤ",
  Fs: "Fₛ", FS: "Fₛ", c: "c′", su: "sᵤ", cu: "cᵤ",
};
function QuantityLabel({ q }: { q: string }) {
  if (QUANTITY_LABELS[q]) return <>{QUANTITY_LABELS[q]}</>;
  if (GREEK[q]) return <>{GREEK[q]}</>;
  const us = q.indexOf("_");
  if (us > 0) {
    const base = GREEK[q.slice(0, us)] ?? q.slice(0, us);
    return <>{base}<sub>{q.slice(us + 1)}</sub></>;
  }
  // trailing single letter after a capital reads as a subscript: Se, Pf, Mmax
  const m = q.match(/^([A-Z])([a-z]+|[a-z])$/);
  if (m && q !== "Fs") return <>{m[1]}<sub>{m[2]}</sub></>;
  return <>{q}</>;
}

function KindBadge({ step }: { step: DesignStep }) {
  const meta = KIND_META[step.kind] || KIND_META.explain;
  const Icon = meta.icon;
  return (
    <span className="inline-flex items-center gap-1.5">
      <span className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[10px] uppercase tracking-wide ${meta.cls}`}>
        <Icon className="w-3 h-3" />
        {meta.label}
      </span>
      {step.augmented && (
        <span className="rounded-full border border-border bg-muted px-2 py-0.5 text-[10px] uppercase tracking-wide text-muted-foreground">
          added explanation
        </span>
      )}
    </span>
  );
}

export function StepPlayer({ solution }: { solution: DesignSolution }) {
  const steps = solution.steps;
  const [current, setCurrent] = useState(0);
  const step = steps[current];

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "ArrowRight") setCurrent((c) => Math.min(c + 1, steps.length - 1));
      if (e.key === "ArrowLeft") setCurrent((c) => Math.max(c - 1, 0));
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [steps.length]);

  const sceneLabel = useMemo(() => {
    if (!step) return "";
    if (step.scene === "setup") return "Setting up the problem";
    if (step.scene === "results") return "Results";
    if (step.scene === "phases") return "The three-phase diagram";
    if (step.scene === "beams") return "The wall as beams between struts";
    if (step.scene === "slices") return "The sliding mass cut into slices";
    if (step.scene.startsWith("method:")) return `${step.scene.slice(7)}'s method`;
    return step.scene;
  }, [step]);

  if (!steps.length) return null;

  return (
    <div className="space-y-4">
      {/* givens block */}
      <div className="rounded-lg border bg-card p-4">
        <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground m-0 mb-1">
          Given
        </p>
        <Tex tex={solution.givens_tex} />
      </div>

      <div className="grid gap-4 lg:grid-cols-[1fr_1.05fr] items-start">
        {/* step roll */}
        <div className="space-y-1.5">
          {steps.map((s, i) => {
            const active = i === current;
            return (
              <button
                key={s.id}
                type="button"
                onClick={() => setCurrent(i)}
                className={[
                  "w-full text-left rounded-lg border px-3 py-2 transition-colors",
                  active
                    ? "border-primary/50 bg-primary/5 shadow-sm"
                    : "border-border bg-card hover:border-primary/30",
                ].join(" ")}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className={`text-sm ${active ? "font-semibold text-foreground" : "text-muted-foreground"}`}>
                    {i + 1}. {s.title}
                  </span>
                  {s.result && !active && (
                    <span className="text-xs font-mono text-muted-foreground whitespace-nowrap">
                      {s.result.display}
                    </span>
                  )}
                </div>

                {active && (
                  <div className="mt-2 space-y-2.5 cursor-default" onClick={(e) => e.stopPropagation()}>
                    <KindBadge step={s} />
                    {s.narration && (
                      <p className="text-sm text-foreground/90 m-0 leading-relaxed">{s.narration}</p>
                    )}
                    {s.equation_tex && (
                      <div className="rounded-md bg-muted/50 px-3 py-1.5 overflow-x-auto">
                        <Tex tex={s.equation_tex} />
                      </div>
                    )}
                    {s.substitution_tex && (
                      <div className="rounded-md bg-muted/30 px-3 py-1.5 overflow-x-auto">
                        <Tex tex={s.substitution_tex} />
                      </div>
                    )}
                    {s.result && (
                      <div className="inline-flex items-center gap-2 rounded-md border border-primary/30 bg-primary/5 px-3 py-1.5">
                        <span className="text-sm font-semibold text-primary">
                          {s.result.display}
                        </span>
                        {s.result.method && (
                          <span className="text-xs text-muted-foreground">({s.result.method})</span>
                        )}
                      </div>
                    )}
                    {s.provenance?.map((p, j) => (
                      <div key={j} className="rounded-md border border-primary/20 bg-primary/5 px-3 py-2 text-xs space-y-1">
                        <p className="m-0 font-medium text-primary">
                          {p.symbol}{p.value !== "" && p.value !== undefined ? ` = ${p.value}` : ""}
                        </p>
                        <p className="m-0 text-foreground/80">{p.means}.</p>
                        <p className="m-0 text-muted-foreground">
                          From {p.source}
                          {p.arguments?.length ? `, entered with ${p.arguments.join(", ")}` : ""}.
                        </p>
                        {p.whyApplies && (
                          <p className="m-0 text-muted-foreground">Why here: {p.whyApplies}.</p>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </button>
            );
          })}
        </div>

        {/* figure panel */}
        <div className="lg:sticky lg:top-4 space-y-2">
          <div className="rounded-lg border bg-card p-2">
            <p className="text-xs text-muted-foreground text-center m-0 mb-1">{sceneLabel}</p>
            <div className="relative">
              <DesignFigure figure={solution.figure} steps={steps} current={current} />
              <FigureOverlay steps={steps} current={current} />
            </div>
            {step?.figure_caption && (
              <p className="text-xs text-foreground/75 text-center m-0 mt-1.5 px-3 leading-relaxed">
                {step.figure_caption}
              </p>
            )}
          </div>
          <div className="flex items-center justify-between">
            <Button variant="outline" size="sm" onClick={() => setCurrent((c) => Math.max(c - 1, 0))}
              disabled={current === 0}>
              <ChevronLeft className="w-4 h-4" /> Previous
            </Button>
            <span className="text-xs text-muted-foreground">
              Step {current + 1} of {steps.length}
            </span>
            <Button variant="outline" size="sm"
              onClick={() => setCurrent((c) => Math.min(c + 1, steps.length - 1))}
              disabled={current === steps.length - 1}>
              Next <ChevronRight className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </div>

      {/* final answers + method comparison, shown once the roll is finished */}
      {current === steps.length - 1 && (
        <div className="space-y-3">
          <div className="rounded-lg border-2 border-primary/40 bg-primary/5 p-4">
            <p className="text-xs font-medium uppercase tracking-wide text-primary m-0 mb-2">
              Answer
            </p>
            <div className="flex flex-wrap gap-4">
              {solution.conclusions.map((c) => (
                <div key={c.quantity}>
                  <span className="text-lg font-semibold text-foreground">
                    <QuantityLabel q={c.quantity} />
                    {" = "}{c.value} {c.unit.replace("m^3", "m³").replace("m^2", "m²")}
                  </span>
                  <p className="text-xs text-muted-foreground m-0">
                    governing method: {c.governing}{c.FS ? `, FS = ${c.FS}` : ""}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {solution.comparison && solution.comparison.rows && (
            <div className="rounded-lg border bg-card p-4 space-y-2">
              <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground m-0">
                {solution.comparison.spread_pct != null
                  ? `Method comparison, spread ${solution.comparison.spread_pct}%`
                  : "Method comparison"}
              </p>
              <div className="overflow-x-auto">
                <table className="text-sm w-full">
                  <tbody>
                    {solution.comparison.rows.map((r) => (
                      <tr key={r.method} className="border-b last:border-0 border-border/60">
                        <td className="py-1.5 pr-4 font-medium">{r.method}</td>
                        <td className="py-1.5 pr-4 text-muted-foreground">{r.label}</td>
                        <td className="py-1.5 text-right font-mono">
                          {r.q_ult} {solution.comparison?.unit ?? "kPa"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <p className="text-sm text-foreground/85 m-0 leading-relaxed">
                {solution.comparison.explanation}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
