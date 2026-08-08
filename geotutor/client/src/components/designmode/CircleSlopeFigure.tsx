import { DesignStep, FigureParams } from "./types";
import { FIG, activeTargets } from "./figShared";

// Trial circle under a plane slope face, with the sliding mass cut into
// vertical slices (Swedish method). World coordinates: toe at the origin,
// x to the right, y upward; the SVG flips y.

const W = 720;
const H = 460;
const halo = { stroke: "#ffffff", strokeWidth: 3.5, paintOrder: "stroke" as const };

export function CircleSlopeFigure({
  params, steps, current,
}: {
  params: FigureParams; steps: DesignStep[]; current: number;
}) {
  const hl = activeTargets(steps, current);
  const Hs = (params.H as number) || 14;
  const beta = ((params.beta as number) || 45) * Math.PI / 180;
  const xc = (params.xc as number) || 11;
  const yc = (params.yc as number) || 20;
  const R = (params.R as number) || Math.hypot(xc, yc);
  const xExit = (params.x_exit as number) || 30;
  const bw = (params.b as number) || 2;

  // world->screen: fit x in [-2, xExit+4], y in [min arc, yc+2]
  const yArcMin = yc - R;
  const xMin = -3, xMax = xExit + 5;
  const yMin = Math.min(yArcMin, 0) - 2, yMax = Math.max(yc + 1.5, Hs + 3);
  const s = Math.min((W - 90) / (xMax - xMin), (H - 60) / (yMax - yMin));
  const px = (x: number) => 55 + (x - xMin) * s;
  const py = (y: number) => H - 34 - (y - yMin) * s;

  const ground = (x: number) => Math.min(x * Math.tan(beta), Hs);
  const arcY = (x: number) => yc - Math.sqrt(Math.max(R * R - (x - xc) * (x - xc), 0));

  // slice polygons
  const slices: string[] = [];
  let x0 = 0;
  while (x0 < xExit - 1e-6) {
    const x1 = Math.min(x0 + bw, xExit);
    const pts = [
      `${px(x0)},${py(ground(x0))}`,
      `${px(x1)},${py(ground(x1))}`,
      `${px(x1)},${py(arcY(x1))}`,
      `${px(x0)},${py(arcY(x0))}`,
    ].join(" ");
    slices.push(pts);
    x0 = x1;
  }

  // arc path between toe (0,0) and exit
  const arcPts: string[] = [];
  for (let i = 0; i <= 60; i++) {
    const x = (xExit * i) / 60;
    arcPts.push(`${px(x)},${py(arcY(x))}`);
  }

  const showSlices = hl.has("slices") || hl.has("slice1");
  const arcOn = hl.has("arc");

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto select-none" role="img"
      aria-label="Trial slip circle with the sliding mass cut into slices">
      <defs>
        <pattern id="soilHatchCirc" width="10" height="10" patternUnits="userSpaceOnUse"
          patternTransform="rotate(45)">
          <line x1="0" y1="0" x2="0" y2="10" stroke={FIG.SOIL_HATCH} strokeWidth="0.7" opacity="0.4" />
        </pattern>
      </defs>

      {/* soil body under the ground line */}
      <polygon
        points={`${px(xMin)},${py(0)} ${px(0)},${py(0)} ${px(Hs / Math.tan(beta))},${py(Hs)} ${px(xMax)},${py(Hs)} ${px(xMax)},${py(yMin + 1)} ${px(xMin)},${py(yMin + 1)}`}
        fill={FIG.SOIL_FILL} />
      <polygon
        points={`${px(xMin)},${py(0)} ${px(0)},${py(0)} ${px(Hs / Math.tan(beta))},${py(Hs)} ${px(xMax)},${py(Hs)} ${px(xMax)},${py(yMin + 1)} ${px(xMin)},${py(yMin + 1)}`}
        fill="url(#soilHatchCirc)" />

      {/* ground surface: level - face - crest */}
      <polyline
        points={`${px(xMin)},${py(0)} ${px(0)},${py(0)} ${px(Hs / Math.tan(beta))},${py(Hs)} ${px(xMax)},${py(Hs)}`}
        fill="none" stroke={FIG.INK} strokeWidth="2.2" />

      {/* slices of the sliding mass */}
      {slices.map((pts, i) => (
        <polygon key={i} points={pts}
          fill={i === 0 && hl.has("slice1") ? FIG.HL
            : showSlices ? (i % 2 ? "#fcd9a8" : "#fbe7c6") : "#f5ecd9"}
          fillOpacity={showSlices ? 0.75 : 0.4}
          stroke={showSlices ? FIG.AMBER : FIG.DIM}
          strokeWidth={showSlices ? 0.9 : 0.4} />
      ))}

      {/* the trial arc */}
      <polyline points={arcPts.join(" ")} fill="none"
        stroke={FIG.SLIP} strokeWidth={arcOn ? 3 : 1.8}
        strokeDasharray={arcOn ? "none" : "7 5"} />

      {/* centre O with radius spokes */}
      <circle cx={px(xc)} cy={py(yc)} r={5} fill={FIG.SLIP} />
      <text x={px(xc) + 10} y={py(yc) - 6} fontSize="16" fill={FIG.SLIP}
        fontFamily="system-ui" {...halo}>{`O (${xc}, ${yc})`}</text>
      <line x1={px(xc)} y1={py(yc)} x2={px(0)} y2={py(0)}
        stroke={FIG.SLIP} strokeWidth="1" strokeDasharray="4 4" />
      <line x1={px(xc)} y1={py(yc)} x2={px(xExit)} y2={py(Hs)}
        stroke={FIG.SLIP} strokeWidth="1" strokeDasharray="4 4" />
      <text x={px((xc) / 2) - 14} y={py(yc / 2) - 6} fontSize="15.5"
        fill={FIG.SLIP} fontFamily="system-ui" {...halo}>{`R = ${R} m`}</text>

      {/* toe and exit labels */}
      <text x={px(0) - 8} y={py(0) + 20} fontSize="15.5" fill={FIG.INK}
        textAnchor="end" fontFamily="system-ui" {...halo}>A (toe)</text>
      <text x={px(xExit) + 6} y={py(Hs) - 8} fontSize="15.5" fill={FIG.INK}
        fontFamily="system-ui" {...halo}>{`B (x = ${xExit} m)`}</text>

      {/* soil properties */}
      <text x={px(xMax) - 8} y={py(yMin + 1) - 10} fontSize="16" fill={FIG.SOIL_HATCH}
        textAnchor="end" fontFamily="system-ui" {...halo}>
        {`γ = ${params.gamma} kN/m³  c' = ${params.c} kPa  φ' = ${params.phi}°`}
      </text>
    </svg>
  );
}
