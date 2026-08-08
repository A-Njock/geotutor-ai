import { DesignStep, FigureParams } from "./types";
import { FIG, activeTargets } from "./figShared";

// Braced cut: the excavation with its two walls and three strut levels,
// and Peck's apparent-pressure envelope drawn beside the left wall.
// Highlights follow the current step (envelope, upper/lower beam of the
// wall, individual struts).

const W = 720;
const H = 460;

export function BracedCutFigure({
  params, steps, current,
}: {
  params: FigureParams;
  steps: DesignStep[];
  current: number;
}) {
  const hl = activeTargets(steps, current);
  const Hcut = (params.H as number) || 9;
  const dA = (params.dA as number) ?? Hcut * 0.22;
  const dB = (params.dB as number) ?? Hcut * 0.55;
  const dC = (params.dC as number) ?? Hcut * 0.88;
  const zTri = (params.z_tri as number) || 0;
  const isClay = params.envelope === "clay";

  const GY = 92;
  const scale = 300 / Hcut;
  const sy = (d: number) => GY + d * scale;
  const bottom = sy(Hcut);
  const WL = 300, WR = 545; // wall x positions
  const ENV_X = 218;        // envelope inner edge
  const envW = 62;          // max envelope width in px

  // envelope polygon (pressure grows to the LEFT of the left wall)
  const envPts = isClay && zTri > 0
    ? `${WL},${GY} ${WL - envW},${sy(zTri)} ${WL - envW},${bottom} ${WL},${bottom}`
    : `${WL},${GY} ${WL - envW},${GY} ${WL - envW},${bottom} ${WL},${bottom}`;

  const strut = (d: number, name: string, key: string) => {
    const on = hl.has(`strut${name}`);
    return (
      <g key={key}>
        <line x1={WL} y1={sy(d)} x2={WR} y2={sy(d)}
          stroke={on ? FIG.AMBER : FIG.INK} strokeWidth={on ? 5 : 3.5} />
        <circle cx={(WL + WR) / 2} cy={sy(d)} r={13}
          fill={on ? FIG.HL : "#ffffff"} stroke={on ? FIG.AMBER : FIG.INK}
          strokeWidth="1.8" />
        <text x={(WL + WR) / 2} y={sy(d) + 5.5} fontSize="15" fontWeight="600"
          fill={FIG.INK} textAnchor="middle" fontFamily="system-ui">{name}</text>
        <text x={WR + 14} y={sy(d) + 5.5} fontSize="15" fill={FIG.DIM}
          fontFamily="system-ui" stroke="#ffffff" strokeWidth="3.5"
          paintOrder="stroke">{`${d} m`}</text>
      </g>
    );
  };

  const beamSeg = (d0: number, d1: number, on: boolean, key: string) => (
    <line key={key} x1={WL} y1={sy(d0)} x2={WL} y2={sy(d1)}
      stroke={on ? FIG.AMBER : "none"} strokeWidth="7" opacity="0.85" />
  );

  const props: string[] = [];
  if (params.gamma) props.push(`γ = ${params.gamma} kN/m³`);
  if (params.phi) props.push(`φ' = ${params.phi}°`);
  if (params.c) props.push(`c = ${params.c} kPa`);

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto select-none" role="img"
      aria-label="Braced cut with struts and the apparent-pressure envelope">
      <defs>
        <pattern id="soilHatchCut" width="10" height="10" patternUnits="userSpaceOnUse"
          patternTransform="rotate(45)">
          <line x1="0" y1="0" x2="0" y2="10" stroke={FIG.SOIL_HATCH} strokeWidth="0.7" opacity="0.45" />
        </pattern>
      </defs>

      {/* soil outside the cut and below its base */}
      <rect x={40} y={GY} width={WL - 40} height={H - GY - 16} fill={FIG.SOIL_FILL} />
      <rect x={40} y={GY} width={WL - 40} height={H - GY - 16} fill="url(#soilHatchCut)" />
      <rect x={WR} y={GY} width={W - WR - 40} height={H - GY - 16} fill={FIG.SOIL_FILL} />
      <rect x={WR} y={GY} width={W - WR - 40} height={H - GY - 16} fill="url(#soilHatchCut)" />
      <rect x={WL} y={bottom} width={WR - WL} height={H - bottom - 16} fill={FIG.SOIL_FILL} />
      <rect x={WL} y={bottom} width={WR - WL} height={H - bottom - 16} fill="url(#soilHatchCut)" />

      {/* ground surface both sides */}
      <line x1={30} y1={GY} x2={WL} y2={GY} stroke={FIG.INK} strokeWidth="2.2" />
      <line x1={WR} y1={GY} x2={W - 30} y2={GY} stroke={FIG.INK} strokeWidth="2.2" />
      {/* excavation base */}
      <line x1={WL} y1={bottom} x2={WR} y2={bottom} stroke={FIG.INK} strokeWidth="1.8" />

      {/* the two walls */}
      <line x1={WL} y1={GY} x2={WL} y2={bottom + 14}
        stroke={hl.has("walls") ? FIG.AMBER : FIG.INK}
        strokeWidth={hl.has("walls") ? 5 : 3.5} />
      <line x1={WR} y1={GY} x2={WR} y2={bottom + 14}
        stroke={hl.has("walls") ? FIG.AMBER : FIG.INK}
        strokeWidth={hl.has("walls") ? 5 : 3.5} />

      {/* beam segments of the left wall (hinge analysis) */}
      {beamSeg(0, dB, hl.has("beam_top"), "bt")}
      {beamSeg(dB, Hcut, hl.has("beam_bot"), "bb")}

      {/* struts */}
      {strut(dA, "A", "sa")}
      {strut(dB, "B", "sb")}
      {strut(dC, "C", "sc")}

      {/* apparent-pressure envelope */}
      <g opacity={hl.has("envelope") ? 1 : 0.45}>
        <polygon points={envPts} fill={FIG.SLIP} fillOpacity="0.16"
          stroke={FIG.SLIP} strokeWidth={hl.has("envelope") ? 2.4 : 1.4} />
        {[0.25, 0.5, 0.75].map((f) => {
          const y = GY + (bottom - GY) * f;
          const grow = isClay && zTri > 0
            ? Math.min(((y - GY) / scale) / zTri, 1) : 1;
          return (
            <line key={f} x1={WL - envW * grow + 4} y1={y} x2={WL - 4} y2={y}
              stroke={FIG.SLIP} strokeWidth="1.6"
              markerEnd="url(#pressArrCut)" />
          );
        })}
        <text x={WL - envW - 10} y={(GY + bottom) / 2} fontSize="15.5"
          fill={FIG.SLIP} textAnchor="end" fontFamily="system-ui"
          stroke="#ffffff" strokeWidth="3.5" paintOrder="stroke">
          {`σa = ${params.sigma_a} kPa`}
        </text>
      </g>
      <defs>
        <marker id="pressArrCut" viewBox="0 0 10 10" refX="8" refY="5"
          markerWidth="6" markerHeight="6" orient="auto">
          <path d="M0,0 L10,5 L0,10 z" fill={FIG.SLIP} />
        </marker>
      </defs>

      {/* H dimension on the right */}
      <g stroke={FIG.DIM} strokeWidth="1.2">
        <line x1={W - 92} y1={GY} x2={W - 92} y2={bottom} />
        <text x={W - 84} y={(GY + bottom) / 2 + 5} fontSize="16.5" fill={FIG.DIM}
          fontFamily="system-ui" stroke="#ffffff" strokeWidth="3.5"
          paintOrder="stroke">{`H = ${Hcut} m`}</text>
      </g>

      {/* soil property labels */}
      <text x={52} y={H - 26} fontSize="17" fill={FIG.SOIL_HATCH}
        fontFamily="system-ui" stroke="#ffffff" strokeWidth="3.5"
        paintOrder="stroke">{props.join("   ")}</text>
    </svg>
  );
}
