import { StratumData } from "./types";

// One borehole log per (sub-)answer: each stratum is a source, thickness is its
// contribution, hatch pattern encodes the document type, dashed frame means the
// source is carried over from an earlier turn.

// Colors derived from the app theme (index.css): chart-2 earthy accent,
// primary professional blue, chart-1 calming green, slate, warm gray.
export const STRATUM_COLORS: Record<string, { stroke: string; fill: string }> = {
  book: { stroke: "#9a6b3f", fill: "#f3e9dd" },      // earthy accent: cohesive layer
  paper: { stroke: "#2272b5", fill: "#e3eef7" },     // primary blue: granular layer
  thesis: { stroke: "#34946f", fill: "#e6f4ee" },    // calming green: silt
  standard: { stroke: "#475569", fill: "#f1f5f9" },  // slate: bedrock
  exam: { stroke: "#57534e", fill: "#f5f5f4" },      // warm gray: thin seam
  other: { stroke: "#9ca3af", fill: "#f9fafb" },
};

const DEPTH_BY_EVIDENCE: Record<string, number> = {
  strong: 300,
  adequate: 200,
  weak: 110,
  none: 40,
};

const PX_PER_METRE = 60;
const MAX_DEPTH_PX = 300; // the scale always shows the full 5 m gauge

interface Props {
  strata: StratumData[];
  evidence: "strong" | "adequate" | "weak" | "none";
  activeN: number | null;
  onHover: (n: number | null) => void;
  onSelect: (n: number) => void;
  patternIdPrefix: string; // unique per borehole instance on the page
}

function HatchPatterns({ prefix }: { prefix: string }) {
  return (
    <defs>
      <pattern id={`${prefix}-book`} width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
        <rect width="8" height="8" fill={STRATUM_COLORS.book.fill} />
        <line x1="0" y1="0" x2="0" y2="8" stroke={STRATUM_COLORS.book.stroke} strokeWidth="1.3" />
      </pattern>
      <pattern id={`${prefix}-paper`} width="9" height="9" patternUnits="userSpaceOnUse">
        <rect width="9" height="9" fill={STRATUM_COLORS.paper.fill} />
        <circle cx="2.5" cy="2.5" r="1.1" fill={STRATUM_COLORS.paper.stroke} />
        <circle cx="6.5" cy="6.5" r="1.1" fill={STRATUM_COLORS.paper.stroke} />
      </pattern>
      <pattern id={`${prefix}-thesis`} width="6" height="8" patternUnits="userSpaceOnUse">
        <rect width="6" height="8" fill={STRATUM_COLORS.thesis.fill} />
        <line x1="3" y1="0" x2="3" y2="8" stroke={STRATUM_COLORS.thesis.stroke} strokeWidth="1" />
      </pattern>
      <pattern id={`${prefix}-standard`} width="12" height="8" patternUnits="userSpaceOnUse">
        <rect width="12" height="8" fill={STRATUM_COLORS.standard.fill} />
        <path d="M0 0 H12 M0 8 H12 M4 0 V4 M10 4 V8" stroke={STRATUM_COLORS.standard.stroke} strokeWidth="1" fill="none" />
      </pattern>
      <pattern id={`${prefix}-exam`} width="8" height="5" patternUnits="userSpaceOnUse">
        <rect width="8" height="5" fill={STRATUM_COLORS.exam.fill} />
        <line x1="0" y1="2.5" x2="8" y2="2.5" stroke={STRATUM_COLORS.exam.stroke} strokeWidth="1.2" />
      </pattern>
      <pattern id={`${prefix}-other`} width="8" height="8" patternUnits="userSpaceOnUse">
        <rect width="8" height="8" fill={STRATUM_COLORS.other.fill} />
        <line x1="0" y1="8" x2="8" y2="0" stroke={STRATUM_COLORS.other.stroke} strokeWidth="1" />
      </pattern>
    </defs>
  );
}

export function EvidenceBorehole({ strata, evidence, activeN, onHover, onSelect, patternIdPrefix }: Props) {
  const totalDepthPx = DEPTH_BY_EVIDENCE[evidence] ?? 110;
  const top = 12;
  const colX = 40;
  const colW = 100;

  // most load-bearing at the bottom, like real ground
  const ordered = [...strata].sort((a, b) => a.weight - b.weight);
  const weightSum = ordered.reduce((s, x) => s + x.weight, 0) || 1;

  let y = top;
  const rows = ordered.map((s) => {
    const h = Math.max(20, (s.weight / weightSum) * totalDepthPx);
    const row = { s, y, h };
    y += h;
    return row;
  });
  const bottomY = y;
  const gaugeBottom = top + MAX_DEPTH_PX;
  const height = gaugeBottom + 14;
  const metres = (bottomY - top) / PX_PER_METRE;

  // the scale always runs to the maximum depth, so the empty part of the
  // hole shows how far the evidence COULD reach
  const ticks: number[] = [];
  for (let m = 0; m * PX_PER_METRE <= MAX_DEPTH_PX + 1; m++) ticks.push(m);

  return (
    <div className="flex flex-col gap-1">
      <svg
        width="190"
        height={height}
        viewBox={`0 0 190 ${height}`}
        role="img"
        aria-label={`Evidence borehole: ${strata.length} sources, evidence ${evidence}`}
      >
        <HatchPatterns prefix={patternIdPrefix} />
        {/* depth scale */}
        <g fontFamily="ui-monospace, monospace" fontSize="9" fill="#6b7280">
          <line x1={colX - 8} y1={top} x2={colX - 8} y2={gaugeBottom} stroke="#e5e7eb" strokeWidth="1" />
          {ticks.map((m) => (
            <g key={m}>
              <text x={colX - 13} y={top + m * PX_PER_METRE + 3.5} textAnchor="end">{m}</text>
              <line x1={colX - 12} y1={top + m * PX_PER_METRE} x2={colX - 4} y2={top + m * PX_PER_METRE} stroke="#9ca3af" />
            </g>
          ))}
        </g>
        {/* strata */}
        {rows.map(({ s, y: sy, h }) => {
          const colors = STRATUM_COLORS[s.doc_type] ?? STRATUM_COLORS.other;
          const active = activeN === s.n;
          return (
            <g
              key={s.n}
              role="button"
              tabIndex={0}
              className="cursor-pointer focus:outline-none"
              onMouseEnter={() => onHover(s.n)}
              onMouseLeave={() => onHover(null)}
              onClick={() => onSelect(s.n)}
              onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); onSelect(s.n); } }}
              aria-label={`Source ${s.n}: ${s.title} (${s.doc_type}), weight ${(s.weight * 100).toFixed(0)}%`}
            >
              <rect x={colX} y={sy} width={colW} height={h} fill={`url(#${patternIdPrefix}-${s.doc_type})`} opacity={active ? 0.65 : 1} />
              <rect
                x={colX} y={sy} width={colW} height={h} fill="none"
                stroke={active ? "#2563eb" : colors.stroke}
                strokeWidth={active ? 2.2 : 1.3}
              />
              <circle cx={colX + colW + 16} cy={sy + h / 2} r="9" fill={active ? "#2563eb" : "#ffffff"} stroke={active ? "#2563eb" : "#6b7280"} strokeWidth="1" />
              <text
                x={colX + colW + 16} y={sy + h / 2 + 3.5} textAnchor="middle"
                fontFamily="ui-monospace, monospace" fontSize="10.5" fontWeight="600"
                fill={active ? "#ffffff" : "#374151"}
              >
                {s.n}
              </text>
            </g>
          );
        })}
        {/* unexplored part of the hole: how deep the evidence could go */}
        {bottomY < gaugeBottom - 2 && (
          <rect
            x={colX} y={bottomY} width={colW} height={gaugeBottom - bottomY}
            fill="none" stroke="#d1d5db" strokeWidth="1" strokeDasharray="4 4"
          />
        )}
        {/* ground line */}
        <line x1={colX - 6} y1={top} x2={colX + colW + 6} y2={top} stroke="#1f2937" strokeWidth="1.6" />
      </svg>
      <div className="font-mono text-[11px] text-gray-500">
        evidence depth:{" "}
        <span className={
          evidence === "strong" ? "text-green-600 font-semibold" :
          evidence === "adequate" ? "text-amber-600 font-semibold" :
          "text-red-500 font-semibold"
        }>
          {metres.toFixed(1)} of {(MAX_DEPTH_PX / PX_PER_METRE).toFixed(1)} m ({evidence})
        </span>
      </div>
    </div>
  );
}

export function BoreholeLegend({ types }: { types: string[] }) {
  // only the document types actually present in this answer are listed
  const all: { type: keyof typeof STRATUM_COLORS; label: string }[] = [
    { type: "book", label: "Book (cohesive layer)" },
    { type: "paper", label: "Paper (granular layer)" },
    { type: "thesis", label: "Thesis (silt)" },
    { type: "standard", label: "Standard (bedrock)" },
    { type: "other", label: "Other source" },
  ];
  const items = all.filter((it) => types.includes(it.type));
  return (
    <div className="grid gap-1 text-xs text-gray-500">
      {items.map((it) => (
        <div key={it.type} className="flex items-center gap-2">
          <span
            className="inline-block w-5 h-3 border"
            style={{ background: STRATUM_COLORS[it.type].fill, borderColor: STRATUM_COLORS[it.type].stroke }}
          />
          {it.label}
        </div>
      ))}
    </div>
  );
}
