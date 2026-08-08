import { useMemo } from "react";
import { DesignStep, FigureParams } from "./types";

// Parametric cross-section of a shallow foundation, drawn to scale from the
// solver's figure parameters. The figure is a pure function of
// (params, steps, current): accumulating ops persist, highlights follow the
// current step only. Colours reuse the app's established evidence palette.

const W = 720;
const H = 460;
const GROUND_Y = 120;
const SOIL = { fill: "#f3e9dd", hatch: "#9a6b3f" };
const INK = "#334155";
const DIM = "#64748b";
const WATER = "#2272b5";
const SLIP = "#b91c1c";
const HL = "#f59e0b";

import { activeTargets, accumulated } from "./figShared";

export function FootingFigure({
  params, steps, current,
}: {
  params: FigureParams;
  steps: DesignStep[];
  current: number;
}) {
  const hl = activeTargets(steps, current);
  const bprimeOp = accumulated(steps, current, "bprime");

  const geo = useMemo(() => {
    const B = Math.max(params.B || 1, 0.3);
    const Df = Math.max(params.Df || 0, 0);
    const worldDepth = Df + 1.9 * B;          // soil shown below ground
    const worldWidth = Math.max(4 * B, B + 4); // metres across
    const pxPerM = Math.min((H - GROUND_Y - 40) / worldDepth, (W - 160) / worldWidth);
    const cx = W / 2;
    const sx = (m: number) => cx + m * pxPerM;          // m from centreline
    const sy = (m: number) => GROUND_Y + m * pxPerM;    // m below ground
    return { B, Df, pxPerM, cx, sx, sy, worldWidth };
  }, [params]);

  const { B, Df, sx, sy, cx } = geo;
  const baseY = sy(Df);
  const footW = B * geo.pxPerM;
  const soilLeft = 70;
  const soilRight = W - 70;
  const soilBottom = H - 24;
  const Dw = params.Dw ?? null;
  const wedgeDepth = Df + 0.9 * B;

  const props: string[] = [];
  if (params.gamma) props.push(`γ = ${params.gamma} kN/m³`);
  if (params.phi) props.push(`φ = ${params.phi}°`);
  if (params.su) props.push(`sᵤ = ${params.su} kPa`);
  else if (params.c) props.push(`c = ${params.c} kPa`);

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto select-none" role="img"
      aria-label="Cross-section of the shallow foundation">
      <defs>
        <pattern id="soilHatchDsg" width="10" height="10" patternUnits="userSpaceOnUse"
          patternTransform="rotate(45)">
          <line x1="0" y1="0" x2="0" y2="10" stroke={SOIL.hatch} strokeWidth="0.7" opacity="0.45" />
        </pattern>
        <marker id="dimArrowDsg" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="7"
          markerHeight="7" orient="auto-start-reverse">
          <path d="M0,0 L8,4 L0,8 z" fill={DIM} />
        </marker>
        <marker id="loadArrowInkDsg" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="8"
          markerHeight="8" orient="auto">
          <path d="M0,0 L10,5 L0,10 z" fill={INK} />
        </marker>
        <marker id="loadArrowAmberDsg" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="8"
          markerHeight="8" orient="auto">
          <path d="M0,0 L10,5 L0,10 z" fill="#b45309" />
        </marker>
        <marker id="pressArrowDsg" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7"
          markerHeight="7" orient="auto">
          <path d="M0,0 L10,5 L0,10 z" fill={SLIP} />
        </marker>
      </defs>

      {/* soil mass */}
      <rect x={soilLeft} y={GROUND_Y} width={soilRight - soilLeft} height={soilBottom - GROUND_Y}
        fill={SOIL.fill} stroke="none" />
      <rect x={soilLeft} y={GROUND_Y} width={soilRight - soilLeft} height={soilBottom - GROUND_Y}
        fill="url(#soilHatchDsg)" />

      {/* submerged tint below the water table */}
      {Dw !== null && sy(Dw) < soilBottom && (
        <rect x={soilLeft} y={Math.max(sy(Dw), GROUND_Y)} width={soilRight - soilLeft}
          height={soilBottom - Math.max(sy(Dw), GROUND_Y)}
          fill={WATER} opacity={hl.has("water") ? 0.22 : 0.1} />
      )}

      {/* surcharge zone: soil beside the footing, above base level */}
      {Df > 0 && (
        <g opacity={hl.has("surcharge_zone") ? 1 : 0}>
          <rect x={soilLeft} y={GROUND_Y} width={cx - footW / 2 - soilLeft}
            height={baseY - GROUND_Y} fill={HL} opacity="0.28" />
          <rect x={cx + footW / 2} y={GROUND_Y} width={soilRight - cx - footW / 2}
            height={baseY - GROUND_Y} fill={HL} opacity="0.28" />
        </g>
      )}

      {/* ground surface */}
      <line x1={soilLeft - 12} y1={GROUND_Y} x2={soilRight + 12} y2={GROUND_Y}
        stroke={INK} strokeWidth="2" />

      {/* failure wedge and slip lines: drawn only when the current step
          enacts the bearing-failure mechanism, never on the problem figure */}
      {hl.has("wedge") && (
        <g>
          <path
            d={`M ${cx - footW / 2} ${baseY} L ${cx} ${sy(wedgeDepth)} L ${cx + footW / 2} ${baseY}`}
            fill={HL} fillOpacity="0.2"
            stroke={SLIP} strokeWidth="1.4" strokeDasharray="5 4" />
          <path
            d={`M ${cx + footW / 2} ${baseY} Q ${cx + footW * 1.15} ${sy(wedgeDepth) + 6} ${cx + footW * 1.9} ${baseY}`}
            fill="none" stroke={SLIP} strokeWidth="1.2" strokeDasharray="5 4" />
          <path
            d={`M ${cx - footW / 2} ${baseY} Q ${cx - footW * 1.15} ${sy(wedgeDepth) + 6} ${cx - footW * 1.9} ${baseY}`}
            fill="none" stroke={SLIP} strokeWidth="1.2" strokeDasharray="5 4" />
        </g>
      )}

      {/* surcharge arrows: overburden pressing on the base level */}
      {Df > 0 && hl.has("surcharge_zone") && (
        <g stroke="#b45309" strokeWidth="1.6">
          {[0.28, 0.5, 0.72].flatMap((f) => {
            const y0 = GROUND_Y + (baseY - GROUND_Y) * 0.25;
            const y1 = baseY - 5;
            const dimX = cx - footW / 2 - 44; // keep clear of the Df dimension
            const xl = soilLeft + (cx - footW / 2 - soilLeft) * f;
            const xr = cx + footW / 2 + (soilRight - cx - footW / 2) * f;
            const out = [];
            if (Math.abs(xl - dimX) > 34)
              out.push(<line key={`sl${f}`} x1={xl} y1={y0} x2={xl} y2={y1} markerEnd="url(#loadArrowAmberDsg)" />);
            out.push(<line key={`sr${f}`} x1={xr} y1={y0} x2={xr} y2={y1} markerEnd="url(#loadArrowAmberDsg)" />);
            return out;
          })}
        </g>
      )}

      {/* bearing pressure block under the base */}
      {hl.has("pressure") && (
        <g>
          <rect x={cx - footW / 2} y={baseY} width={footW} height={16}
            fill={SLIP} opacity="0.18" />
          <g stroke={SLIP} strokeWidth="1.5">
            {[0.12, 0.3, 0.5, 0.7, 0.88].map((f) => (
              <line key={f} x1={cx - footW / 2 + footW * f} y1={baseY + 24}
                x2={cx - footW / 2 + footW * f} y2={baseY + 4}
                markerEnd="url(#pressArrowDsg)" />
            ))}
          </g>
        </g>
      )}

      {/* footing + column stub + applied load */}
      <g>
        <rect x={cx - footW / 2} y={baseY - 16} width={footW} height={16}
          fill={hl.has("footing") ? "#fde68a" : "#e2e8f0"} stroke={INK} strokeWidth="1.6" />
        <rect x={cx - 12} y={GROUND_Y - 34} width={24} height={baseY - 16 - (GROUND_Y - 34)}
          fill="#e2e8f0" stroke={INK} strokeWidth="1.4" />
        {/* the load, drawn ONLY when the problem actually involves one
            (given load, or the allowable load being sought) */}
        {params.load_label && (() => {
          const eOff = ((params.e_load as number) || 0) * geo.pxPerM;
          const lx = cx + eOff;
          return (
            <g opacity={hl.has("load") ? 1 : 0.65}>
              {eOff > 0 && (
                <g>
                  <line x1={cx} y1={GROUND_Y - 100} x2={cx} y2={baseY - 16}
                    stroke={DIM} strokeWidth="1" strokeDasharray="5 4" />
                  <text x={(cx + lx) / 2} y={GROUND_Y - 104} fontSize="14.5"
                    fill={DIM} textAnchor="middle" fontFamily="system-ui"
                    stroke="#ffffff" strokeWidth="3.5" paintOrder="stroke">
                    {`e = ${params.e_load} m`}
                  </text>
                </g>
              )}
              <line x1={lx} y1={GROUND_Y - 88} x2={lx} y2={GROUND_Y - 38}
                stroke={hl.has("load") ? "#b45309" : INK}
                strokeWidth={hl.has("load") ? 3 : 2}
                markerEnd={hl.has("load") ? "url(#loadArrowAmberDsg)" : "url(#loadArrowInkDsg)"} />
              <text x={lx + 10} y={GROUND_Y - 62} fontSize="16" fontStyle="italic"
                fill={hl.has("load") ? "#b45309" : INK} fontFamily="system-ui" stroke="#ffffff" strokeWidth="3.5" paintOrder="stroke">
                {params.load_label === "Q_all" ? "Qₐₗₗ" : params.load_label === "Q_ult" ? "Qᵤₗₜ" : params.load_label}
              </text>
            </g>
          );
        })()}
      </g>

      {/* water table marker */}
      {Dw !== null && (
        <g>
          <line x1={soilLeft - 8} y1={sy(Dw)} x2={soilRight + 8} y2={sy(Dw)}
            stroke={WATER} strokeWidth="1.6" strokeDasharray="8 5" />
          <path d={`M ${soilRight - 26} ${sy(Dw) - 12} l 12 0 l -6 10 z`} fill={WATER} />
          <text x={soilRight - 60} y={sy(Dw) - 16} fontSize="16" fill={WATER}
            fontFamily="system-ui" stroke="#ffffff" strokeWidth="3.5" paintOrder="stroke">{`Dw = ${Dw} m`}</text>
        </g>
      )}

      {/* Df dimension, left of the footing */}
      {Df > 0 && (
        <g stroke={DIM} strokeWidth="1.2">
          <line x1={cx - footW / 2 - 44} y1={GROUND_Y} x2={cx - footW / 2 - 44} y2={baseY}
            markerStart="url(#dimArrowDsg)" markerEnd="url(#dimArrowDsg)" />
          <text x={cx - footW / 2 - 52} y={(GROUND_Y + baseY) / 2 + 4} fontSize="16.5"
            fill={DIM} textAnchor="end" fontFamily="system-ui" stroke="#ffffff"
            strokeWidth="3.5" paintOrder="stroke">
            {`Df = ${Df} m`}
          </text>
        </g>
      )}

      {/* B dimension, under the footing */}
      <g stroke={DIM} strokeWidth="1.2">
        <line x1={cx - footW / 2} y1={baseY + 26} x2={cx + footW / 2} y2={baseY + 26}
          markerStart="url(#dimArrowDsg)" markerEnd="url(#dimArrowDsg)" />
        <text x={cx} y={baseY + 44} fontSize="16.5" fill={DIM} textAnchor="middle"
          fontFamily="system-ui" stroke="#ffffff" strokeWidth="3.5" paintOrder="stroke">{`B = ${B} m`}</text>
      </g>

      {/* soil property labels */}
      <text x={soilLeft + 14} y={soilBottom - 16} fontSize="17" fill={SOIL.hatch}
        fontFamily="system-ui" stroke="#ffffff" strokeWidth="3.5" paintOrder="stroke">
        {props.join("   ")}
      </text>

      {/* effective width B' after the eccentricity step (accumulates) */}
      {bprimeOp?.Bp && (
        <g>
          <rect x={cx - footW / 2 + (B - (bprimeOp.Bp as number)) * geo.pxPerM}
            y={baseY - 16}
            width={(bprimeOp.Bp as number) * geo.pxPerM} height={16}
            fill={HL} opacity="0.5" stroke="#b45309" strokeWidth="1.4" />
          <text x={cx + ((B - (bprimeOp.Bp as number)) * geo.pxPerM) / 2}
            y={baseY + 64} fontSize="16" fill="#b45309" textAnchor="middle"
            fontFamily="system-ui" stroke="#ffffff" strokeWidth="3.5"
            paintOrder="stroke">{`B' = ${bprimeOp.Bp} m`}</text>
        </g>
      )}
    </svg>
  );
}
