import { DesignStep, FigureParams } from "./types";
import { FIG, activeTargets } from "./figShared";

// Two retaining-structure figures sharing one file: the cantilever sheet
// pile (water table, dredge line, active/passive diagrams) and the
// cantilever concrete wall (stem, toe, heel, sloping backfill, Rankine
// plane through the heel).

const W = 720;
const H = 460;
const halo = { stroke: "#ffffff", strokeWidth: 3.5, paintOrder: "stroke" as const };

export function SheetPileFigure({
  params, steps, current,
}: {
  params: FigureParams; steps: DesignStep[]; current: number;
}) {
  const hl = activeTargets(steps, current);
  const L1 = (params.L1 as number) || 4;
  const L2 = (params.L2 as number) || 8;
  const D = (params.D as number) || 12;
  const L3 = (params.L3 as number) || 1.5;
  const total = L1 + L2 + D;
  const GY = 70;
  const scale = 340 / total;
  const sy = (d: number) => GY + d * scale;
  const wx = 430;                       // wall x
  const dredgeY = sy(L1 + L2);
  const wtY = sy(L1);
  const tipY = sy(total);

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto select-none" role="img"
      aria-label="Cantilever sheet pile wall">
      <defs>
        <pattern id="soilHatchSp" width="10" height="10" patternUnits="userSpaceOnUse"
          patternTransform="rotate(45)">
          <line x1="0" y1="0" x2="0" y2="10" stroke={FIG.SOIL_HATCH} strokeWidth="0.7" opacity="0.4" />
        </pattern>
        <marker id="arrSp" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6"
          markerHeight="6" orient="auto">
          <path d="M0,0 L10,5 L0,10 z" fill={FIG.SLIP} />
        </marker>
        <marker id="arrSpB" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6"
          markerHeight="6" orient="auto">
          <path d="M0,0 L10,5 L0,10 z" fill={FIG.WATER} />
        </marker>
      </defs>

      {/* retained soil (right of wall) and foundation soil (left, below dredge) */}
      <rect x={wx} y={GY} width={W - wx - 36} height={H - GY - 14} fill={FIG.SOIL_FILL} />
      <rect x={wx} y={GY} width={W - wx - 36} height={H - GY - 14} fill="url(#soilHatchSp)" />
      <rect x={36} y={dredgeY} width={wx - 36} height={H - dredgeY - 14} fill={FIG.SOIL_FILL} />
      <rect x={36} y={dredgeY} width={wx - 36} height={H - dredgeY - 14} fill="url(#soilHatchSp)" />

      {/* ground, dredge line, water table */}
      <line x1={wx} y1={GY} x2={W - 28} y2={GY} stroke={FIG.INK} strokeWidth="2.2" />
      <line x1={28} y1={dredgeY} x2={wx} y2={dredgeY} stroke={FIG.INK} strokeWidth="2" />
      <text x={40} y={dredgeY - 8} fontSize="15" fill={FIG.DIM} fontFamily="system-ui" {...halo}>
        dredge line
      </text>
      <line x1={wx} y1={wtY} x2={W - 28} y2={wtY} stroke={FIG.WATER}
        strokeWidth="1.6" strokeDasharray="8 5" />
      <path d={`M ${W - 70} ${wtY - 12} l 12 0 l -6 10 z`} fill={FIG.WATER} />

      {/* the wall */}
      <line x1={wx} y1={GY - 16} x2={wx} y2={tipY}
        stroke={hl.has("wall") ? FIG.AMBER : FIG.INK}
        strokeWidth={hl.has("wall") ? 6 : 4.5} />

      {/* zero net pressure point and embedment highlight */}
      <circle cx={wx} cy={sy(L1 + L2 + L3)} r={7}
        fill={hl.has("zero_point") ? FIG.HL : "#ffffff"}
        stroke={FIG.SLIP} strokeWidth="1.6" />
      {hl.has("embedment") && (
        <line x1={wx} y1={dredgeY} x2={wx} y2={tipY} stroke={FIG.SLIP}
          strokeWidth="7" opacity="0.65" />
      )}

      {/* active pressure triangle (right side, pushes left) */}
      <g opacity={hl.has("active") ? 1 : 0.4}>
        <polygon points={`${wx},${GY} ${wx + 95},${dredgeY} ${wx},${dredgeY}`}
          fill={FIG.SLIP} fillOpacity="0.15" stroke={FIG.SLIP} strokeWidth="1.4" />
        {[0.45, 0.75, 0.97].map((f) => (
          <line key={f} x1={wx + 95 * f} y1={sy((L1 + L2) * f)} x2={wx + 6}
            y2={sy((L1 + L2) * f)} stroke={FIG.SLIP} strokeWidth="1.5"
            markerEnd="url(#arrSp)" />
        ))}
        <text x={wx + 104} y={dredgeY - 6} fontSize="15" fill={FIG.SLIP}
          fontFamily="system-ui" {...halo}>{`σ'₂ = ${params.sigma2} kPa`}</text>
      </g>

      {/* passive resistance (left side below dredge, pushes right) */}
      <g opacity={hl.has("passive") ? 1 : 0.35}>
        <polygon points={`${wx},${dredgeY} ${wx - 85},${tipY} ${wx},${tipY}`}
          fill={FIG.WATER} fillOpacity="0.15" stroke={FIG.WATER} strokeWidth="1.4" />
        {[0.55, 0.85].map((f) => (
          <line key={f} x1={wx - 85 * f} y1={sy(L1 + L2 + D * f)} x2={wx - 6}
            y2={sy(L1 + L2 + D * f)} stroke={FIG.WATER} strokeWidth="1.5"
            markerEnd="url(#arrSpB)" />
        ))}
      </g>

      {/* depth labels */}
      <text x={W - 34} y={(GY + wtY) / 2 + 5} fontSize="15.5" fill={FIG.DIM}
        textAnchor="end" fontFamily="system-ui" {...halo}>{`L₁ = ${L1} m`}</text>
      <text x={W - 34} y={(wtY + dredgeY) / 2 + 5} fontSize="15.5" fill={FIG.DIM}
        textAnchor="end" fontFamily="system-ui" {...halo}>{`L₂ = ${L2} m`}</text>
      <text x={wx - 14} y={(dredgeY + tipY) / 2 + 5} fontSize="15.5" fill={FIG.SLIP}
        textAnchor="end" fontFamily="system-ui" {...halo}>{`D = ${D} m`}</text>

      <text x={44} y={H - 22} fontSize="16" fill={FIG.SOIL_HATCH}
        fontFamily="system-ui" {...halo}>
        {`γ = ${params.gamma} kN/m³   φ' = ${params.phi}°`}
      </text>
    </svg>
  );
}

export function CantileverWallFigure({
  params, steps, current,
}: {
  params: FigureParams; steps: DesignStep[]; current: number;
}) {
  const hl = activeTargets(steps, current);
  const Hs = (params.H as number) || 8;
  const x1 = (params.x1 as number) || 0.4;
  const x2 = (params.x2 as number) || 0.6;
  const x3 = (params.x3 as number) || 1.5;
  const x4 = (params.x4 as number) || 3.5;
  const x5 = (params.x5 as number) || 1;
  const alpha = ((params.alpha as number) || 0) * Math.PI / 180;
  const B = x2 + x3 + x4;

  const baseYpix = 380;
  const scale = Math.min(280 / (Hs + x5), 300 / B);
  const ox = 200; // toe x in px
  const sx = (m: number) => ox + m * scale;
  const topY = baseYpix - (x5 + Hs) * scale;

  const heelX = sx(x3 + x2);          // back of stem at base
  const planeX = sx(B);               // vertical plane through the heel
  const slopeRise = x4 * Math.tan(alpha) * scale;

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto select-none" role="img"
      aria-label="Cantilever retaining wall">
      <defs>
        <pattern id="soilHatchWall" width="10" height="10" patternUnits="userSpaceOnUse"
          patternTransform="rotate(45)">
          <line x1="0" y1="0" x2="0" y2="10" stroke={FIG.SOIL_HATCH} strokeWidth="0.7" opacity="0.4" />
        </pattern>
        <marker id="arrWall" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6"
          markerHeight="6" orient="auto">
          <path d="M0,0 L10,5 L0,10 z" fill={FIG.SLIP} />
        </marker>
      </defs>

      {/* backfill over the heel, with the sloping surface */}
      <g opacity={hl.has("sections") ? 1 : 0.9}>
        <polygon
          points={`${heelX},${topY} ${planeX},${topY - slopeRise} ${planeX},${baseYpix - x5 * scale} ${heelX},${baseYpix - x5 * scale}`}
          fill={FIG.SOIL_FILL} stroke="none" />
        <polygon
          points={`${heelX},${topY} ${planeX},${topY - slopeRise} ${planeX},${baseYpix - x5 * scale} ${heelX},${baseYpix - x5 * scale}`}
          fill="url(#soilHatchWall)" />
      </g>
      {/* backfill continues right of the plane */}
      <polygon
        points={`${planeX},${topY - slopeRise} ${W - 40},${topY - slopeRise - (W - 40 - planeX) * Math.tan(alpha)} ${W - 40},${baseYpix} ${planeX},${baseYpix}`}
        fill={FIG.SOIL_FILL} />
      <polygon
        points={`${planeX},${topY - slopeRise} ${W - 40},${topY - slopeRise - (W - 40 - planeX) * Math.tan(alpha)} ${W - 40},${baseYpix} ${planeX},${baseYpix}`}
        fill="url(#soilHatchWall)" />

      {/* foundation soil below the base */}
      <rect x={60} y={baseYpix} width={W - 100} height={H - baseYpix - 14}
        fill="#e8e0d0" />
      <rect x={60} y={baseYpix} width={W - 100} height={H - baseYpix - 14}
        fill="url(#soilHatchWall)" />
      <line x1={50} y1={baseYpix} x2={sx(0)} y2={baseYpix} stroke={FIG.INK} strokeWidth="2" />

      {/* the concrete wall: stem (tapered) + base slab */}
      <g fill={hl.has("sections") ? "#fde68a" : "#d6d9de"} stroke={FIG.INK} strokeWidth="1.8">
        <rect x={sx(0)} y={baseYpix - x5 * scale} width={B * scale} height={x5 * scale} />
        <polygon points={`${sx(x3)},${baseYpix - x5 * scale} ${sx(x3 + x2)},${baseYpix - x5 * scale} ${sx(x3 + x2)},${topY} ${sx(x3 + x2 - x1)},${topY}`} />
      </g>

      {/* toe and base highlights */}
      {hl.has("toe") && <circle cx={sx(0)} cy={baseYpix} r={10} fill={FIG.HL} opacity="0.6" />}
      {hl.has("base") && (
        <line x1={sx(0)} y1={baseYpix} x2={sx(B)} y2={baseYpix}
          stroke={FIG.AMBER} strokeWidth="6" opacity="0.8" />
      )}

      {/* Rankine vertical plane through the heel */}
      <line x1={planeX} y1={topY - slopeRise} x2={planeX} y2={baseYpix}
        stroke={hl.has("virtual_plane") ? FIG.AMBER : FIG.DIM}
        strokeWidth={hl.has("virtual_plane") ? 3 : 1.4} strokeDasharray="7 5" />

      {/* active thrust on the plane */}
      {hl.has("active") && (
        <g stroke={FIG.SLIP} strokeWidth="2">
          {[0.5, 0.72, 0.92].map((f) => (
            <line key={f} x1={planeX + 66 * f} y1={topY - slopeRise + (baseYpix - topY + slopeRise) * f}
              x2={planeX + 5} y2={topY - slopeRise + (baseYpix - topY + slopeRise) * f}
              markerEnd="url(#arrWall)" />
          ))}
          <text x={planeX + 72} y={baseYpix - 40} fontSize="15.5" fill={FIG.SLIP}
            fontFamily="system-ui" {...halo}>Pₐ</text>
        </g>
      )}

      {/* dimensions */}
      <text x={sx(x3 + x2 - x1 / 2) - 6} y={topY - 10} fontSize="14.5" fill={FIG.DIM}
        fontFamily="system-ui" {...halo}>{`x₁ = ${x1} m`}</text>
      <g stroke={FIG.DIM} strokeWidth="1.1">
        <line x1={sx(0)} y1={baseYpix + 22} x2={sx(B)} y2={baseYpix + 22} />
      </g>
      <text x={sx(B / 2)} y={baseYpix + 40} fontSize="15.5" fill={FIG.DIM}
        textAnchor="middle" fontFamily="system-ui" {...halo}>{`B = ${B.toFixed(1)} m`}</text>
      <g stroke={FIG.DIM} strokeWidth="1.1">
        <line x1={sx(x3 + x2) + 40 - 110} y1={topY} x2={sx(x3 + x2) - 110} y2={baseYpix} strokeWidth="0" />
        <line x1={140} y1={topY} x2={140} y2={baseYpix - x5 * scale} />
      </g>
      <text x={130} y={(topY + baseYpix) / 2} fontSize="15.5" fill={FIG.DIM}
        textAnchor="end" fontFamily="system-ui" {...halo}>{`H = ${Hs} m`}</text>

      <text x={70} y={H - 24} fontSize="15.5" fill={FIG.SOIL_HATCH}
        fontFamily="system-ui" {...halo}>
        {`backfill γ₁ = ${params.gamma}, φ'₁ = ${params.phi}°   foundation γ₂ = ${params.gamma2}, φ'₂ = ${params.phi2}°, c'₂ = ${params.c2}`}
      </text>
    </svg>
  );
}
