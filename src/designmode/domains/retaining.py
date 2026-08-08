"""Retaining structures: cantilever sheet pile walls in granular soil and
cantilever concrete retaining walls (Das's three stability checks).

The sheet pile follows the full textbook procedure down to the quartic in
L4, solved numerically. The concrete wall needs its geometry (x1..x5, D,
alpha) in the statement; without it the problem is rejected honestly.
"""

import math
import re

from ..compute import display_round
from .. import factors as F

GW = 9.81

_SHEET_RE = re.compile(r"sheet\s*pile", re.IGNORECASE)


def build(frame: dict, givens: dict, add, problem_text: str) -> dict:
    if _SHEET_RE.search(problem_text):
        return _sheet_pile(frame, givens, add)
    return _cantilever_wall(frame, givens, add)


# ---------------------------------------------------------------------------
# cantilever sheet pile in granular soil
# ---------------------------------------------------------------------------

def _sheet_pile(frame, givens, add):
    L1, L2 = givens.get("L1"), givens.get("L2")
    gamma = givens.get("gamma")
    gsat = givens.get("gamma_sat", gamma)
    phi = givens.get("phi")
    if None in (L1, L2, gamma, phi):
        return {"error": "The cantilever sheet pile needs L1 (above the "
                         "water table), L2 (to the dredge line), gamma, "
                         "gamma_sat and phi'."}
    gp = gsat - GW
    p = math.radians(phi)
    Ka = math.tan(math.pi / 4 - p / 2) ** 2
    Kp = math.tan(math.pi / 4 + p / 2) ** 2
    dK = Kp - Ka
    add("lookup", "Rankine coefficients Ka and Kp", "setup",
        tex=(f"K_a = \\tan^2(45 - \\tfrac{{{phi:g}}}{{2}}) = {Ka:.3f},"
             f"\\quad K_p = \\tan^2(45 + \\tfrac{{{phi:g}}}{{2}}) = {Kp:.3f}"),
        provenance=[{"symbol": "Ka, Kp", "value": f"{Ka:.3f}, {Kp:.3f}",
                     "means": "active and passive limits of the horizontal "
                              "to vertical stress ratio",
                     "source": "Rankine's states for a smooth vertical wall",
                     "arguments": [f"φ' = {phi:g}°"],
                     "whyApplies": "the flexible wall mobilizes active "
                                   "pressure behind and passive in front"}],
        viz=[{"op": "highlight", "target": "wall"}])

    s1 = gamma * L1 * Ka
    s2 = (gamma * L1 + gp * L2) * Ka
    add("compute", "Active pressure ordinates", "setup",
        tex="\\sigma'_1 = \\gamma L_1 K_a;\\quad "
            "\\sigma'_2 = (\\gamma L_1 + \\gamma' L_2)K_a",
        sub=(f"\\sigma'_1 = {display_round(s1)};\\quad "
             f"\\sigma'_2 = {display_round(s2)}"),
        result={"sym": "s2", "value": s2, "unit": "kPa",
                "display": f"σ'₂ = {display_round(s2)} kPa"},
        viz=[{"op": "highlight", "target": "active"}])

    L3 = s2 / (gp * dK)
    add("compute", "Depth of zero net pressure L3", "setup",
        tex="L_3 = \\tfrac{\\sigma'_2}{\\gamma'(K_p - K_a)}",
        sub=f"L_3 = \\tfrac{{{display_round(s2)}}}{{({gp:.2f})({dK:.3f})}}",
        result={"sym": "L3", "value": L3, "unit": "m",
                "display": f"L₃ = {display_round(L3, 4)} m"},
        narration="Below the dredge line the passive resistance in front "
                  "grows faster than the active push behind; L3 is where "
                  "they cancel.",
        viz=[{"op": "highlight", "target": "zero_point"}])

    A1 = 0.5 * s1 * L1
    A2 = s1 * L2
    A3 = 0.5 * (s2 - s1) * L2
    A4 = 0.5 * s2 * L3
    Pt = A1 + A2 + A3 + A4
    zbar = (A1 * (L3 + L2 + L1 / 3.0) + A2 * (L3 + L2 / 2.0)
            + A3 * (L3 + L2 / 3.0) + A4 * (2.0 * L3 / 3.0)) / Pt
    add("compute", "Resultant P of the active diagram and its arm", "setup",
        tex="P = \\sum A_i;\\qquad \\bar z = \\tfrac{\\sum A_i z_i}{P}",
        sub=(f"P = {display_round(Pt)}\\ \\text{{kN/m}},\\quad "
             f"\\bar z = {display_round(zbar, 3)}\\ \\text{{m}}"),
        result={"sym": "P", "value": Pt, "unit": "kN/m",
                "display": f"P = {display_round(Pt)} kN/m"},
        viz=[{"op": "highlight", "target": "active"}])

    s5 = (gamma * L1 + gp * L2) * Kp + gp * L3 * dK
    c1 = s5 / (gp * dK)
    c2 = 8.0 * Pt / (gp * dK)
    c3 = 6.0 * Pt * (2.0 * zbar * gp * dK + s5) / (gp * dK) ** 2
    c4 = Pt * (6.0 * zbar * s5 + 4.0 * Pt) / (gp * dK) ** 2
    add("compute", "Quartic coefficients A1 to A4", "setup",
        tex="L_4^4 + A_1L_4^3 - A_2L_4^2 - A_3L_4 - A_4 = 0",
        sub=(f"A_1 = {c1:.2f},\\ A_2 = {c2:.2f},\\ A_3 = {c3:.2f},\\ "
             f"A_4 = {c4:.2f}"),
        result={"sym": "sigma5", "value": s5, "unit": "kPa",
                "display": f"σ'₅ = {display_round(s5)} kPa"},
        viz=[{"op": "highlight", "target": "passive"}])

    def q(x):
        return x ** 4 + c1 * x ** 3 - c2 * x ** 2 - c3 * x - c4
    lo, hi = 0.01, max(4.0 * (L1 + L2), 40.0)
    while q(hi) < 0:
        hi *= 1.5
    for _ in range(200):
        mid = (lo + hi) / 2.0
        if q(mid) > 0:
            hi = mid
        else:
            lo = mid
    L4 = (lo + hi) / 2.0
    D = L3 + L4
    add("compute", "Solve the quartic: L4 and the embedment", "results",
        tex="D_{theory} = L_3 + L_4",
        sub=(f"L_4 = {display_round(L4, 4)}\\ \\text{{m}} \\Rightarrow "
             f"D = {display_round(L3, 4)} + {display_round(L4, 4)}"),
        result={"sym": "D", "value": D, "unit": "m",
                "display": f"D = {display_round(D, 4)} m"},
        narration="The quartic is just moment equilibrium about the pile "
                  "tip written out; its positive root is the embedment "
                  "that balances the active push.",
        viz=[{"op": "highlight", "target": "embedment"}])

    total = L1 + L2 + 1.3 * D
    add("compute", "Total sheet pile length with the 30 percent margin",
        "results",
        tex="L_{total} = L_1 + L_2 + 1.3\\,D_{theory}",
        sub=f"L = {L1:g} + {L2:g} + 1.3({display_round(D, 4)})",
        result={"sym": "Ltot", "value": total, "unit": "m",
                "display": f"{display_round(total, 4)} m"},
        viz=[{"op": "highlight", "target": "wall"}])

    zp = math.sqrt(2.0 * Pt / (gp * dK))
    Mmax = Pt * (zbar + zp) - 0.5 * gp * zp * zp * dK * zp / 3.0
    add("compute", "Maximum bending moment", "results",
        tex="z' = \\sqrt{\\tfrac{2P}{\\gamma'(K_p-K_a)}};\\quad "
            "M_{max} = P(\\bar z + z') - "
            "\\tfrac{\\gamma' z'^2(K_p-K_a)}{2}\\tfrac{z'}{3}",
        sub=f"z' = {display_round(zp, 3)}\\ \\text{{m}}",
        result={"sym": "Mmax", "value": Mmax, "unit": "kN-m/m",
                "display": f"Mmax = {display_round(Mmax)} kN·m/m"},
        narration="The moment peaks where the shear crosses zero, a depth "
                  "z' below the point of zero net pressure.",
        viz=[{"op": "highlight", "target": "zero_point"}])

    return {
        "results": [],
        "conclusions": [
            {"quantity": "D_theory", "value": display_round(D, 4),
             "unit": "m", "governing": "cantilever sheet pile"},
            {"quantity": "L_total", "value": display_round(total, 4),
             "unit": "m", "governing": "with the 1.3 factor"},
            {"quantity": "M_max", "value": display_round(Mmax),
             "unit": "kN·m/m", "governing": "at zero shear"}],
        "comparison": None,
        "figure": {"template": "sheet_pile", "L1": L1, "L2": L2,
                   "D": round(D, 2), "L3": round(L3, 2),
                   "gamma": gamma, "phi": phi,
                   "sigma2": display_round(s2)},
    }


# ---------------------------------------------------------------------------
# cantilever concrete retaining wall (Das Example 13.1 chain)
# ---------------------------------------------------------------------------

def _cantilever_wall(frame, givens, add):
    need = ["H", "x1", "x2", "x3", "x4", "x5", "gamma", "phi",
            "gamma2", "phi2", "c2", "gamma_c"]
    missing = [k for k in need if givens.get(k) is None]
    if missing:
        return {"error": "The cantilever wall check needs the full wall "
                         "geometry and both soils (missing: "
                         + ", ".join(missing) + "). Include the stem, toe, "
                         "heel and base dimensions in the statement."}
    H = givens["H"]; x1 = givens["x1"]; x2 = givens["x2"]
    x3 = givens["x3"]; x4 = givens["x4"]; x5 = givens["x5"]
    D = givens.get("Df", givens.get("D", 0.0))
    alpha = givens.get("alpha", 0.0)
    g1, p1 = givens["gamma"], givens["phi"]
    g2, p2d, c2 = givens["gamma2"], givens["phi2"], givens["c2"]
    gc = givens["gamma_c"]
    B = x2 + x3 + x4
    a = math.radians(alpha)
    p2 = math.radians(p2d)

    H1 = x4 * math.tan(a)
    Hp = H1 + H + x5
    add("compute", "Height of the vertical soil plane", "setup",
        tex="H' = x_4\\tan\\alpha + H + x_5",
        sub=f"H' = {x4:g}\\tan {alpha:g}^\\circ + {H:g} + {x5:g}",
        result={"sym": "Hp", "value": Hp, "unit": "m",
                "display": f"H' = {display_round(Hp, 4)} m"},
        narration="Rankine's pressure is taken on the vertical plane "
                  "through the heel, so its height runs from the base to "
                  "where the sloping backfill meets that plane.",
        viz=[{"op": "highlight", "target": "virtual_plane"}])

    Ka = F.rankine_Ka(p1, alpha)
    Pa = 0.5 * g1 * Hp * Hp * Ka
    Pv = Pa * math.sin(a)
    Ph = Pa * math.cos(a)
    add("compute", "Rankine active force and its components", "setup",
        tex="P_a = \\tfrac{1}{2}\\gamma_1 H'^2 K_a",
        sub=(f"P_a = \\tfrac{{1}}{{2}}({g1:g})({display_round(Hp, 4)})^2"
             f"({Ka:.4f}) = {display_round(Pa)}"),
        result={"sym": "Pa", "value": Pa, "unit": "kN/m",
                "display": f"Pa = {display_round(Pa)} kN/m"},
        provenance=[{"symbol": "Ka", "value": round(Ka, 4),
                     "means": "active coefficient for a backfill sloping "
                              "at alpha",
                     "source": "Rankine's solution with the sloping ground "
                               "surface",
                     "arguments": [f"φ'₁ = {p1:g}°", f"α = {alpha:g}°"],
                     "whyApplies": "the wall can yield enough for the "
                                   "backfill to reach the active state"}],
        viz=[{"op": "highlight", "target": "active"}])

    Mo = Ph * Hp / 3.0
    add("compute", "Overturning moment about the toe", "setup",
        tex="M_o = P_h\\,\\tfrac{H'}{3}",
        sub=f"M_o = {display_round(Ph)}\\times{display_round(Hp/3, 4)}",
        result={"sym": "Mo", "value": Mo, "unit": "kN-m/m",
                "display": f"Mo = {display_round(Mo)} kN·m/m"},
        viz=[{"op": "highlight", "target": "toe"}])

    # weights and arms about the toe
    sections = [
        ("stem rectangle", x1 * H * gc, x3 + (x2 - x1) + x1 / 2.0),
        ("stem taper", 0.5 * (x2 - x1) * H * gc, x3 + 2.0 * (x2 - x1) / 3.0),
        ("base slab", B * x5 * gc, B / 2.0),
        ("soil on the heel", x4 * H * g1, x3 + x2 + x4 / 2.0),
        ("backfill slope wedge", 0.5 * x4 * H1 * g1, x3 + x2 + 2.0 * x4 / 3.0),
        ("vertical component of Pa", Pv, B),
    ]
    V = sum(wgt for _, wgt, _ in sections)
    MR = sum(wgt * arm for _, wgt, arm in sections)
    add("compute", "Weights and resisting moments about the toe", "setup",
        tex="\\Sigma V,\\ \\Sigma M_R \\text{ from the six sections}",
        sub=(f"\\Sigma V = {display_round(V)}\\ \\text{{kN/m}},\\quad "
             f"\\Sigma M_R = {display_round(MR)}\\ \\text{{kN·m/m}}"),
        result={"sym": "V", "value": V, "unit": "kN/m",
                "display": f"ΣV = {display_round(V)} kN/m"},
        narration="Everything standing on the base resists: the concrete "
                  "stem and slab, the soil block over the heel, the slope "
                  "wedge above it, and the vertical part of the thrust.",
        viz=[{"op": "highlight", "target": "sections"}])

    FSo = MR / Mo
    add("compute", "Factor of safety against overturning", "results",
        tex="FS_{ot} = \\tfrac{\\Sigma M_R}{M_o}",
        sub=f"FS = \\tfrac{{{display_round(MR)}}}{{{display_round(Mo)}}}",
        result={"sym": "FSo", "value": FSo, "unit": "",
                "display": f"FS = {display_round(FSo, 3)}"},
        viz=[{"op": "highlight", "target": "toe"}])

    FSs = (V * math.tan(2.0 * p2 / 3.0) + B * (2.0 / 3.0) * c2) / Ph
    add("compute", "Factor of safety against sliding", "results",
        tex="FS_{sl} = \\tfrac{\\Sigma V\\tan(\\tfrac{2}{3}\\phi'_2) + "
            "\\tfrac{2}{3}B c'_2 + P_p}{P_h}",
        sub=(f"FS = \\tfrac{{({display_round(V)})\\tan("
             f"{2*p2d/3:.2f}^\\circ) + ({B:g})(2/3)({c2:g}) + 0}}"
             f"{{{display_round(Ph)}}}"),
        result={"sym": "FSs", "value": FSs, "unit": "",
                "display": f"FS = {display_round(FSs, 3)}"},
        narration="Passive resistance in front is conservatively ignored, "
                  "as the problem instructs.",
        viz=[{"op": "highlight", "target": "base"}])

    e = B / 2.0 - (MR - Mo) / V
    qmax = V / B * (1.0 + 6.0 * e / B)
    add("compute", "Eccentricity and the toe pressure", "results",
        tex="e = \\tfrac{B}{2} - \\tfrac{\\Sigma M_R - M_o}{\\Sigma V};"
            "\\quad q_{toe} = \\tfrac{\\Sigma V}{B}(1 + \\tfrac{6e}{B})",
        sub=(f"e = {display_round(e, 3)}\\ \\text{{m}} < B/6 = "
             f"{B/6:.3f}\\ \\text{{m}}"),
        result={"sym": "qmax", "value": qmax, "unit": "kPa",
                "display": f"q toe = {display_round(qmax)} kPa"},
        viz=[{"op": "highlight", "target": "base"}])

    Nq = F.vesic_Nq(p2d); Nc = F.vesic_Nc(p2d); Ng = F.vesic_Ngamma(p2d)
    Bp = B - 2.0 * e
    qs = g2 * D
    k = D / B
    Fqd = 1.0 + 2.0 * math.tan(p2) * (1.0 - math.sin(p2)) ** 2 * k
    Fcd = Fqd - (1.0 - Fqd) / (Nc * math.tan(p2)) if p2 > 0 else 1.0 + 0.4 * k
    psi = math.degrees(math.atan(Ph / V))
    Fci = Fqi = (1.0 - psi / 90.0) ** 2
    Fgi = (1.0 - psi / p2d) ** 2 if psi < p2d else 0.0
    qu = (c2 * Nc * Fcd * Fci + qs * Nq * Fqd * Fqi
          + 0.5 * g2 * Bp * Ng * 1.0 * Fgi)
    FSb = qu / qmax
    add("compute", "Bearing capacity of the base and its FS", "results",
        tex="q_u = c'_2N_cF_{cd}F_{ci} + qN_qF_{qd}F_{qi} + "
            "\\tfrac{1}{2}\\gamma_2 B'N_\\gamma F_{\\gamma i}",
        sub=(f"q_u = {display_round(qu)}\\ \\text{{kPa}};\\quad "
             f"FS = \\tfrac{{{display_round(qu)}}}{{{display_round(qmax)}}}"),
        result={"sym": "FSb", "value": FSb, "unit": "",
                "display": f"FS = {display_round(FSb, 3)}"},
        provenance=[{"symbol": "Nc, Nq, Nγ", "value": f"{Nc:.2f}, {Nq:.2f}, {Ng:.2f}",
                     "means": "general bearing capacity factors of the "
                              "foundation soil",
                     "source": "the standard closed forms (Prandtl, "
                               "Reissner, Vesic)",
                     "arguments": [f"φ'₂ = {p2d:g}°"],
                     "whyApplies": "the base acts as an eccentric, "
                                   "inclined-loaded strip footing"}],
        viz=[{"op": "highlight", "target": "base"}])

    add("conclude", "The three checks together", "results",
        tex=(f"FS_{{ot}} = {display_round(FSo, 3)},\\quad "
             f"FS_{{sl}} = {display_round(FSs, 3)},\\quad "
             f"FS_{{bc}} = {display_round(FSb, 3)}"),
        viz=[{"op": "compare", "methods": [
            {"method": "Overturning", "q_ult": display_round(FSo, 3)},
            {"method": "Sliding", "q_ult": display_round(FSs, 3)},
            {"method": "Bearing", "q_ult": display_round(FSb, 3)}]}])

    return {
        "results": [],
        "conclusions": [
            {"quantity": "FS_overturning", "value": display_round(FSo, 3),
             "unit": "", "governing": "vs 2 required"},
            {"quantity": "FS_sliding", "value": display_round(FSs, 3),
             "unit": "", "governing": "vs 1.5 required"},
            {"quantity": "FS_bearing", "value": display_round(FSb, 3),
             "unit": "", "governing": "vs 3 required"}],
        "comparison": None,
        "figure": {"template": "cantilever_wall", "H": H, "x1": x1,
                   "x2": x2, "x3": x3, "x4": x4, "x5": x5, "D": D,
                   "alpha": alpha, "gamma": g1, "phi": p1,
                   "gamma2": g2, "phi2": p2d, "c2": c2},
    }
