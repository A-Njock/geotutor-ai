"""Driven piles: point capacity, side resistance and elastic settlement.

Point capacity compares Meyerhof (Nq* table with the limiting value),
Coyle & Castello (chart) and Vesic (closed-form N-sigma* from the reduced
rigidity index). The two Coyle & Castello charts are digitized from the
vector paths of Das PFE SI 7e (Figs 11.15 and 11.17) and validated against
the book's own worked reading; the tolerance is disclosed in provenance.
"""

import math
import re

from ..compute import display_round

PA = 100.0  # atmospheric pressure, kN/m^2

# Meyerhof's Nq* (Das, Principles of Foundation Engineering, per-degree table
# interpolated from Meyerhof's theory; full 20-45 degree run)
_MEYERHOF_NQ = [
    (20, 12.4), (21, 13.8), (22, 15.5), (23, 17.9), (24, 21.4), (25, 26.0),
    (26, 29.5), (27, 34.0), (28, 39.7), (29, 46.5), (30, 56.7), (31, 68.2),
    (32, 81.0), (33, 96.0), (34, 115.0), (35, 143.0), (36, 168.0),
    (37, 194.0), (38, 231.0), (39, 276.0), (40, 346.0), (41, 420.0),
    (42, 525.0), (43, 650.0), (44, 780.0), (45, 930.0),
]


def _meyerhof_nq_star(phi):
    pts = _MEYERHOF_NQ
    if phi <= pts[0][0]:
        return pts[0][1]
    if phi >= pts[-1][0]:
        return pts[-1][1]
    for (p0, v0), (p1, v1) in zip(pts, pts[1:]):
        if p0 <= phi <= p1:
            f = (phi - p0) / (p1 - p0)
            return math.exp(math.log(v0) + f * (math.log(v1) - math.log(v0)))
    return pts[-1][1]


# Coyle & Castello (1981) charts, digitized from the vector paths of Das,
# Principles of Foundation Engineering SI 7e, Fig 11.15 (Nq* vs L/D) and
# Fig 11.17 (K vs L/D). Axis calibration residual < 3 % of a log decade;
# validated against the book's own reading (Nq* ~ 48 at phi' 35, L/D 33.3 ->
# digitized 45.9). The phi' = 42 Nq* curve lies BEYOND the published chart:
# it follows the 40-degree curve's shape, anchored on the course text's
# reading Nq* = 100 at L/D = 33.7, and its provenance says so.
_CC_NQ = {
    30: [(0, 23.8), (5, 26.6), (10, 28.7), (15, 30.0), (20, 30.7), (25, 30.4),
         (30, 28.8), (35, 26.7), (40, 24.5), (45, 22.2), (50, 20.0),
         (55, 18.0), (60, 16.2), (65, 14.5)],
    32: [(0, 28.9), (5, 32.3), (10, 34.8), (15, 36.5), (20, 37.3), (25, 36.9),
         (30, 35.0), (35, 32.4), (40, 29.7), (45, 27.0), (50, 24.3),
         (55, 21.9), (60, 19.6), (65, 17.6)],
    34: [(0, 34.5), (5, 38.6), (10, 41.6), (15, 43.6), (20, 44.6), (25, 44.0),
         (30, 41.8), (35, 38.7), (40, 35.5), (45, 32.2), (50, 29.0),
         (55, 26.1), (60, 23.5), (65, 21.0)],
    36: [(0, 45.4), (5, 50.8), (10, 54.7), (15, 57.3), (20, 58.8), (25, 58.3),
         (30, 55.7), (35, 51.7), (40, 47.5), (45, 43.2), (50, 39.0),
         (55, 35.1), (60, 31.6), (65, 28.3)],
    38: [(0, 59.7), (5, 66.9), (10, 72.0), (15, 75.2), (20, 77.0), (25, 76.7),
         (30, 73.8), (35, 69.0), (40, 63.4), (45, 57.5), (50, 51.9),
         (55, 46.6), (60, 41.8), (65, 37.4)],
    40: [(0, 78.6), (5, 88.0), (10, 94.8), (15, 99.0), (20, 101.2),
         (25, 100.6), (30, 96.4), (35, 90.0), (40, 82.8), (45, 75.6),
         (50, 68.7), (55, 62.3), (60, 56.4), (65, 50.8)],
}
# phi 42: 40-degree shape scaled so Nq*(42, 33.7) = 100 (course text reading)
_CC_NQ[42] = [(ld, round(v * 1.0905, 1)) for ld, v in _CC_NQ[40]]

_CC_K = {
    30: [(4, 1.162), (8, 0.988), (12, 0.840), (16, 0.714), (20, 0.607),
         (24, 0.516), (28, 0.439), (32, 0.373), (36, 0.317)],
    31: [(0, 1.576), (4, 1.340), (8, 1.139), (12, 0.968), (16, 0.823),
         (20, 0.700), (24, 0.595), (28, 0.506), (32, 0.430), (36, 0.366)],
    32: [(0, 1.849), (4, 1.572), (8, 1.336), (12, 1.136), (16, 0.966),
         (20, 0.821), (24, 0.698), (28, 0.594), (32, 0.505), (36, 0.429)],
    33: [(0, 2.216), (4, 1.884), (8, 1.602), (12, 1.362), (16, 1.158),
         (20, 0.984), (24, 0.837), (28, 0.712), (32, 0.605), (36, 0.515)],
    34: [(0, 2.763), (4, 2.349), (8, 1.997), (12, 1.698), (16, 1.444),
         (20, 1.227), (24, 1.044), (28, 0.887), (32, 0.754), (36, 0.641)],
    35: [(0, 3.542), (4, 3.011), (8, 2.560), (12, 2.177), (16, 1.851),
         (20, 1.574), (24, 1.338), (28, 1.138), (32, 0.967), (36, 0.822)],
    36: [(0, 4.507), (4, 3.832), (8, 3.258), (12, 2.770), (16, 2.355),
         (20, 2.002), (24, 1.702), (28, 1.447), (32, 1.231), (36, 1.046)],
}


def _interp(pts, x):
    if x <= pts[0][0]:
        return pts[0][1]
    if x >= pts[-1][0]:
        return pts[-1][1]
    for (a, va), (b, vb) in zip(pts, pts[1:]):
        if a <= x <= b:
            return va + (vb - va) * (x - a) / (b - a)
    return pts[-1][1]


def _curve_family(table, phi, ld):
    """Linear in L/D along each curve, log-linear across phi between curves;
    clamped to the outermost curves (disclosed in the provenance)."""
    phis = sorted(table)
    if phi <= phis[0]:
        return _interp(table[phis[0]], ld)
    if phi >= phis[-1]:
        return _interp(table[phis[-1]], ld)
    for p0, p1 in zip(phis, phis[1:]):
        if p0 <= phi <= p1:
            v0 = _interp(table[p0], ld)
            v1 = _interp(table[p1], ld)
            f = (phi - p0) / (p1 - p0)
            return math.exp(math.log(v0) + f * (math.log(v1) - math.log(v0)))
    return _interp(table[phis[-1]], ld)


def _cc_nq_star(phi, ld):
    return _curve_family(_CC_NQ, phi, ld)


def _cc_k(phi, ld):
    return _curve_family(_CC_K, phi, ld)


_SIDE_RE = re.compile(r"side resistance|skin friction|shaft resistance|Q_?s\b",
                      re.IGNORECASE)
_SETTLE_RE = re.compile(r"settlement", re.IGNORECASE)


def build(frame: dict, givens: dict, add, problem_text: str) -> dict:
    if _SETTLE_RE.search(problem_text):
        return _settlement(frame, givens, add)
    if _SIDE_RE.search(problem_text):
        return _side(frame, givens, add, problem_text)
    return _point(frame, givens, add)


# ---------------------------------------------------------------------------
# ultimate point load: Meyerhof / Coyle & Castello / Vesic
# ---------------------------------------------------------------------------

def _point(frame, givens, add):
    L = givens.get("L")
    D = givens.get("D", givens.get("B"))
    phi1, gamma1 = givens.get("phi"), givens.get("gamma")
    phi2 = givens.get("phi2", phi1)
    missing = [n for n, v in (("L", L), ("pile width D", D),
                              ("phi of the soil above the tip", phi1),
                              ("gamma of the soil above the tip", gamma1))
               if v is None]
    if missing:
        return {"error": "The pile point-capacity check needs "
                         + ", ".join(missing) + "."}
    if D > 3.0:  # a pile "width" in metres should be small; mm slipped through
        D = D / 1000.0
        add("assume", "Pile width read in millimetres", "setup",
            tex=f"D = {D:g}\\ \\text{{m}}", augmented=True)

    Ap = D * D
    qp = gamma1 * L  # effective stress at the tip (shaft crosses layer 1)
    add("compute", "Effective vertical stress at the pile tip", "setup",
        tex="q' = \\gamma L",
        sub=f"q' = ({gamma1:g})({L:g})",
        result={"sym": "q_tip", "value": qp, "unit": "kPa",
                "display": f"q' = {display_round(qp)} kPa"},
        narration="The shaft crosses the upper layer, so its unit weight "
                  "builds the effective stress the tip feels.",
        viz=[{"op": "highlight", "target": "tip"}])

    results = []
    # -- Meyerhof ----------------------------------------------------------
    nq = _meyerhof_nq_star(phi2)
    add("lookup", "Meyerhof: bearing-capacity factor Nq*", "method:Meyerhof",
        tex=f"\\phi' = {phi2:g}^\\circ \\Rightarrow N_q^* = {nq:.0f}",
        provenance=[{"symbol": "Nq*", "value": round(nq),
                     "means": "converts the tip's effective stress into an "
                              "ultimate point pressure for a deep foundation",
                     "source": "the standard table of Nq* interpolated from "
                               "Meyerhof's theory (Table 11.5 in the course "
                               "textbook)",
                     "arguments": [f"φ' = {phi2:g}° of the bearing layer"],
                     "whyApplies": "read at the bearing layer's friction "
                                   "angle, not the layer the shaft passes "
                                   "through"}],
        viz=[{"op": "highlight", "target": "tip"}])
    Qp_raw = Ap * qp * nq
    Qp_lim = Ap * (0.5 * PA * nq * math.tan(math.radians(phi2)))
    Qp_m = min(Qp_raw, Qp_lim)
    add("compute", "Meyerhof: point load with the limiting value",
        "method:Meyerhof",
        tex="Q_p = A_p q' N_q^* \\le A_p(0.5\\,p_a N_q^* \\tan\\phi')",
        sub=(f"Q_p = \\min({display_round(Qp_raw):g},\\ "
             f"{display_round(Qp_lim):g})"),
        result={"sym": "Qp", "value": Qp_m, "unit": "kN",
                "display": f"Qp = {display_round(Qp_m):g} kN"},
        narration="Meyerhof caps the point resistance: beyond a critical "
                  "depth the tip pressure stops growing with depth, which "
                  "the limiting value represents.",
        viz=[{"op": "highlight", "target": "tip"},
             {"op": "highlight", "target": "point_arrows"}])
    results.append({"method": "Meyerhof", "label": "Meyerhof (1976) with "
                    "the limiting point resistance", "q_ult": Qp_m})

    # -- Coyle & Castello --------------------------------------------------
    ld = L / D
    nq_cc = _cc_nq_star(phi2, ld)
    add("lookup", "Coyle & Castello: Nq* from the chart", "method:Coyle",
        tex=f"\\tfrac{{L}}{{D}} = {ld:.1f},\\ \\phi' = {phi2:g}^\\circ "
            f"\\Rightarrow N_q^* \\approx {nq_cc:.0f}",
        provenance=[{"symbol": "Nq*", "value": round(nq_cc),
                     "means": "point bearing factor back-figured from "
                              "full-scale pile load tests",
                     "source": "the Coyle and Castello (1981) chart, Das "
                               "Fig. 11.15, digitized from the book's vector "
                               "graphics (about ±5 %); beyond φ' = 40° the "
                               "curve is an extension anchored on the course "
                               "text's own reading",
                     "arguments": [f"φ' = {phi2:g}°", f"L/D = {ld:.1f}"],
                     "whyApplies": "unlike Meyerhof's table it accounts for "
                                   "the pile's slenderness"}],
        viz=[{"op": "highlight", "target": "shaft"}])
    Qp_cc = qp * nq_cc * Ap
    add("compute", "Coyle & Castello: point load", "method:Coyle",
        tex="Q_p = q' N_q^* A_p",
        sub=f"Q_p = ({display_round(qp):g})({nq_cc:.0f})({Ap:.4g})",
        result={"sym": "Qp", "value": Qp_cc, "unit": "kN",
                "display": f"Qp = {display_round(Qp_cc):g} kN"},
        viz=[{"op": "highlight", "target": "point_arrows"}])
    results.append({"method": "Coyle-Castello",
                    "label": "Coyle and Castello (1981) chart",
                    "q_ult": Qp_cc})

    # -- Vesic -------------------------------------------------------------
    p2 = math.radians(phi2)
    m = givens.get("Es")  # Es may arrive as the ratio m = Es/pa or as kPa
    m_ratio = None
    for a in frame.get("assumptions_made", []):
        mm = re.search(r"m\s*=\s*(\d+)", str(a))
        if mm:
            m_ratio = float(mm.group(1))
    if m_ratio is None and m is not None:
        m_ratio = m / PA if m > 2000 else m
    if m_ratio is None:
        m_ratio = 600.0
        add("assume", "Soil modulus ratio", "method:Vesic",
            tex="m = E_s/p_a = 600", augmented=True,
            narration="No modulus was given, so the usual dense-sand ratio "
                      "of six hundred is used.")
    sig_m = (1.0 + 2.0 * (1.0 - math.sin(p2))) / 3.0 * qp
    Es = m_ratio * PA
    mu = 0.1 + 0.3 * (phi2 - 25.0) / 20.0
    delta = 0.005 * (1.0 - (phi2 - 25.0) / 20.0) * qp / PA
    Ir = Es / (2.0 * (1.0 + mu) * qp * math.tan(p2))
    Irr = Ir / (1.0 + Ir * delta)
    add("compute", "Vesic: reduced rigidity index", "method:Vesic",
        tex="I_{rr} = \\tfrac{I_r}{1 + I_r\\,\\Delta}",
        sub=f"I_{{rr}} = \\tfrac{{{Ir:.1f}}}{{1 + {Ir:.1f}\\times{delta:.6f}}}",
        result={"sym": "Irr", "value": Irr, "unit": "",
                "display": f"Irr = {display_round(Irr)}"},
        narration="Vesic ties the point capacity to how rigid the soil is "
                  "relative to its strength; the volumetric strain reduces "
                  "that rigidity.",
        viz=[{"op": "highlight", "target": "tip"}])
    n_sig = (3.0 / (3.0 - math.sin(p2))
             * math.exp((math.pi / 2.0 - p2) * math.tan(p2))
             * math.tan(math.pi / 4.0 + p2 / 2.0) ** 2
             * Irr ** (4.0 * math.sin(p2) / (3.0 * (1.0 + math.sin(p2)))))
    sig_m_val = sig_m
    Qp_v = Ap * sig_m_val * n_sig
    add("compute", "Vesic: Nσ* and the point load", "method:Vesic",
        tex="Q_p = A_p\\,\\overline{\\sigma}'_m N_\\sigma^*",
        sub=(f"Q_p = ({Ap:.4g})({display_round(sig_m_val):g})"
             f"({n_sig:.0f})"),
        result={"sym": "Qp", "value": Qp_v, "unit": "kN",
                "display": f"Qp = {display_round(Qp_v):g} kN"},
        provenance=[{"symbol": "Nσ*", "value": round(n_sig),
                     "means": "Vesic's point bearing factor on the mean "
                              "effective stress",
                     "source": "Vesic's (1977) closed form evaluated at the "
                               "reduced rigidity index",
                     "arguments": [f"φ' = {phi2:g}°", f"Irr = {Irr:.1f}"],
                     "whyApplies": "computed, not read from a chart, so it "
                                   "carries no reading tolerance"}],
        viz=[{"op": "highlight", "target": "point_arrows"}])
    results.append({"method": "Vesic", "label": "Vesic (1977) rigidity "
                    "method", "q_ult": Qp_v})

    add("conclude", "Compare the three estimates", "results",
        narration="Three respected methods, three answers: the spread is "
                  "the honest uncertainty of pile design, which is why "
                  "load tests matter.",
        viz=[{"op": "compare", "methods": [
            {"method": r["method"], "q_ult": display_round(r["q_ult"])}
            for r in results]}])

    return {
        "results": [{"method": r["method"], "label": r["label"],
                     "q_ult": display_round(r["q_ult"])} for r in results],
        "conclusions": [{"quantity": "Q_p",
                         "value": display_round(min(r["q_ult"]
                                                    for r in results)),
                         "unit": "kN", "governing": "most conservative"}],
        "comparison": None,
        "figure": _fig(frame, givens, L, D, "point"),
    }


# ---------------------------------------------------------------------------
# side resistance
# ---------------------------------------------------------------------------

def _side(frame, givens, add, problem_text):
    L = givens.get("L")
    D = givens.get("D", givens.get("B"))
    phi, gamma = givens.get("phi"), givens.get("gamma")
    if None in (L, D, phi, gamma):
        return {"error": "The side-resistance check needs L, D, phi and "
                         "gamma of the shaft soil."}
    if D > 3.0:
        D = D / 1000.0
    p = 4.0 * D
    K = givens.get("delta") and None  # placeholder, K comes from text or 1.3
    mK = re.search(r"K\s*=\s*([\d.]+)", problem_text)
    K = float(mK.group(1)) if mK else 1.3
    delta = 0.8 * phi

    Lc = 15.0 * D
    add("compute", "Critical depth L'", "setup",
        tex="L' = 15D",
        sub=f"L' = 15 \\times {D:g}",
        result={"sym": "Lc", "value": Lc, "unit": "m",
                "display": f"L' = {display_round(Lc, 3)} m"},
        narration="Measured skin friction stops growing below about "
                  "fifteen pile widths; the effective stress in the "
                  "friction formula is frozen there.",
        viz=[{"op": "highlight", "target": "critical"}])

    sig_c = gamma * Lc
    f_c = K * sig_c * math.tan(math.radians(delta))
    add("compute", "Unit friction at the critical depth", "setup",
        tex="f = K\\sigma'_o\\tan\\delta'",
        sub=(f"f = ({K:g})({display_round(sig_c):g})"
             f"\\tan({delta:g}^\\circ)"),
        result={"sym": "f_c", "value": f_c, "unit": "kPa",
                "display": f"f = {display_round(f_c)} kPa"},
        viz=[{"op": "highlight", "target": "shaft"}])

    Qs1 = 0.5 * f_c * p * Lc + f_c * p * (L - Lc)
    add("compute", "Sum the triangular and constant zones", "results",
        tex="Q_s = \\tfrac{f}{2}\\,pL' + f\\,p(L - L')",
        sub=(f"Q_s = \\tfrac{{{display_round(f_c)}}}{{2}}({p:.3g})"
             f"({Lc:g}) + {display_round(f_c)}({p:.3g})({L:g}-{Lc:g})"),
        result={"sym": "Qs", "value": Qs1, "unit": "kN",
                "display": f"Qs = {display_round(Qs1):g} kN"},
        viz=[{"op": "highlight", "target": "shaft_arrows"}])

    ld = L / D
    K_cc = _cc_k(phi, ld)
    sig_avg = gamma * L / 2.0
    Qs2 = K_cc * sig_avg * math.tan(math.radians(delta)) * p * L
    add("compute", "Coyle & Castello: side resistance", "results",
        tex="Q_s = K\\,\\overline{\\sigma}'_o \\tan(0.8\\phi')\\,pL",
        sub=(f"Q_s = ({K_cc:.2f})({display_round(sig_avg):g})"
             f"\\tan({delta:g}^\\circ)({p:.3g})({L:g})"),
        result={"sym": "Qs", "value": Qs2, "unit": "kN",
                "display": f"Qs = {display_round(Qs2):g} kN"},
        provenance=[{"symbol": "K", "value": round(K_cc, 2),
                     "means": "lateral earth pressure coefficient "
                              "back-figured from pile load tests",
                     "source": "the Coyle and Castello (1981) chart, Das "
                               "Fig. 11.17, digitized from the book's vector "
                               "graphics; chart reading carries "
                               "a real tolerance",
                     "arguments": [f"φ' = {phi:g}°", f"L/D = {ld:.1f}"],
                     "whyApplies": "empirical alternative to assuming K"}],
        viz=[{"op": "highlight", "target": "shaft_arrows"}])

    add("conclude", "Compare the two estimates", "results",
        narration="The classical effective-stress sum and the load-test "
                  "chart disagree by more than a factor of two, a healthy "
                  "reminder that skin friction is the least certain part "
                  "of pile design.",
        viz=[{"op": "compare", "methods": [
            {"method": "K given", "q_ult": display_round(Qs1)},
            {"method": "Coyle-Castello", "q_ult": display_round(Qs2)}]}])

    return {
        "results": [
            {"method": "K given", "label": "effective-stress method with "
             "the critical depth", "q_ult": display_round(Qs1)},
            {"method": "Coyle-Castello",
             "label": "Coyle and Castello (1981)",
             "q_ult": display_round(Qs2)}],
        "conclusions": [{"quantity": "Q_s", "value": display_round(Qs1),
                         "unit": "kN", "governing": "effective-stress method"}],
        "comparison": None,
        "figure": _fig(frame, givens, L, D, "side"),
    }


# ---------------------------------------------------------------------------
# elastic settlement
# ---------------------------------------------------------------------------

def _settlement(frame, givens, add):
    L = givens.get("L")
    D = givens.get("D", givens.get("B"))
    Qwp, Qws = givens.get("Qwp"), givens.get("Qws")
    Ep, Es, mu = givens.get("Ep"), givens.get("Es"), givens.get("mu_s")
    missing = [n for n, v in (("L", L), ("D", D), ("Qwp", Qwp),
                              ("Qws", Qws), ("Ep", Ep), ("Es", Es))
               if v is None]
    if missing:
        return {"error": "The settlement check needs "
                         + ", ".join(missing) + "."}
    if mu is None:
        mu = 0.38
        add("assume", "Soil Poisson ratio", "setup", tex="\\mu_s = 0.38",
            augmented=True)
    Ap = D * D
    p = 4.0 * D
    xi = 0.57
    Iwp = 0.85

    se1 = (Qwp + xi * Qws) * L / (Ap * Ep)
    add("compute", "Elastic shortening of the pile itself", "setup",
        tex="S_{e(1)} = \\tfrac{(Q_{wp} + \\xi Q_{ws})L}{A_p E_p}",
        sub=(f"S = \\tfrac{{({Qwp:g} + 0.57\\times{Qws:g})({L:g})}}"
             f"{{({Ap:.4g})({Ep:g})}}"),
        result={"sym": "se1", "value": se1 * 1000, "unit": "mm",
                "display": f"{display_round(se1 * 1000, 3)} mm"},
        provenance=[{"symbol": "ξ", "value": 0.57,
                     "means": "how much of the shaft load compresses the "
                              "pile on average",
                     "source": "Vesic's recommendation, sitting between the "
                               "uniform and parabolic friction distributions",
                     "arguments": ["friction distribution along the shaft"],
                     "whyApplies": "the shaft load builds up gradually, so "
                                   "only part of it shortens the pile"}],
        viz=[{"op": "highlight", "target": "shaft"}])

    se2 = Qwp * D / (Ap * Es) * (1.0 - mu * mu) * Iwp
    add("compute", "Settlement from the load at the tip", "setup",
        tex="S_{e(2)} = \\tfrac{Q_{wp} D}{A_p E_s}(1-\\mu_s^2)I_{wp}",
        sub=(f"S = \\tfrac{{({Qwp:g})({D:g})}}{{({Ap:.4g})({Es:g})}}"
             f"(1-{mu:g}^2)(0.85)"),
        result={"sym": "se2", "value": se2 * 1000, "unit": "mm",
                "display": f"{display_round(se2 * 1000, 3)} mm"},
        viz=[{"op": "highlight", "target": "tip"}])

    Iws = 2.0 + 0.35 * math.sqrt(L / D)
    se3 = Qws * D / (p * L * Es) * (1.0 - mu * mu) * Iws
    add("compute", "Settlement from the shaft load", "setup",
        tex="S_{e(3)} = \\tfrac{Q_{ws} D}{pLE_s}(1-\\mu_s^2)I_{ws},\\quad "
            "I_{ws} = 2 + 0.35\\sqrt{L/D}",
        sub=f"I_{{ws}} = {Iws:.2f}",
        result={"sym": "se3", "value": se3 * 1000, "unit": "mm",
                "display": f"{display_round(se3 * 1000, 3)} mm"},
        narration="The shaft load spreads over the whole embedded surface, "
                  "which is why its contribution is tiny compared with the "
                  "concentrated tip load.",
        viz=[{"op": "highlight", "target": "shaft_arrows"}])

    se = se1 + se2 + se3
    add("conclude", "Total elastic settlement", "results",
        tex=(f"S_e = {display_round(se1*1000, 3)} + "
             f"{display_round(se2*1000, 3)} + {display_round(se3*1000, 3)}"
             f" = {display_round(se*1000, 4)}\\ \\text{{mm}}"),
        viz=[{"op": "compare", "methods": [
            {"method": "Pile axial", "q_ult": display_round(se1 * 1000, 3)},
            {"method": "Tip load", "q_ult": display_round(se2 * 1000, 3)},
            {"method": "Shaft load", "q_ult": display_round(se3 * 1000, 3)}]}])

    return {
        "results": [],
        "conclusions": [{"quantity": "S_e",
                         "value": display_round(se * 1000, 4),
                         "unit": "mm", "governing": "elastic settlement"}],
        "comparison": None,
        "figure": _fig(frame, givens, L, D, "settlement"),
    }


def _fig(frame, givens, L, D, mode):
    return {
        "template": "pile",
        "L": L, "D": D, "mode": mode,
        "gamma": givens.get("gamma"), "phi": givens.get("phi"),
        "phi2": givens.get("phi2"),
        "Lc": 15.0 * D if mode == "side" else None,
        "two_layers": givens.get("phi2") is not None
                      and givens.get("phi2") != givens.get("phi"),
    }
