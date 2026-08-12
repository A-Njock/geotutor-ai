import { DesignStep, FigureParams } from "./types";
import { FIG, activeTargets } from "./figShared";

// Driven pile in one or two soil layers: shaft, tip, the critical depth for
// side friction, and load arrows per phenomenon (skin friction along the
// shaft, point resistance at the tip).

const W = 720;
const H = 460;

export function PileFigure({
  params, steps, current,
}: {
  params: FigureParams;
  steps: DesignStep[];
  current: number;
}) {
  const hl = activeTargets(steps, current);
  const L = (params.L as number) || 12;
  const two = !!params.two_layers;
  const Lc = params.Lc as number | null;

  const GY = 96;
  const scale = 300 / L;
  const sy = (d: number) => GY + d * scale;
  const tipY = sy(L);
  const cx = W / 2;
  const pw = 26; // pile half-visual width
  const layerY = two ? sy(L) - 40 : tipY + 24; // dense layer starts near tip

  const halo = { stroke: "#ffffff", strokeWidth: 3.5, paintOrder: "stroke" as const };

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto select-none" role="img"
      aria-label="Pile in the soil profile">
      <defs>
        <pattern id="soilHatchPile" width="10" height="10" patternUnits="userSpaceOnUse"
          patternTransform="rotate(45)">
          <line x1="0" y1="0" x2="0" y2="10" stroke={FIG.SOIL_HATCH} strokeWidth="0.7" opacity="0.4" />
        </pattern>
        <pattern id="densePile" width="7" height="7" patternUnits="userSpaceOnUse"
          patternTransform="rotate(45)">
          <line x1="0" y1="0" x2="0" y2="7" stroke={FIG.SOIL_HATCH} strokeWidth="1.1" opacity="0.7" />
        </pattern>
        <marker id="arrPile" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6"
          markerHeight="6" orient="auto">
          <path d="M0,0 L10,5 L0,10 z" fill={FIG.SLIP} />
        </marker>
      </defs>

      {/* upper (loose) layer */}
      <rect x={50} y={GY} width={W - 100} height={layerY - GY} fill={FIG.SOIL_FILL} />
      <rect x={50} y={GY} width={W - 100} height={layerY - GY} fill="url(#soilHatchPile)" />
      {/* lower (dense/bearing) layer */}
      <rect x={50} y={layerY} width={W - 100} height={H - layerY - 16}
        fill={two ? "#e8e0d0" : FIG.SOIL_FILL} />
      <rect x={50} y={layerY} width={W - 100} height={H - layerY - 16}
        fill={two ? "url(#densePile)" : "url(#soilHatchPile)"} />

      <line x1={40} y1={GY} x2={W - 40} y2={GY} stroke={FIG.INK} strokeWidth="2.2" />

      {/* the pile */}
      <rect x={cx - pw / 2} y={GY - 34} width={pw} height={tipY - GY + 34}
        fill={hl.has("shaft") ? "#fde68a" : "#d6d9de"}
        stroke={FIG.INK} strokeWidth="1.8" />

      {/* critical depth marker for side friction */}
      {Lc != null && (
        <g>
          <line x1={60} y1={sy(Lc)} x2={W - 60} y2={sy(Lc)}
            stroke={hl.has("critical") ? FIG.AMBER : FIG.DIM}
            strokeWidth={hl.has("critical") ? 2.4 : 1.2} strokeDasharray="7 5" />
          <text x={W - 66} y={sy(Lc) - 8} fontSize="15" fill={FIG.AMBER}
            textAnchor="end" fontFamily="system-ui" {...halo}>
            {`L' = 15D = ${(Lc as number).toFixed(2)} m`}
          </text>
        </g>
      )}

      {/* skin friction arrows along the shaft */}
      {hl.has("shaft_arrows") && (
        <g stroke={FIG.SLIP} strokeWidth="1.8">
          {[0.2, 0.4, 0.6, 0.8].map((f) => (
            <g key={f}>
              <line x1={cx - pw / 2 - 16} y1={sy(L * f) + 12} x2={cx - pw / 2 - 16}
                y2={sy(L * f) - 8} markerEnd="url(#arrPile)" />
              <line x1={cx + pw / 2 + 16} y1={sy(L * f) + 12} x2={cx + pw / 2 + 16}
                y2={sy(L * f) - 8} markerEnd="url(#arrPile)" />
            </g>
          ))}
        </g>
      )}

      {/* point resistance arrows at the tip */}
      {(hl.has("point_arrows") || hl.has("tip")) && (
        <g stroke={FIG.SLIP} strokeWidth="1.8"
          opacity={hl.has("point_arrows") ? 1 : 0.55}>
          {[-8, 0, 8].map((dx) => (
            <line key={dx} x1={cx + dx} y1={tipY + 24} x2={cx + dx} y2={tipY + 4}
              markerEnd="url(#arrPile)" />
          ))}
        </g>
      )}
      {hl.has("tip") && (
        <circle cx={cx} cy={tipY} r={16} fill={FIG.HL} opacity="0.35" />
      )}

      {/* dimensions */}
      <g stroke={FIG.DIM} strokeWidth="1.2">
        <line x1={cx - 120} y1={GY} x2={cx - 120} y2={tipY} />
        <text x={cx - 130} y={(GY + tipY) / 2} fontSize="16.5" fill={FIG.DIM}
          textAnchor="end" fontFamily="system-ui" {...halo}>{`L = ${L} m`}</text>
      </g>
      <text x={cx + pw / 2 + 10} y={GY - 12} fontSize="15.5" fill={FIG.DIM}
        fontFamily="system-ui" {...halo}>{`D = ${params.D} m`}</text>

      {/* layer labels */}
      <text x={64} y={GY + 26} fontSize="16" fill={FIG.SOIL_HATCH}
        fontFamily="system-ui" {...halo}>
        {`${(params.soil_type as string) || "soil"}${params.phi ? `  φ' = ${params.phi}°` : ""}${params.gamma ? `  γ = ${params.gamma} kN/m³` : ""}`}
      </text>
      {two && (
        <text x={64} y={layerY + 26} fontSize="16" fill={FIG.SOIL_HATCH}
          fontFamily="system-ui" {...halo}>
          {`bearing layer  φ' = ${params.phi2}°`}
        </text>
      )}
    </svg>
  );
}
