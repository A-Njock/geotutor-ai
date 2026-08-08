import { DesignStep, FigureParams } from "./types";
import { FIG, activeTargets } from "./figShared";

// Clay layer between its drainage boundaries for time-rate problems:
// sand above (and below when doubly drained), the drainage path arrows,
// and a sketched isochrone of the remaining excess pore pressure.

const W = 720;
const H = 460;
const halo = { stroke: "#ffffff", strokeWidth: 3.5, paintOrder: "stroke" as const };

export function ConsolidationFigure({
  params, steps, current,
}: {
  params: FigureParams; steps: DesignStep[]; current: number;
}) {
  const hl = activeTargets(steps, current);
  const Hm = (params.H as number) || 4;
  const ways = (params.ways as number) || 2;
  const double = ways === 2;

  const X0 = 150, XW = 430;
  const topY = 140, botY = 340;
  const midY = (topY + botY) / 2;

  const label = (x: number, y: number, t: string,
    anchor: "start" | "middle" | "end" = "start", fill = FIG.INK) => (
    <text x={x} y={y} fontSize="15.5" fill={fill} textAnchor={anchor}
      fontFamily="system-ui" {...halo}>{t}</text>
  );

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto select-none" role="img"
      aria-label="Clay layer between its drainage boundaries">
      <defs>
        <pattern id="clayHatchCons" width="10" height="10" patternUnits="userSpaceOnUse"
          patternTransform="rotate(45)">
          <line x1="0" y1="0" x2="0" y2="10" stroke={FIG.SOIL_HATCH} strokeWidth="0.7" opacity="0.4" />
        </pattern>
        <pattern id="sandDotsCons" width="12" height="12" patternUnits="userSpaceOnUse">
          <circle cx="4" cy="4" r="1.3" fill={FIG.SAND} />
          <circle cx="10" cy="9" r="1.3" fill={FIG.SAND} />
        </pattern>
        <marker id="arrCons" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6"
          markerHeight="6" orient="auto">
          <path d="M0,0 L10,5 L0,10 z" fill={FIG.WATER} />
        </marker>
      </defs>

      {/* surcharge arrows: the load driving consolidation */}
      <g stroke={FIG.INK} strokeWidth="1.8">
        {[0.15, 0.35, 0.55, 0.75, 0.95].map((f) => (
          <line key={f} x1={X0 + XW * f} y1={52} x2={X0 + XW * f} y2={76} />
        ))}
      </g>
      <line x1={X0} y1={78} x2={X0 + XW} y2={78} stroke={FIG.INK} strokeWidth="2.2" />
      {label(X0 + XW / 2, 42, "applied load Δσ", "middle", FIG.DIM)}

      {/* upper sand (always a drainage boundary here) */}
      <rect x={X0} y={80} width={XW} height={topY - 80} fill="#f7f2e6" />
      <rect x={X0} y={80} width={XW} height={topY - 80} fill="url(#sandDotsCons)" />
      {label(X0 + XW + 12, (80 + topY) / 2 + 5, "sand (drains)", "start", FIG.DIM)}

      {/* the clay layer */}
      <rect x={X0} y={topY} width={XW} height={botY - topY}
        fill={FIG.SOIL_FILL}
        stroke={hl.has("layer") ? FIG.HL : FIG.INK}
        strokeWidth={hl.has("layer") ? 3 : 1.6} />
      <rect x={X0} y={topY} width={XW} height={botY - topY} fill="url(#clayHatchCons)" />
      {label(X0 + 14, topY + 24, `clay, cv = ${params.cv} m²/yr`, "start", FIG.INK)}

      {/* lower boundary: sand or impermeable rock */}
      {double ? (
        <>
          <rect x={X0} y={botY} width={XW} height={40} fill="#f7f2e6" />
          <rect x={X0} y={botY} width={XW} height={40} fill="url(#sandDotsCons)" />
          {label(X0 + XW + 12, botY + 26, "sand (drains)", "start", FIG.DIM)}
        </>
      ) : (
        <>
          <rect x={X0} y={botY} width={XW} height={40} fill="#d8d3c8" />
          <g stroke={FIG.INK} strokeWidth="1.2" opacity="0.6">
            {[0.1, 0.3, 0.5, 0.7, 0.9].map((f) => (
              <line key={f} x1={X0 + XW * f} y1={botY + 8}
                x2={X0 + XW * f - 18} y2={botY + 32} />
            ))}
          </g>
          {label(X0 + XW + 12, botY + 26, "impermeable", "start", FIG.DIM)}
        </>
      )}

      {/* drainage path arrows */}
      <g opacity={hl.has("drainage") ? 1 : 0.75}>
        <line x1={X0 + XW * 0.3} y1={double ? midY : botY - 14}
          x2={X0 + XW * 0.3} y2={topY + 8}
          stroke={FIG.WATER} strokeWidth="2.6" markerEnd="url(#arrCons)" />
        {double && (
          <line x1={X0 + XW * 0.44} y1={midY}
            x2={X0 + XW * 0.44} y2={botY - 8}
            stroke={FIG.WATER} strokeWidth="2.6" markerEnd="url(#arrCons)" />
        )}
        {label(X0 + XW * 0.3 + 12, double ? midY - 8 : (topY + botY) / 2,
          `Hdr = ${params.Hdr} m`, "start", FIG.WATER)}
      </g>

      {/* sketched isochrone: remaining excess pore pressure */}
      <g opacity={hl.has("isochrone") ? 1 : 0.5}>
        <path
          d={double
            ? `M ${X0 + XW * 0.62} ${topY} Q ${X0 + XW * 0.87} ${midY} ${X0 + XW * 0.62} ${botY}`
            : `M ${X0 + XW * 0.62} ${topY} Q ${X0 + XW * 0.9} ${botY - 20} ${X0 + XW * 0.66} ${botY}`}
          fill="none" stroke={FIG.WATER} strokeWidth="2" strokeDasharray="6 4" />
        {label(X0 + XW * 0.8, midY + 4, "excess u left", "start", FIG.WATER)}
      </g>

      {/* thickness dimension */}
      <g stroke={FIG.DIM} strokeWidth="1.1">
        <line x1={X0 - 26} y1={topY} x2={X0 - 26} y2={botY} />
      </g>
      {label(X0 - 36, midY + 5, `H = ${Hm} m`, "end", FIG.DIM)}

      {label(X0, H - 24,
        `U = ${params.U} %  →  t = ${params.t} years`, "start", FIG.INK)}
    </svg>
  );
}
