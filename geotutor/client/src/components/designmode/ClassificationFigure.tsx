import { DesignStep, FigureParams } from "./types";
import { FIG, activeTargets } from "./figShared";

// Classification figure: a stacked gravel/sand/fines composition bar, a
// mini Casagrande plasticity chart with the A-line, and the resulting
// group symbol and name. Highlights follow the current step: "fractions"
// lights the bar, "chart" lights the plasticity chart.

const W = 720;
const H = 460;

// blue family only (house rule: blue, never green)
const BLUE = {
  gravel: "#1e5f8e",
  sand: "#4a90c9",
  fines: "#a8cbe8",
  line: "#2272b5",
  deep: "#1d4ed8",
};

export function ClassificationFigure({
  params, steps, current,
}: {
  params: FigureParams;
  steps: DesignStep[];
  current: number;
}) {
  const hl = activeTargets(steps, current);
  const gravel = (params.gravel as number) ?? 0;
  const sand = (params.sand as number) ?? 0;
  const fines = (params.fines as number) ?? 0;
  const LL = params.LL as number | null;
  const PI = params.PI as number | null;
  const symbol = (params.symbol as string) || "?";
  const name = (params.name as string) || "";
  const system = (params.system as string) || "";

  const label = (x: number, y: number, t: string,
    anchor: "start" | "middle" | "end" = "start", fill = FIG.INK,
    size = 15.5, weight?: number) => (
    <text x={x} y={y} fontSize={size} fill={fill} textAnchor={anchor}
      fontFamily="system-ui" fontWeight={weight} stroke="#ffffff"
      strokeWidth="3.5" paintOrder="stroke">{t}</text>
  );

  // ---- composition bar (top) ----
  const BX = 60, BY = 66, BW2 = 600, BH2 = 44;
  const total = Math.max(gravel + sand + fines, 1e-6);
  const wG = (gravel / total) * BW2;
  const wS = (sand / total) * BW2;
  const wF = (fines / total) * BW2;
  const barHl = hl.has("fractions");
  const segs: { x: number; w: number; fill: string; text: string; pct: number }[] = [
    { x: BX, w: wG, fill: BLUE.gravel, text: "gravel", pct: gravel },
    { x: BX + wG, w: wS, fill: BLUE.sand, text: "sand", pct: sand },
    { x: BX + wG + wS, w: wF, fill: BLUE.fines, text: "fines", pct: fines },
  ];

  // ---- mini plasticity chart (bottom left) ----
  const CX = 60, CY = 170, CW = 330, CH2 = 240;
  const xLL = (v: number) => CX + (Math.min(Math.max(v, 0), 100) / 100) * CW;
  const yPI = (v: number) => CY + CH2 - (Math.min(Math.max(v, 0), 60) / 60) * CH2;
  const chartHl = hl.has("chart");
  // A-line PI = 0.73 (LL - 20), from LL = 20 up to where PI hits 60
  const llTop = 20 + 60 / 0.73; // LL where the A-line leaves the frame
  const hasPoint = LL != null && PI != null;

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto select-none" role="img"
      aria-label="Soil classification: composition bar, plasticity chart and group">

      {label(BX, 40, "composition", "start", FIG.DIM)}
      {system && label(BX + BW2, 40, system, "end", FIG.DIM)}

      {/* stacked composition bar */}
      <g>
        {segs.map((s, i) => (
          <g key={i}>
            <rect x={s.x} y={BY} width={Math.max(s.w, 0)} height={BH2}
              fill={s.fill} fillOpacity={barHl ? 0.95 : 0.75}
              stroke={barHl ? FIG.HL : FIG.INK}
              strokeWidth={barHl ? 2.5 : 1} />
            {s.w > 46 && label(s.x + s.w / 2, BY + BH2 / 2 + 5,
              `${s.text} ${Math.round(s.pct * 10) / 10}%`, "middle",
              i === 2 ? FIG.INK : "#ffffff", 14.5)}
            {s.w <= 46 && s.w > 2 && label(s.x + s.w / 2, BY + BH2 + 20,
              `${s.text} ${Math.round(s.pct * 10) / 10}%`, "middle", FIG.DIM, 13)}
          </g>
        ))}
        <rect x={BX} y={BY} width={BW2} height={BH2} fill="none"
          stroke={barHl ? FIG.HL : FIG.INK} strokeWidth={barHl ? 3 : 1.4} />
      </g>

      {/* plasticity chart */}
      <g>
        {label(CX, CY - 12, "plasticity chart", "start", FIG.DIM)}
        <rect x={CX} y={CY} width={CW} height={CH2} fill="#ffffff"
          stroke={chartHl ? FIG.HL : FIG.INK}
          strokeWidth={chartHl ? 3 : 1.4} />

        {/* gridlines and ticks */}
        {[20, 40, 60, 80].map((v) => (
          <line key={`gx${v}`} x1={xLL(v)} y1={CY} x2={xLL(v)} y2={CY + CH2}
            stroke={FIG.DIM} strokeWidth="0.5" opacity="0.35" />
        ))}
        {[20, 40].map((v) => (
          <line key={`gy${v}`} x1={CX} y1={yPI(v)} x2={CX + CW} y2={yPI(v)}
            stroke={FIG.DIM} strokeWidth="0.5" opacity="0.35" />
        ))}
        {[0, 20, 40, 60, 80, 100].map((v) => (
          <g key={`tx${v}`}>{label(xLL(v), CY + CH2 + 18, `${v}`, "middle", FIG.DIM, 12.5)}</g>
        ))}
        {[0, 20, 40, 60].map((v) => (
          <g key={`ty${v}`}>{label(CX - 8, yPI(v) + 4, `${v}`, "end", FIG.DIM, 12.5)}</g>
        ))}
        {label(CX + CW / 2, CY + CH2 + 38, "liquid limit LL", "middle", FIG.DIM, 13.5)}
        {label(CX - 38, CY + CH2 / 2, "PI", "end", FIG.DIM, 13.5)}

        {/* LL = 50 divider */}
        <line x1={xLL(50)} y1={CY} x2={xLL(50)} y2={CY + CH2}
          stroke={BLUE.line} strokeWidth="1.2" strokeDasharray="5 4" opacity="0.7" />

        {/* A-line, solid */}
        <line x1={xLL(20)} y1={yPI(0)} x2={xLL(Math.min(llTop, 100))}
          y2={yPI(0.73 * (Math.min(llTop, 100) - 20))}
          stroke={BLUE.line} strokeWidth="2.4" />
        {label(xLL(78), yPI(0.73 * 58) - 8, "A-line", "start", BLUE.line, 13)}

        {/* region labels */}
        {label(xLL(33), yPI(21), "CL", "middle", BLUE.deep, 14, 600)}
        {label(xLL(38), yPI(5), "ML", "middle", FIG.DIM, 14, 600)}
        {label(xLL(66), yPI(45), "CH", "middle", BLUE.deep, 14, 600)}
        {label(xLL(76), yPI(22), "MH", "middle", FIG.DIM, 14, 600)}

        {/* the soil's point */}
        {hasPoint && (
          <g>
            <circle cx={xLL(LL as number)} cy={yPI(PI as number)} r={7}
              fill={chartHl ? FIG.HL : BLUE.line} stroke="#ffffff"
              strokeWidth="2.2" />
            {label(xLL(LL as number) + 12, yPI(PI as number) - 10,
              `(${LL}, ${PI})`, "start",
              chartHl ? FIG.AMBER : BLUE.line, 13)}
          </g>
        )}
        {!hasPoint && label(CX + CW / 2, CY + CH2 / 2 - 40,
          "no Atterberg limits given", "middle", FIG.DIM, 12.5)}
      </g>

      {/* the verdict: group symbol and name */}
      <g>
        <rect x={430} y={200} width={250} height={180} rx={10}
          fill={BLUE.fines} fillOpacity="0.25"
          stroke={BLUE.line} strokeWidth="1.4" />
        {label(555, 232, "group", "middle", FIG.DIM, 13.5)}
        <text x={555} y={288} fontSize="44" fill={BLUE.deep}
          textAnchor="middle" fontFamily="system-ui" fontWeight={700}
          stroke="#ffffff" strokeWidth="4.5" paintOrder="stroke">{symbol}</text>
        {wrapName(name).map((line, i) => (
          <g key={i}>{label(555, 322 + i * 22, line, "middle", FIG.INK, 14.5)}</g>
        ))}
      </g>
    </svg>
  );
}

// wrap the group name into short centered lines for the verdict card
function wrapName(name: string): string[] {
  const words = name.split(/\s+/).filter(Boolean);
  const lines: string[] = [];
  let cur = "";
  for (const w of words) {
    if ((cur + " " + w).trim().length > 24) {
      if (cur) lines.push(cur);
      cur = w;
    } else {
      cur = (cur + " " + w).trim();
    }
  }
  if (cur) lines.push(cur);
  return lines.slice(0, 3);
}
