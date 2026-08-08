import { useEffect, useMemo, useRef, useState } from "react";
import { Streamdown, defaultRemarkPlugins } from "streamdown";

// Streamdown disables $...$ inline math by default; re-enable it so the
// tutor's answers show real mathematical notation everywhere.
const REMARK_PLUGINS = [
  defaultRemarkPlugins.gfm,
  [(defaultRemarkPlugins.math as unknown as [unknown, object])[0], { singleDollarTextMath: true }],
] as never[];

import { GroundedResult, StratumData, Passport } from "./types";
import { EvidenceBorehole, BoreholeLegend, STRATUM_COLORS } from "./EvidenceBorehole";

function Md({ children }: { children: string }) {
  return <Streamdown remarkPlugins={REMARK_PLUGINS}>{children}</Streamdown>;
}

// Renders the Mode-1 answer contract: sub-answers with citation chips,
// per-sub-answer Evidence Boreholes, Formula Passports and the Divergence
// Panel (both only when present), plus the click-to-open passage viewer.

const TYPE_LABEL: Record<string, string> = {
  book: "Book", paper: "Paper", thesis: "Thesis", standard: "Standard",
  exam: "Exam", other: "Source",
};

// How a source is named in the passage viewer, per document type.
// Books read as a recommendation; papers show title plus authors and year;
// section headings are never shown (they confused more than they helped).
function sourceLabel(s: StratumData): string {
  if (!s.title) return ""; // an uninformative heading shows nothing at all
  if (s.doc_type === "book") return `Recommended Book: ${s.title}`;
  if (s.doc_type === "paper" || s.doc_type === "thesis") {
    return s.authors && s.year ? `${s.title} · ${s.authors} (${s.year})` : s.title;
  }
  return s.title;
}

function CitedMarkdown({
  markdown, strata, activeN, onHover, onSelect,
}: {
  markdown: string;
  strata: StratumData[];
  activeN: number | null;
  onHover: (n: number | null) => void;
  onSelect: (n: number) => void;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const typeByN = useMemo(
    () => Object.fromEntries(strata.map((s) => [s.n, s.doc_type])),
    [strata]
  );

  // Replace [n] text markers with chip buttons after markdown renders.
  useEffect(() => {
    const root = ref.current;
    if (!root) return;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    const targets: Text[] = [];
    let node: Node | null;
    while ((node = walker.nextNode())) {
      if (/\[\d+\]/.test(node.nodeValue || "")) targets.push(node as Text);
    }
    targets.forEach((t) => {
      const parts = (t.nodeValue || "").split(/\[(\d+)\]/);
      if (parts.length < 3) return;
      const frag = document.createDocumentFragment();
      parts.forEach((p, i) => {
        if (i % 2 === 1) {
          const type = typeByN[Number(p)] || "other";
          const colors = STRATUM_COLORS[type] ?? STRATUM_COLORS.other;
          const b = document.createElement("button");
          b.type = "button";
          b.textContent = p;
          b.dataset.chip = p;
          b.title = `Source ${p}: click to see the passage`;
          b.style.cssText =
            "display:inline-flex;align-items:center;justify-content:center;" +
            "min-width:20px;height:18px;padding:0 6px;margin:0 2px;" +
            "border-radius:999px;font-family:ui-monospace,monospace;" +
            "font-size:11px;font-weight:600;line-height:1;cursor:pointer;" +
            "vertical-align:2px;transition:all .15s;" +
            `border:1.3px solid ${colors.stroke};background:${colors.fill};color:${colors.stroke};`;
          frag.appendChild(b);
        } else if (p) {
          frag.appendChild(document.createTextNode(p));
        }
      });
      t.parentNode?.replaceChild(frag, t);
    });
  }, [markdown, typeByN]);

  // Delegated interaction + active highlight.
  useEffect(() => {
    const root = ref.current;
    if (!root) return;
    root.querySelectorAll<HTMLButtonElement>("[data-chip]").forEach((b) => {
      const n = Number(b.dataset.chip);
      const isActive = n === activeN;
      const type = typeByN[n] || "other";
      const colors = STRATUM_COLORS[type] ?? STRATUM_COLORS.other;
      b.style.background = isActive ? "#2563eb" : colors.fill;
      b.style.borderColor = isActive ? "#2563eb" : colors.stroke;
      b.style.color = isActive ? "#ffffff" : colors.stroke;
    });
    const click = (e: Event) => {
      const el = (e.target as HTMLElement).closest("[data-chip]") as HTMLElement | null;
      if (el) onSelect(Number(el.dataset.chip));
    };
    const over = (e: Event) => {
      const el = (e.target as HTMLElement).closest("[data-chip]") as HTMLElement | null;
      if (el) onHover(Number(el.dataset.chip));
    };
    const out = (e: Event) => {
      const el = (e.target as HTMLElement).closest("[data-chip]") as HTMLElement | null;
      if (el) onHover(null);
    };
    root.addEventListener("click", click);
    root.addEventListener("mouseover", over);
    root.addEventListener("mouseout", out);
    return () => {
      root.removeEventListener("click", click);
      root.removeEventListener("mouseover", over);
      root.removeEventListener("mouseout", out);
    };
  }, [activeN, typeByN, onHover, onSelect]);

  return (
    <div ref={ref} className="prose prose-sm max-w-none">
      <Md>{markdown}</Md>
    </div>
  );
}

// Units arrive as plain text with caret exponents ("kN/m^2"); convert the
// exponents to real superscripts so units read properly without italic math.
const SUPERSCRIPTS: Record<string, string> = {
  "0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴",
  "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹", "-": "⁻",
};
function fmtUnits(u: string): string {
  return u
    .replace(/\^\{(-?\d+)\}/g, (_, d: string) => [...d].map((c) => SUPERSCRIPTS[c] ?? c).join(""))
    .replace(/\^(-?\d+)/g, (_, d: string) => [...d].map((c) => SUPERSCRIPTS[c] ?? c).join(""));
}

// Wrap prose word-runs inside a math segment in \text{} so they stay upright
// instead of being typeset letter-by-letter as variables.
function protectProse(seg: string): string {
  return seg.replace(
    /(?<!\\)((?:\b[A-Za-z]{3,}\b[ ,;:]*){2,})/g,
    (m) => `\\text{${m}}`
  );
}

// Renders math from the brain robustly, whatever mix arrives:
// bare LaTeX, $-delimited spans, prose, or all three in one string.
function MathTex({ tex }: { tex: string }) {
  let src = tex;
  if (!src.includes("$")) {
    if (/[\\^_{]/.test(src)) src = `$${protectProse(src)}$`;
  } else {
    src = src
      .split(/(\$[^$]*\$)/)
      .map((seg) => {
        if (seg.startsWith("$")) return seg;
        if (/\\[a-zA-Z]+|[_^]\{|\^\d/.test(seg)) return `$${protectProse(seg)}$`;
        return seg;
      })
      .join("");
  }
  return (
    <span className="[&_p]:m-0 [&_p]:inline">
      <Md>{src}</Md>
    </span>
  );
}

function PassportCard({ passport }: { passport: Passport }) {
  return (
    <div className="border border-gray-200 border-t-2 border-t-amber-600 rounded-b-md bg-white text-sm my-4">
      <div className="flex items-center gap-2 px-4 py-2 bg-gray-50 border-b border-gray-200">
        <span className="font-mono text-[10px] uppercase tracking-widest text-amber-700 font-semibold">
          Formula
        </span>
        <span className="ml-2 text-gray-800"><MathTex tex={passport.formula} /></span>
      </div>
      {passport.variables.length > 0 && (
        <table className="w-full border-collapse">
          <tbody>
            {passport.variables.map((v, i) => (
              <tr key={i} className="border-b border-gray-100 last:border-0">
                <td className="px-4 py-1.5 w-20 whitespace-nowrap"><MathTex tex={v.symbol} /></td>
                <td className="px-2 py-1.5 text-gray-700">{v.meaning}</td>
                <td className="px-4 py-1.5 font-mono text-xs text-gray-500 w-24">
                  {/[\\$]/.test(v.units) ? <MathTex tex={v.units} /> : fmtUnits(v.units)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      <div className="flex flex-wrap gap-2 px-4 py-2.5">
        {passport.valid.map((c, i) => (
          <span key={i} className="inline-block max-w-full break-words font-mono text-[11px] px-2.5 py-0.5 rounded-2xl bg-blue-50 text-blue-700">
            valid: <MathTex tex={c} />
          </span>
        ))}
        {passport.not_valid.map((c, i) => (
          <span key={i} className="inline-block max-w-full break-words font-mono text-[11px] px-2.5 py-0.5 rounded-2xl bg-orange-50 text-orange-700">
            not valid: <MathTex tex={c} />
          </span>
        ))}
        {passport.valid.length === 0 && passport.not_valid.length === 0 && (
          <span className="font-mono text-[11px] px-2.5 py-0.5 rounded-full bg-gray-100 text-gray-500">
            validity conditions not stated in source
          </span>
        )}
      </div>
    </div>
  );
}

export function GroundedAnswer({ result }: { result: GroundedResult }) {
  const [activeN, setActiveN] = useState<number | null>(null);
  const [openN, setOpenN] = useState<number | null>(null);

  const strataByN = useMemo(
    () => Object.fromEntries(result.strata.map((s) => [s.n, s])),
    [result.strata]
  );
  const openStratum = openN != null ? strataByN[openN] : undefined;
  const multi = result.sub_answers.length > 1;

  const highlight = activeN ?? openN;
  const onSelect = (n: number) => setOpenN((cur) => (cur === n ? null : n));
  const hasEvidence = result.strata.length > 0;

  // passports shown after the sub-answer that cites their source
  const passportsFor = (sub: number): Passport[] =>
    result.passports.filter((p) => {
      const st = strataByN[p.source_n];
      const idx = st ? st.sub_question : 0;
      return idx === sub || (idx >= result.sub_answers.length && sub === result.sub_answers.length - 1);
    });

  return (
    <div className="space-y-6">
      <div className="bg-gray-50 rounded-lg border border-gray-200 overflow-hidden">
        <div className={hasEvidence ? "grid md:grid-cols-[1fr_240px]" : ""}>
          {/* answers */}
          <div className="p-6 md:p-8 min-w-0">
            {result.sub_answers.map((sa, i) => (
              <div key={i} className={i > 0 ? "mt-6 pt-5 border-t border-dashed border-gray-300" : ""}>
                {multi && (
                  <div className="mb-2">
                    <span className="font-mono text-[11px] uppercase tracking-widest text-blue-700">
                      Question {sa.label}
                    </span>
                    <h3 className="text-base font-semibold text-gray-900">{sa.question}</h3>
                  </div>
                )}
                <CitedMarkdown
                  markdown={sa.answer_markdown}
                  strata={result.strata}
                  activeN={highlight}
                  onHover={setActiveN}
                  onSelect={onSelect}
                />
                {passportsFor(i).map((p, j) => (
                  <PassportCard key={j} passport={p} />
                ))}
              </div>
            ))}
          </div>

          {/* borehole rail (only when the answer actually has evidence) */}
          {hasEvidence && (
          <aside className="border-t md:border-t-0 md:border-l border-gray-200 bg-white p-5 flex flex-col gap-4">
            <h3 className="font-mono text-[11px] uppercase tracking-widest text-gray-500 font-semibold m-0">
              Evidence borehole
            </h3>
            {result.sub_answers.map((sa, i) => {
              const strata = result.strata.filter((s) => s.sub_question === i);
              if (strata.length === 0) return null;
              return (
                <div key={i}>
                  {multi && (
                    <div className="font-mono text-[11px] text-gray-500 mb-1">Q-{sa.label}</div>
                  )}
                  <EvidenceBorehole
                    strata={strata}
                    evidence={sa.evidence}
                    activeN={highlight}
                    onHover={setActiveN}
                    onSelect={onSelect}
                    patternIdPrefix={`bh${i}`}
                  />
                </div>
              );
            })}
            <BoreholeLegend
              types={[...new Set(result.strata.map((s) => s.doc_type))]}
            />
          </aside>
          )}
        </div>

        {/* passage viewer */}
        {openStratum && (
          <div className="mx-6 md:mx-8 mb-6 border border-gray-200 rounded-md bg-white p-4 text-sm">
            <div className="flex flex-wrap gap-2 items-center font-mono text-[11px] text-gray-500 mb-2">
              <span className="border border-gray-200 rounded-full px-2.5 py-0.5 bg-gray-50">
                {TYPE_LABEL[openStratum.doc_type]}
              </span>
              <span className="border border-gray-200 rounded-full px-2.5 py-0.5 bg-gray-50">
                weight {(openStratum.weight * 100).toFixed(0)}%
              </span>
              <span className="text-gray-600">{sourceLabel(openStratum)}</span>
            </div>
            <blockquote className="m-0 pl-3 border-l-2 border-blue-600 text-gray-700 font-serif [&_p]:m-0">
              <Md>{`${openStratum.excerpt}…`}</Md>
            </blockquote>
          </div>
        )}
      </div>

      {/* divergence panel */}
      {result.divergence && (
        <div>
          <div className="font-mono text-[11px] uppercase tracking-widest text-gray-500 font-semibold mb-2">
            Consensus and Misconstrual on the Question
          </div>
          <div className="grid md:grid-cols-2 gap-4">
            <div className="rounded-lg border border-blue-200 bg-blue-50 p-5 text-sm">
              <h4 className="font-mono text-xs uppercase tracking-wider text-blue-700 font-semibold mb-2 mt-0">
                Consensus
              </h4>
              <ul className="m-0 pl-5 space-y-1.5 text-gray-800">
                {result.divergence.agree.map((a, i) => (
                  <li key={i}>
                    <CitedMarkdown
                      markdown={a}
                      strata={result.strata}
                      activeN={highlight}
                      onHover={setActiveN}
                      onSelect={onSelect}
                    />
                  </li>
                ))}
              </ul>
            </div>
            <div className="rounded-lg border border-orange-200 bg-orange-50 p-5 text-sm">
              <h4 className="font-mono text-xs uppercase tracking-wider text-orange-700 font-semibold mb-2 mt-0">
                Misconstrual
              </h4>
              {result.divergence.methods.length > 0 && (
                <div className="rounded-md border border-gray-200 bg-white overflow-hidden mb-2 divide-y divide-gray-100">
                  {result.divergence.methods.map((m, i) => (
                    <div key={i} className="px-4 py-2.5 flex flex-wrap items-baseline gap-x-3 gap-y-1">
                      <span className="font-mono text-[10px] uppercase tracking-wider text-gray-500 shrink-0">
                        <MathTex tex={m.name} />
                      </span>
                      <span className="text-sm font-medium text-gray-900">
                        <MathTex tex={m.value} />
                      </span>
                      {m.result && (
                        <span className="text-xs text-gray-500 w-full [&_p]:m-0 [&_p]:inline">
                          <CitedMarkdown
                            markdown={m.result}
                            strata={result.strata}
                            activeN={highlight}
                            onHover={setActiveN}
                            onSelect={onSelect}
                          />
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              )}
              <div className="italic text-gray-600 text-[13px]"><MathTex tex={result.divergence.guidance} /></div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
