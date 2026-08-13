import { DesignStep, FigureParams } from "./types";
import { FIG } from "./figShared";

// General reasoning mode: no parametric geometry exists yet, so the
// tutorial visual is the computation itself - the given quantities
// flowing through the planned chain into the answer. The box whose
// symbol matches the current step's result lights up.

const W = 720;
const H = 460;
const halo = { stroke: "#ffffff", strokeWidth: 3.5, paintOrder: "stroke" as const };

interface ChainItem { target: string; value: number | string; unit?: string }

export function CalcChainFigure({
  params, steps, current,
}: {
  params: FigureParams; steps: DesignStep[]; current: number;
}) {
  const givens = (params.givens as { sym: string; value: number }[]) || [];
  const chain = (params.chain as ChainItem[]) || [];
  const answer = params.answer as { quantity: string; value: number | string; unit: string } | undefined;
  const activeSym = steps[current]?.result?.sym;

  const gPerRow = 5;
  const gw = 128, gh = 34, gGapX = 8, gGapY = 8;
  const gx0 = (W - Math.min(givens.length, gPerRow) * (gw + gGapX)) / 2;

  const cW = 250, cH = 40, cGap = 14;
  const chainX = W / 2 - cW / 2;
  const chainY0 = 60 + Math.ceil(givens.length / gPerRow) * (gh + gGapY) + 26;
  const shown = chain.slice(0, 6);
  const truncated = chain.length > shown.length;

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto select-none" role="img"
      aria-label="Computation chain of the general method">
      <text x={W / 2} y={28} fontSize="15" fill={FIG.DIM} textAnchor="middle"
        fontFamily="system-ui" {...halo}>
        {`${params.method ?? "general method"} (planned method, deterministic arithmetic)`}
      </text>

      {/* givens */}
      <text x={gx0} y={52} fontSize="13" fill={FIG.DIM} fontFamily="system-ui" {...halo}>
        given
      </text>
      {givens.map((g, i) => {
        const x = gx0 + (i % gPerRow) * (gw + gGapX);
        const y = 60 + Math.floor(i / gPerRow) * (gh + gGapY);
        return (
          <g key={g.sym}>
            <rect x={x} y={y} width={gw} height={gh} rx={8}
              fill="#eff6ff" stroke={FIG.WATER} strokeWidth="1.2" />
            <text x={x + gw / 2} y={y + gh / 2 + 5} fontSize="13"
              fill={FIG.INK} textAnchor="middle" fontFamily="ui-monospace, monospace">
              {`${g.sym} = ${g.value}`}
            </text>
          </g>
        );
      })}

      {/* chain */}
      {shown.map((c, i) => {
        const y = chainY0 + i * (cH + cGap);
        const on = activeSym === c.target;
        return (
          <g key={c.target}>
            <line x1={W / 2} y1={y - cGap} x2={W / 2} y2={y}
              stroke={FIG.DIM} strokeWidth="1.4" />
            <path d={`M ${W / 2} ${y} l -5 -8 l 10 0 z`} fill={FIG.DIM} />
            <rect x={chainX} y={y} width={cW} height={cH} rx={9}
              fill={on ? "#dbeafe" : "#ffffff"}
              stroke={on ? FIG.WATER : "#cbd5e1"}
              strokeWidth={on ? 2.4 : 1.3} />
            <text x={W / 2} y={y + cH / 2 + 5} fontSize="14"
              fill={FIG.INK} textAnchor="middle"
              fontFamily="ui-monospace, monospace">
              {`${c.target} = ${c.value}${c.unit ? " " + c.unit : ""}`}
            </text>
          </g>
        );
      })}
      {truncated && (
        <text x={W / 2} y={chainY0 + shown.length * (cH + cGap) + 4}
          fontSize="13" fill={FIG.DIM} textAnchor="middle"
          fontFamily="system-ui" {...halo}>
          {`… ${chain.length - shown.length} more steps in the player`}
        </text>
      )}

      {/* answer */}
      {answer && (
        <g>
          <rect x={W / 2 - 160} y={H - 74} width={320} height={46} rx={10}
            fill="#eff6ff" stroke={FIG.WATER} strokeWidth="2.2" />
          <text x={W / 2} y={H - 74 + 29} fontSize="16" fontWeight="600"
            fill={FIG.INK} textAnchor="middle" fontFamily="system-ui">
            {`${answer.quantity} = ${answer.value} ${answer.unit}`}
          </text>
        </g>
      )}
      <text x={W / 2} y={H - 12} fontSize="12" fill={FIG.DIM}
        textAnchor="middle" fontFamily="system-ui" {...halo}>
        general mode: verify the method independently
      </text>
    </svg>
  );
}
