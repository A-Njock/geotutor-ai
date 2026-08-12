import { DesignStep, FigureParams } from "./types";
import { FIG, activeTargets } from "./figShared";

// Seepage sketches for the permeability chains: a laboratory permeameter
// (constant or falling head), a pumping test with its drawdown curve, and
// a sheet-pile flow net. params.mode picks the sketch.

const W = 720;
const H = 460;
const halo = { stroke: "#ffffff", strokeWidth: 3.5, paintOrder: "stroke" as const };

export function PermeabilityFigure({
  params, steps, current,
}: {
  params: FigureParams; steps: DesignStep[]; current: number;
}) {
  const hl = activeTargets(steps, current);
  const mode = (params.mode as string) || "constant";

  const num = (v: unknown, fallback = "?"): string =>
    v === null || v === undefined ? fallback : String(v);

  const label = (x: number, y: number, t: string,
    anchor: "start" | "middle" | "end" = "start", fill = FIG.INK) => (
    <text x={x} y={y} fontSize="15.5" fill={fill} textAnchor={anchor}
      fontFamily="system-ui" {...halo}>{t}</text>
  );

  const bottomLabel =
    params.k !== undefined && params.k !== null
      ? `k = ${params.k as number} m/s`
      : params.q !== undefined && params.q !== null
        ? `q = ${params.q as number} m³/s`
        : "";

  // ---- permeameter: shared column for constant and falling head --------
  const renderPermeameter = (falling: boolean) => {
    const CX = 300, CW = 130, CT = 190, CB = 330;
    const specimenHl = hl.has("specimen");
    const pipeHl = hl.has("standpipe");
    const datumY = 360;
    const h1Y = 74, h2Y = 134;
    return (
      <>
        {/* soil column with porous stones */}
        <rect x={CX} y={CT} width={CW} height={CB - CT} fill={FIG.SOIL_FILL}
          stroke={specimenHl ? FIG.HL : FIG.INK}
          strokeWidth={specimenHl ? 3 : 1.6} />
        <rect x={CX} y={CT} width={CW} height={CB - CT} fill="url(#soilHatchPerm)" />
        <rect x={CX} y={CT - 8} width={CW} height={8} fill="#d8d3c8" stroke={FIG.INK} strokeWidth="1" />
        <rect x={CX} y={CB} width={CW} height={8} fill="#d8d3c8" stroke={FIG.INK} strokeWidth="1" />
        {label(CX + CW / 2, (CT + CB) / 2 + 5, "soil", "middle", FIG.INK)}

        {/* flow arrows through the specimen */}
        <g opacity={specimenHl ? 1 : 0.8}>
          <line x1={CX + CW * 0.3} y1={CT + 18} x2={CX + CW * 0.3} y2={CB - 18}
            stroke={FIG.WATER} strokeWidth="2.4" markerEnd="url(#arrPerm)" />
          <line x1={CX + CW * 0.7} y1={CT + 18} x2={CX + CW * 0.7} y2={CB - 18}
            stroke={FIG.WATER} strokeWidth="2.4" markerEnd="url(#arrPerm)" />
        </g>

        {/* dimensions of the specimen */}
        <line x1={CX + CW + 22} y1={CT} x2={CX + CW + 22} y2={CB}
          stroke={FIG.DIM} strokeWidth="1.1" />
        {label(CX + CW + 30, (CT + CB) / 2 + 5, `L = ${num(params.L_s)} m`, "start", FIG.DIM)}
        <line x1={CX} y1={CB + 26} x2={CX + CW} y2={CB + 26}
          stroke={FIG.DIM} strokeWidth="1.1" />
        {label(CX + CW / 2, CB + 44, `D = ${num(params.D_s)} m`, "middle", FIG.DIM)}

        {/* tailwater basin: the outflow level is the datum */}
        <path d={`M 480 ${datumY - 18} L 480 ${datumY + 30} L 590 ${datumY + 30} L 590 ${datumY - 18}`}
          fill="none" stroke={FIG.INK} strokeWidth="1.6" />
        <rect x={481} y={datumY} width={108} height={29} fill={FIG.WATER} opacity="0.3" />
        <line x1={481} y1={datumY} x2={589} y2={datumY} stroke={FIG.WATER} strokeWidth="2" />
        <line x1={CX + CW * 0.5} y1={CB + 8} x2={CX + CW * 0.5} y2={datumY - 6}
          stroke={FIG.WATER} strokeWidth="2.2" markerEnd="url(#arrPerm)" opacity="0.7" />
        <line x1={120} y1={datumY} x2={480} y2={datumY}
          stroke={FIG.DIM} strokeWidth="1" strokeDasharray="6 5" />
        {label(596, datumY + 5, "outflow (datum)", "start", FIG.DIM)}

        {falling ? (
          <>
            {/* falling-head standpipe with the h1 and h2 marks */}
            <rect x={355} y={52} width={16} height={CT - 60}
              fill="#ffffff"
              stroke={pipeHl ? FIG.HL : FIG.INK}
              strokeWidth={pipeHl ? 3 : 1.6} />
            <rect x={357} y={h1Y} width={12} height={CT - 8 - h1Y}
              fill={FIG.WATER} opacity="0.45" />
            <line x1={357} y1={h1Y} x2={369} y2={h1Y} stroke={FIG.WATER} strokeWidth="2.4" />
            <line x1={357} y1={h2Y} x2={369} y2={h2Y} stroke={FIG.WATER} strokeWidth="2.4" />
            <line x1={363} y1={h1Y + 8} x2={363} y2={h2Y - 8}
              stroke={FIG.WATER} strokeWidth="2" markerEnd="url(#arrPerm)" />
            {label(345, h1Y + 5, `h₁ = ${num(params.h1)} m`, "end", FIG.WATER)}
            {label(345, h2Y + 5, `h₂ = ${num(params.h2)} m`, "end", FIG.WATER)}
            {label(363, 40, "standpipe, area a", "middle", FIG.DIM)}
            {label(120, datumY - 8, "heads measured to the datum", "start", FIG.DIM)}
          </>
        ) : (
          <>
            {/* constant-head reservoir with overflow, and the collector */}
            <path d="M 110 70 L 110 150 L 230 150 L 230 70"
              fill="none" stroke={FIG.INK} strokeWidth="1.8" />
            <rect x={111} y={92} width={118} height={57} fill={FIG.WATER} opacity="0.3" />
            <line x1={111} y1={92} x2={229} y2={92} stroke={FIG.WATER} strokeWidth="2.2" />
            <line x1={230} y1={92} x2={252} y2={100} stroke={FIG.WATER} strokeWidth="2" />
            {label(170, 62, "constant head", "middle", FIG.DIM)}
            {label(258, 106, "overflow", "start", FIG.DIM)}
            <polyline points={`230,142 ${CX + CW * 0.5},142 ${CX + CW * 0.5},${CT - 8}`}
              fill="none" stroke={FIG.WATER} strokeWidth="5" opacity="0.55" />

            {/* head difference driving the flow */}
            <line x1={86} y1={92} x2={86} y2={datumY} stroke={FIG.DIM} strokeWidth="1.1" />
            <line x1={80} y1={92} x2={92} y2={92} stroke={FIG.DIM} strokeWidth="1.1" />
            <line x1={80} y1={datumY} x2={92} y2={datumY} stroke={FIG.DIM} strokeWidth="1.1" />
            {label(74, (92 + datumY) / 2 + 5, `h = ${num(params.h)} m`, "end", FIG.DIM)}

            {/* collection beaker */}
            <path d={`M 500 ${CB - 4} L 500 ${CB + 60} L 566 ${CB + 60} L 566 ${CB - 4}`}
              fill="none" stroke={FIG.INK} strokeWidth="1.6" />
            <rect x={501} y={CB + 24} width={64} height={35} fill={FIG.WATER} opacity="0.35" />
            <polyline points={`${CX + CW},${CB - 12} 470,${CB - 12} 530,${CB + 18}`}
              fill="none" stroke={FIG.WATER} strokeWidth="2.2" markerEnd="url(#arrPerm)" />
            {label(533, CB + 78, "collected Q", "middle", FIG.DIM)}
          </>
        )}
      </>
    );
  };

  // ---- pumping test with drawdown through two observation wells --------
  const renderPumping = () => {
    const wellsHl = hl.has("wells");
    const groundY = 150, baseY = 400, wtY = 195;
    const wellX = 360, r1X = 460, r2X = 575;
    const curveAt = (x: number) => {
      // sketched drawdown: deep at the well, easing back to the water table
      const d = Math.min(Math.abs(x - wellX), 290);
      return 332 - (137 * d) / (d + 55);
    };
    const hw1Y = curveAt(r1X);
    const hw2Y = curveAt(r2X);
    return (
      <>
        {/* aquifer between the ground line and the impermeable base */}
        <rect x={60} y={groundY} width={600} height={baseY - groundY} fill={FIG.SOIL_FILL} />
        <rect x={60} y={groundY} width={600} height={baseY - groundY} fill="url(#soilHatchPerm)" />
        <line x1={60} y1={groundY} x2={660} y2={groundY} stroke={FIG.INK} strokeWidth="2.2" />
        <line x1={60} y1={baseY} x2={660} y2={baseY} stroke={FIG.INK} strokeWidth="2.2" />
        {label(66, groundY - 8, "ground", "start", FIG.DIM)}
        {label(66, baseY + 20, "impermeable base", "start", FIG.DIM)}

        {/* initial water table */}
        <line x1={60} y1={wtY} x2={660} y2={wtY}
          stroke={FIG.WATER} strokeWidth="1.6" strokeDasharray="7 5" opacity="0.7" />
        {label(654, wtY - 8, "initial WT", "end", FIG.WATER)}

        {/* pumped well */}
        <rect x={wellX - 11} y={groundY - 40} width={22} height={baseY - groundY + 30}
          fill="#ffffff" stroke={FIG.INK} strokeWidth="1.8" />
        <line x1={wellX} y1={groundY - 46} x2={wellX} y2={groundY - 82}
          stroke={FIG.WATER} strokeWidth="2.6" markerEnd="url(#arrPerm)" />
        {label(wellX, groundY - 90, `pumping q = ${num(params.q)} m³/s`, "middle", FIG.WATER)}

        {/* drawdown curve */}
        <path d={`M 70 ${curveAt(70)} Q 240 ${curveAt(210)} ${wellX - 11} 330`}
          fill="none" stroke={FIG.WATER} strokeWidth="2.4" />
        <path d={`M ${wellX + 11} 330 Q 480 ${curveAt(510)} 650 ${curveAt(650)}`}
          fill="none" stroke={FIG.WATER} strokeWidth="2.4" />
        {label(180, 250, "drawdown", "start", FIG.WATER)}

        {/* observation wells at r1 and r2 */}
        {[{ x: r1X, hy: hw1Y, r: params.r1, hw: params.hw1, n: 1 },
          { x: r2X, hy: hw2Y, r: params.r2, hw: params.hw2, n: 2 }].map((o) => (
          <g key={o.n}>
            <rect x={o.x - 5} y={groundY} width={10} height={baseY - groundY - 10}
              fill="#ffffff"
              stroke={wellsHl ? FIG.HL : FIG.INK}
              strokeWidth={wellsHl ? 2.6 : 1.4} />
            <line x1={o.x - 5} y1={o.hy} x2={o.x + 5} y2={o.hy}
              stroke={FIG.WATER} strokeWidth="3" />
            <line x1={o.x} y1={o.hy} x2={o.x} y2={baseY}
              stroke={FIG.WATER} strokeWidth="1.2" strokeDasharray="3 3" />
            {label(o.x + 10, (o.hy + baseY) / 2,
              `hw${o.n} = ${num(o.hw)} m`, "start", FIG.WATER)}
            <line x1={wellX} y1={groundY - (o.n === 1 ? 14 : 30)}
              x2={o.x} y2={groundY - (o.n === 1 ? 14 : 30)}
              stroke={FIG.DIM} strokeWidth="1.1" strokeDasharray="5 4" />
            {label(o.x + 6, groundY - (o.n === 1 ? 10 : 26),
              `r${o.n} = ${num(o.r)} m`, "start", FIG.DIM)}
          </g>
        ))}
      </>
    );
  };

  // ---- flow net under a sheet-pile wall --------------------------------
  const renderFlownet = () => {
    const netHl = hl.has("net");
    const Nf = (params.Nf as number) || 4;
    const Nd = (params.Nd as number) || 8;
    const soilT = 190, soilB = 400, soilL = 130, soilR = 610;
    const wallX = 360, wallBot = 300;
    const shownF = Math.max(2, Math.min(Math.round(Nf), 5));
    const shownD = Math.max(3, Math.min(Math.round(Nd), 8));
    return (
      <>
        {/* soil box */}
        <rect x={soilL} y={soilT} width={soilR - soilL} height={soilB - soilT}
          fill={FIG.SOIL_FILL} stroke={FIG.INK} strokeWidth="1.8" />
        <rect x={soilL} y={soilT} width={soilR - soilL} height={soilB - soilT}
          fill="url(#soilHatchPerm)" />
        {label(soilL + 6, soilB + 20, "impermeable base", "start", FIG.DIM)}

        {/* water on both sides of the wall */}
        <rect x={soilL} y={130} width={wallX - 5 - soilL} height={soilT - 130}
          fill={FIG.WATER} opacity="0.3" />
        <line x1={soilL} y1={130} x2={wallX - 5} y2={130} stroke={FIG.WATER} strokeWidth="2.2" />
        {label(soilL + 6, 122, "upstream", "start", FIG.WATER)}
        <rect x={wallX + 5} y={166} width={soilR - wallX - 5} height={soilT - 166}
          fill={FIG.WATER} opacity="0.3" />
        <line x1={wallX + 5} y1={166} x2={soilR} y2={166} stroke={FIG.WATER} strokeWidth="2.2" />
        {label(soilR - 6, 158, "downstream", "end", FIG.WATER)}

        {/* the embedded wall */}
        <rect x={wallX - 5} y={104} width={10} height={wallBot - 104}
          fill="#475569" stroke={FIG.INK} strokeWidth="1.4" />
        {label(wallX, 96, "wall", "middle", FIG.INK)}

        {/* equipotential drops fanning around the wall tip */}
        <g opacity={netHl ? 0.95 : 0.6}>
          {Array.from({ length: shownD }, (_, j) => {
            const t = (j + 0.5) / shownD;
            const a = Math.PI * (1 - t);
            const x1 = wallX + 26 * Math.cos(a), y1 = wallBot + 8 + 26 * Math.sin(a);
            const x2 = wallX + 92 * Math.cos(a), y2 = wallBot + 8 + 92 * Math.sin(a);
            return (
              <line key={j} x1={x1} y1={y1} x2={x2} y2={y2}
                stroke={FIG.DIM} strokeWidth="1.4" strokeDasharray="5 4" />
            );
          })}
        </g>

        {/* flow lines dipping under the wall */}
        <g opacity={netHl ? 1 : 0.85}>
          {Array.from({ length: shownF }, (_, i) => {
            const sy = 206 + i * 15;
            const tipY = Math.min(316 + i * 20, soilB - 10);
            return (
              <path key={i}
                d={`M 165 ${sy} C 295 ${tipY}, 425 ${tipY}, 555 ${206 + i * 15}`}
                fill="none"
                stroke={netHl ? FIG.HL : FIG.WATER}
                strokeWidth="2.2" markerEnd="url(#arrPerm)" />
            );
          })}
        </g>
        {label(soilL + 6, soilT + 18, `Nf = ${num(params.Nf)} flow channels`, "start", FIG.WATER)}
        {label(soilR - 6, soilT + 18, `Nd = ${num(params.Nd)} drops`, "end", FIG.DIM)}
      </>
    );
  };

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto select-none" role="img"
      aria-label="Permeability and seepage sketch">
      <defs>
        <pattern id="soilHatchPerm" width="10" height="10" patternUnits="userSpaceOnUse"
          patternTransform="rotate(45)">
          <line x1="0" y1="0" x2="0" y2="10" stroke={FIG.SOIL_HATCH} strokeWidth="0.7" opacity="0.4" />
        </pattern>
        <marker id="arrPerm" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6"
          markerHeight="6" orient="auto">
          <path d="M0,0 L10,5 L0,10 z" fill={FIG.WATER} />
        </marker>
      </defs>

      {mode === "pumping"
        ? renderPumping()
        : mode === "flownet"
          ? renderFlownet()
          : renderPermeameter(mode === "falling")}

      {bottomLabel && label(130, H - 14, bottomLabel, "start", FIG.INK)}
    </svg>
  );
}
