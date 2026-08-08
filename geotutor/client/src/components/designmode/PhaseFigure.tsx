import { DesignStep, FigureParams } from "./types";
import { FIG, activeTargets } from "./figShared";

// Three-phase diagram for phase-relation problems: the sample block on the
// left, the idealized air/water/solids stack on the right, drawn to scale
// from the computed volumes. Highlights follow the current step.

const W = 720;
const H = 460;

export function PhaseFigure({
  params, steps, current,
}: {
  params: FigureParams;
  steps: DesignStep[];
  current: number;
}) {
  const hl = activeTargets(steps, current);
  const V = (params.V as number) || 1;
  const e = (params.e as number) ?? 0.9;
  const S = ((params.S as number) ?? 50) / 100; // fraction of voids filled

  const Vs = V / (1 + e);
  const Vv = V - Vs;
  const Vw = Vv * S;
  const Va = Vv - Vw;

  // stack geometry (heights proportional to volumes)
  const X0 = 400, BW = 170, TOP = 90, BH = 300;
  const hS = (Vs / V) * BH;
  const hW = (Vw / V) * BH;
  const hA = (Va / V) * BH;
  const yA = TOP, yW = TOP + hA, yS = TOP + hA + hW;

  const label = (x: number, y: number, t: string,
    anchor: "start" | "middle" | "end" = "start", fill = FIG.INK) => (
    <text x={x} y={y} fontSize="15.5" fill={fill} textAnchor={anchor}
      fontFamily="system-ui" stroke="#ffffff" strokeWidth="3.5" paintOrder="stroke">{t}</text>
  );

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto select-none" role="img"
      aria-label="Three-phase diagram of the soil sample">
      <defs>
        <pattern id="soilHatchPhase" width="10" height="10" patternUnits="userSpaceOnUse"
          patternTransform="rotate(45)">
          <line x1="0" y1="0" x2="0" y2="10" stroke={FIG.SOIL_HATCH} strokeWidth="0.7" opacity="0.5" />
        </pattern>
      </defs>

      {/* the real sample */}
      <g>
        <rect x={90} y={150} width={150} height={180} fill={FIG.SOIL_FILL}
          stroke={hl.has("total") ? FIG.HL : FIG.INK}
          strokeWidth={hl.has("total") ? 3.5 : 1.6} />
        <rect x={90} y={150} width={150} height={180} fill="url(#soilHatchPhase)" />
        {label(165, 360, "the sample", "middle", FIG.DIM)}
        {label(165, 385, `V, W`, "middle", FIG.DIM)}
      </g>

      {/* idealization arrow */}
      <line x1={265} y1={240} x2={360} y2={240} stroke={FIG.DIM} strokeWidth="2" />
      <path d={`M 360 240 l -10 -6 l 0 12 z`} fill={FIG.DIM} />
      {label(312, 222, "idealize", "middle", FIG.DIM)}

      {/* phase stack */}
      <g>
        {/* air */}
        <rect x={X0} y={yA} width={BW} height={Math.max(hA, 2)} fill="#ffffff"
          stroke={hl.has("voids") || hl.has("phases") ? FIG.HL : FIG.DIM}
          strokeWidth={hl.has("voids") || hl.has("phases") ? 2.5 : 1.2}
          strokeDasharray="5 4" />
        {hA > 14 && label(X0 + BW / 2, yA + hA / 2 + 5, "air", "middle", FIG.DIM)}

        {/* water */}
        <rect x={X0} y={yW} width={BW} height={Math.max(hW, 2)} fill={FIG.WATER}
          fillOpacity={hl.has("water") ? 0.5 : 0.28}
          stroke={hl.has("water") || hl.has("voids") || hl.has("phases") ? FIG.HL : FIG.WATER}
          strokeWidth={hl.has("water") ? 2.5 : 1.2} />
        {hW > 14 && label(X0 + BW / 2, yW + hW / 2 + 5, "water", "middle", FIG.WATER)}

        {/* solids */}
        <rect x={X0} y={yS} width={BW} height={hS} fill={FIG.SAND}
          fillOpacity={0.85}
          stroke={hl.has("solids") || hl.has("phases") ? FIG.HL : FIG.INK}
          strokeWidth={hl.has("solids") ? 2.8 : 1.4} />
        <rect x={X0} y={yS} width={BW} height={hS} fill="url(#soilHatchPhase)" opacity="0.4" />
        {label(X0 + BW / 2, yS + hS / 2 + 5, "solids", "middle", FIG.INK)}
      </g>

      {/* volume side (left of stack) */}
      {label(X0 - 12, yA + Math.max(hA, 14) / 2 + 5, "Va", "end", FIG.DIM)}
      {label(X0 - 12, yW + Math.max(hW, 14) / 2 + 5, "Vw", "end", FIG.WATER)}
      {label(X0 - 12, yS + hS / 2 + 5, "Vs", "end", FIG.INK)}
      {label(X0 - 64, TOP - 18, "volumes", "start", FIG.DIM)}

      {/* weight side (right of stack) */}
      {label(X0 + BW + 12, yW + Math.max(hW, 14) / 2 + 5, "Ww", "start", FIG.WATER)}
      {label(X0 + BW + 12, yS + hS / 2 + 5, "Ws", "start", FIG.INK)}
      {label(X0 + BW + 12, TOP - 18, "weights", "start", FIG.DIM)}

      {/* void bracket: air + water */}
      {(hl.has("voids")) && (
        <g stroke={FIG.HL} strokeWidth="2.4" fill="none">
          <path d={`M ${X0 + BW + 58} ${yA} l 12 0 l 0 ${hA + hW} l -12 0`} />
          <text x={X0 + BW + 78} y={yA + (hA + hW) / 2 + 5} fontSize="15.5"
            fill={FIG.AMBER} fontFamily="system-ui" stroke="#ffffff"
            strokeWidth="3.5" paintOrder="stroke">voids Vv</text>
        </g>
      )}
    </svg>
  );
}
