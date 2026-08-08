import { DesignStep, FigureParams } from "./types";
import { FIG, activeTargets } from "./figShared";

// Infinite (translational) slope: soil layer of thickness z on bedrock,
// slip surface parallel to the ground at angle beta, with the analysed
// slice and its force triangle. Highlights follow the current step.

const W = 720;
const H = 460;

export function SlopeFigure({
  params, steps, current,
}: {
  params: FigureParams;
  steps: DesignStep[];
  current: number;
}) {
  const hl = activeTargets(steps, current);
  const beta = ((params.beta as number) || 17) * Math.PI / 180;

  // slope line through the canvas centre
  const cx = W / 2, cy = 235;
  const dx = Math.cos(beta), dy = -Math.sin(beta);
  const span = 340;
  const gx0 = cx - span * dx, gy0 = cy - span * dy;
  const gx1 = cx + span * dx, gy1 = cy + span * dy;
  // slip surface: parallel, offset z (perpendicular) below
  const zPx = 92;
  const nx = Math.sin(beta), ny = Math.cos(beta); // downward normal
  const bx0 = gx0 + zPx * nx, by0 = gy0 + zPx * ny;
  const bx1 = gx1 + zPx * nx, by1 = gy1 + zPx * ny;

  // slice: width b along the slope, centred
  const bHalf = 40;
  const sTopL = { x: cx - bHalf * dx, y: cy - bHalf * dy };
  const sTopR = { x: cx + bHalf * dx, y: cy + bHalf * dy };
  const sBotL = { x: sTopL.x + zPx * nx, y: sTopL.y + zPx * ny };
  const sBotR = { x: sTopR.x + zPx * nx, y: sTopR.y + zPx * ny };
  const sc = { x: cx + (zPx / 2) * nx, y: cy + (zPx / 2) * ny }; // slice centre
  const bc = { x: cx + zPx * nx, y: cy + zPx * ny };             // base centre

  const props: string[] = [];
  if (params.gamma) props.push(`γ = ${params.gamma} kN/m³`);
  if (params.c) props.push(`c' = ${params.c} kPa`);
  if (params.phi) props.push(`φ' = ${params.phi}°`);

  const halo = { stroke: "#ffffff", strokeWidth: 3.5, paintOrder: "stroke" as const };

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto select-none" role="img"
      aria-label="Translational slope with the analysed slice">
      <defs>
        <pattern id="soilHatchSlope" width="10" height="10" patternUnits="userSpaceOnUse"
          patternTransform="rotate(45)">
          <line x1="0" y1="0" x2="0" y2="10" stroke={FIG.SOIL_HATCH} strokeWidth="0.7" opacity="0.45" />
        </pattern>
        <pattern id="rockHatchSlope" width="8" height="8" patternUnits="userSpaceOnUse">
          <line x1="0" y1="8" x2="8" y2="0" stroke={FIG.DIM} strokeWidth="0.9" opacity="0.6" />
        </pattern>
        <marker id="arrSlope" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7"
          markerHeight="7" orient="auto">
          <path d="M0,0 L10,5 L0,10 z" fill={FIG.SLIP} />
        </marker>
        <marker id="dimArrSlope" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="7"
          markerHeight="7" orient="auto-start-reverse">
          <path d="M0,0 L8,4 L0,8 z" fill={FIG.DIM} />
        </marker>
      </defs>

      {/* soil layer between ground and slip surface */}
      <polygon points={`${gx0},${gy0} ${gx1},${gy1} ${bx1},${by1} ${bx0},${by0}`}
        fill={FIG.SOIL_FILL} />
      <polygon points={`${gx0},${gy0} ${gx1},${gy1} ${bx1},${by1} ${bx0},${by0}`}
        fill="url(#soilHatchSlope)" />

      {/* bedrock below the slip surface */}
      <polygon points={`${bx0},${by0} ${bx1},${by1} ${bx1},${H - 12} ${bx0},${H - 12}`}
        fill="#e8e6e1" />
      <polygon points={`${bx0},${by0} ${bx1},${by1} ${bx1},${H - 12} ${bx0},${H - 12}`}
        fill="url(#rockHatchSlope)" />
      <text x={bx1 - 8} y={H - 28} fontSize="15.5" fill={FIG.DIM} textAnchor="end"
        fontFamily="system-ui" {...halo}>bedrock</text>

      {/* ground surface and slip surface */}
      <line x1={gx0} y1={gy0} x2={gx1} y2={gy1} stroke={FIG.INK} strokeWidth="2.2" />
      <line x1={bx0} y1={by0} x2={bx1} y2={by1}
        stroke={hl.has("base") ? FIG.SLIP : FIG.DIM}
        strokeWidth={hl.has("base") ? 3 : 1.8}
        strokeDasharray={hl.has("base") ? "none" : "7 5"} />

      {/* the slice */}
      <g>
        <polygon
          points={`${sTopL.x},${sTopL.y} ${sTopR.x},${sTopR.y} ${sBotR.x},${sBotR.y} ${sBotL.x},${sBotL.y}`}
          fill={hl.has("slice") ? FIG.HL : "#ffffff"}
          fillOpacity={hl.has("slice") ? 0.35 : 0.25}
          stroke={hl.has("slice") ? FIG.AMBER : FIG.INK} strokeWidth="1.8" />
        {/* base of the slice */}
        <line x1={sBotL.x} y1={sBotL.y} x2={sBotR.x} y2={sBotR.y}
          stroke={hl.has("base") ? FIG.SLIP : FIG.INK}
          strokeWidth={hl.has("base") ? 3.5 : 2} />
      </g>

      {/* forces on the slice */}
      {hl.has("forces") && (
        <g>
          <line x1={sc.x} y1={sc.y} x2={sc.x} y2={sc.y + 74}
            stroke={FIG.SLIP} strokeWidth="2.4" markerEnd="url(#arrSlope)" />
          <text x={sc.x + 10} y={sc.y + 58} fontSize="16" fontStyle="italic"
            fill={FIG.SLIP} fontFamily="system-ui" {...halo}>W</text>
          <line x1={bc.x} y1={bc.y} x2={bc.x - 60 * nx} y2={bc.y - 60 * ny}
            stroke={FIG.AMBER} strokeWidth="2.2" markerEnd="url(#arrSlope)" />
          <text x={bc.x - 60 * nx - 26} y={bc.y - 60 * ny + 2} fontSize="16"
            fontStyle="italic" fill={FIG.AMBER} fontFamily="system-ui" {...halo}>N</text>
          <line x1={bc.x} y1={bc.y} x2={bc.x - 62 * dx} y2={bc.y - 62 * dy}
            stroke={FIG.WATER} strokeWidth="2.2" markerEnd="url(#arrSlope)" />
          <text x={bc.x - 62 * dx - 8} y={bc.y - 62 * dy + 22} fontSize="16"
            fontStyle="italic" fill={FIG.WATER} fontFamily="system-ui" {...halo}>T</text>
        </g>
      )}

      {/* z dimension (perpendicular thickness), on the upslope side */}
      <g stroke={FIG.DIM} strokeWidth="1.2">
        <line x1={gx0 + 60 * dx} y1={gy0 + 60 * dy}
          x2={gx0 + 60 * dx + zPx * nx} y2={gy0 + 60 * dy + zPx * ny}
          markerStart="url(#dimArrSlope)" markerEnd="url(#dimArrSlope)" />
        <text x={gx0 + 60 * dx + zPx * nx + 10} y={gy0 + 60 * dy + zPx * ny - 14}
          fontSize="16.5" fill={FIG.DIM} fontFamily="system-ui" stroke="#ffffff"
          strokeWidth="3.5" paintOrder="stroke">{`z = ${params.z} m`}</text>
      </g>

      {/* beta angle at the toe */}
      <g>
        <line x1={gx1 - 120} y1={gy1 + (120 * Math.sin(beta)) * Math.cos(beta)}
          x2={gx1} y2={gy1 + 0} stroke="none" />
        <path d={`M ${gx1 - 90} ${gy1 + 90 * Math.sin(beta) * 1}
                  A 90 90 0 0 1 ${gx1 - 90 * dx} ${gy1 - 90 * dy}`}
          fill="none" stroke={FIG.DIM} strokeWidth="1.4" />
        <line x1={gx1 - 96} y1={gy1 + 96 * Math.sin(beta)} x2={gx1} y2={gy1}
          stroke={FIG.DIM} strokeWidth="1.2" strokeDasharray="4 4" />
        <text x={gx1 - 130} y={gy1 - 6} fontSize="16.5" fill={FIG.DIM}
          fontFamily="system-ui" stroke="#ffffff" strokeWidth="3.5"
          paintOrder="stroke">{`β = ${params.beta}°`}</text>
      </g>

      {/* soil property labels */}
      <text x={40} y={H - 22} fontSize="17" fill={FIG.SOIL_HATCH}
        fontFamily="system-ui" stroke="#ffffff" strokeWidth="3.5"
        paintOrder="stroke">{props.join("   ")}</text>
    </svg>
  );
}
