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
_PASSIVE_RE = re.compile(r"passive", re.IGNORECASE)


def build(frame: dict, givens: dict, add, problem_text: str) -> dict:
    if _SHEET_RE.search(problem_text):
        return _sheet_pile(frame, givens, add)
    # full cantilever geometry present -> Das's three stability checks;
    # otherwise a wall with just height and soil is a lateral-thrust ask
    geometry = all(givens.get(k) is not None
                   for k in ("x1", "x2", "x3", "x4", "x5"))
    if not geometry and givens.get("H") is not None \
            and givens.get("gamma") is not None:
        return _lateral_thrust(frame, givens, add, problem_text)
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
# Coulomb wedge: wall friction delta, battered back, sloping backfill
# ---------------------------------------------------------------------------

def _coulomb_thrust(add, H, gamma, phi, delta, theta_wall, alpha, q):
    face = 90.0 - theta_wall  # wall face angle from horizontal
    Ka = F.coulomb_Ka(phi, delta, alpha, face)
    add("lookup", "Coulomb's active coefficient for the real wall", "setup",
        tex=f"K_a = {Ka:.4f}",
        provenance=[{"symbol": "Ka", "value": round(Ka, 4),
                     "means": "active coefficient from the sliding wedge "
                              "between the wall back and the trial plane",
                     "source": "Coulomb (1776) wedge theory, the standard "
                               "closed form",
                     "arguments": [f"φ = {phi:g}°", f"δ = {delta:g}°",
                                   f"backfill slope α = {alpha:g}°",
                                   f"wall back {theta_wall:g}° from "
                                   "vertical"],
                     "whyApplies": "wall friction and a battered back "
                                   "are outside Rankine's assumptions; "
                                   "Coulomb's wedge handles both"}],
        viz=[{"op": "highlight", "target": "wall"}])
    P = 0.5 * gamma * H * H * Ka + q * H * Ka
    add("compute", "Active thrust on the wall", "results",
        tex="P_a = \\tfrac{1}{2}\\gamma H^2 K_a" + (" + qHK_a" if q else ""),
        sub=(f"P_a = \\tfrac{{1}}{{2}}({gamma:g})({H:g})^2({Ka:.4f})"
             + (f" + ({q:g})({H:g})({Ka:.4f})" if q else "")),
        result={"sym": "P_a", "value": P, "unit": "kN/m",
                "display": f"Pa = {display_round(P)} kN/m"},
        narration="The thrust acts at the wall friction angle delta from "
                  "the normal to the wall back, not horizontally.",
        viz=[{"op": "highlight", "target": "resultant"}])
    # inclination of P to the horizontal: delta measured from the normal
    # to the wall back, the back itself tilted theta_wall from vertical
    incl = math.radians(delta + theta_wall)
    Ph = P * math.cos(incl)
    Pv = P * math.sin(incl)
    add("compute", "Horizontal and vertical components", "results",
        tex="P_h = P_a\\cos(\\delta+\\theta);\\quad "
            "P_v = P_a\\sin(\\delta+\\theta)",
        sub=(f"P_h = {display_round(Ph)};\\quad "
             f"P_v = {display_round(Pv)}"),
        result={"sym": "P_h", "value": Ph, "unit": "kN/m",
                "display": f"Ph = {display_round(Ph)} kN/m"},
        viz=[{"op": "highlight", "target": "resultant"}])
    return {
        "results": [],
        "conclusions": [
            {"quantity": "P_a", "value": display_round(P), "unit": "kN/m",
             "governing": "Coulomb wedge"},
            {"quantity": "P_ah", "value": display_round(Ph),
             "unit": "kN/m", "governing": "horizontal component"},
            {"quantity": "P_av", "value": display_round(Pv),
             "unit": "kN/m", "governing": "vertical component"},
            {"quantity": "z_bar", "value": display_round(H / 3.0, 3),
             "unit": "m", "governing": "above the base"}],
        "comparison": None,
        "figure": {"template": "lateral_wall", "H": H, "Dw": None,
                   "gamma": gamma, "phi": phi, "c": 0, "alpha": alpha,
                   "q": q, "passive": False,
                   "sigma_base": display_round(gamma * H * Ka),
                   "zc": None, "P": display_round(P),
                   "zbar": display_round(H / 3.0, 3)},
    }


# ---------------------------------------------------------------------------
# lateral thrust on a wall from height and soil alone (Rankine)
# ---------------------------------------------------------------------------

def _lateral_thrust(frame, givens, add, problem_text):
    H = givens["H"]
    gamma = givens["gamma"]
    phi = givens.get("phi")
    c = givens.get("c", givens.get("su"))
    alpha = givens.get("alpha", givens.get("beta", 0.0)) or 0.0
    q = givens.get("q_applied", 0.0) or 0.0
    Dw = givens.get("Dw")
    cw = givens.get("cw")
    delta = givens.get("delta")
    theta_wall = givens.get("theta_wall", 0.0) or 0.0
    passive = bool(_PASSIVE_RE.search(problem_text))
    side = "passive" if passive else "active"

    if phi is None and c is None:
        return {"error": "The lateral thrust needs the backfill strength: "
                         "phi for a granular soil, or the undrained "
                         "strength for a clay."}
    if phi is None:
        phi = 0.0
    if c is None:
        c = 0.0

    # wall friction or a battered back: Coulomb's wedge, not Rankine
    if (delta or theta_wall) and c == 0.0 and not passive:
        return _coulomb_thrust(add, H, gamma, phi, delta or 0.0,
                               theta_wall, alpha, q)
    if c > 0 and alpha:
        return {"error": "A cohesive backfill with a sloping surface is "
                         "beyond the Rankine expressions used here; state "
                         "a level backfill or a granular soil."}
    water = Dw is not None and Dw < H
    if water and c > 0:
        return {"error": "A cohesive backfill with a water table inside "
                         "the wall height is not covered yet; state the "
                         "problem with one effect at a time."}
    if water and givens.get("gamma_sat") is None:
        return {"error": "The water table sits within the wall height, so "
                         "the saturated unit weight below it is needed."}

    p = math.radians(phi)
    if passive:
        K = F.rankine_Kp(phi, alpha)
        k_tex = (f"K_p = \\tfrac{{1+\\sin{phi:g}^\\circ}}"
                 f"{{1-\\sin{phi:g}^\\circ}} = {K:.3f}") if not alpha else \
                f"K_p({phi:g}^\\circ, \\alpha={alpha:g}^\\circ) = {K:.3f}"
        which = "passive resistance the soil can mobilize"
    else:
        K = F.rankine_Ka(phi, alpha)
        k_tex = (f"K_a = \\tfrac{{1-\\sin{phi:g}^\\circ}}"
                 f"{{1+\\sin{phi:g}^\\circ}} = {K:.3f}") if not alpha else \
                f"K_a({phi:g}^\\circ, \\alpha={alpha:g}^\\circ) = {K:.3f}"
        which = "active push the backfill applies"
    add("lookup", f"Rankine {side} earth pressure coefficient", "setup",
        tex=k_tex,
        provenance=[{"symbol": "Kp" if passive else "Ka", "value": round(K, 4),
                     "means": "limit ratio of horizontal to vertical "
                              "effective stress",
                     "source": "Rankine's states for a smooth vertical wall",
                     "arguments": [f"φ = {phi:g}°"]
                                  + ([f"α = {alpha:g}°"] if alpha else []),
                     "whyApplies": f"the wall yields enough to reach the "
                                   f"{side} limit state, so this is the "
                                   + which}],
        viz=[{"op": "highlight", "target": "wall"}])

    sq = math.sqrt(K)
    conclusions = []

    if water:
        gsat = givens["gamma_sat"]
        gp = gsat - GW
        s_top = q * K
        s_w = (q + gamma * Dw) * K
        s_base = s_w + gp * (H - Dw) * K
        u = GW * (H - Dw)
        add("compute", "Pressure ordinates above and below the water table",
            "setup",
            tex="\\sigma'_h = (q + \\gamma z)K \\text{ above};\\quad "
                "\\sigma'_h = [q + \\gamma D_w + \\gamma'(z-D_w)]K "
                "\\text{ below}",
            sub=(f"\\sigma'_{{{Dw:g}}} = {display_round(s_w)};\\quad "
                 f"\\sigma'_{{{H:g}}} = {display_round(s_base)}"),
            result={"sym": "sigma_base", "value": s_base, "unit": "kPa",
                    "display": f"σ'@base = {display_round(s_base)} kPa"},
            narration="Below the water table only the buoyant unit weight "
                      "keeps adding effective stress; the water pushes on "
                      "the wall separately.",
            viz=[{"op": "highlight", "target": "active"}])
        A_rect_q = s_top * H
        A_tri_1 = 0.5 * (s_w - s_top) * Dw
        A_rect_2 = (s_w - s_top) * (H - Dw)
        A_tri_2 = 0.5 * (s_base - s_w) * (H - Dw)
        A_water = 0.5 * u * (H - Dw)
        P = A_rect_q + A_tri_1 + A_rect_2 + A_tri_2 + A_water
        moment = (A_rect_q * H / 2.0
                  + A_tri_1 * (H - Dw + Dw / 3.0)
                  + A_rect_2 * (H - Dw) / 2.0
                  + A_tri_2 * (H - Dw) / 3.0
                  + A_water * (H - Dw) / 3.0)
        zbar = moment / P
        add("compute", "Sum the diagram areas, soil plus water", "results",
            tex="P = \\Sigma A_i;\\quad \\bar z = \\tfrac{\\Sigma A_i "
                "z_i}{P} \\text{ above the base}",
            sub=(f"P = {display_round(A_rect_q + A_tri_1 + A_rect_2 + A_tri_2)}"
                 f" + {display_round(A_water)}\\ (\\text{{water}}) = "
                 f"{display_round(P)}"),
            result={"sym": "P", "value": P, "unit": "kN/m",
                    "display": f"P = {display_round(P)} kN/m"},
            narration="The thrust is the area of the whole pressure "
                      "diagram, and the water wedge below the table is "
                      "part of it.",
            viz=[{"op": "highlight", "target": "resultant"}])
        sym = "P_p" if passive else "P_a"
        conclusions = [
            {"quantity": sym, "value": display_round(P), "unit": "kN/m",
             "governing": f"Rankine {side} with water at {Dw:g} m"},
            {"quantity": "z_bar", "value": display_round(zbar, 3),
             "unit": "m", "governing": "above the base"}]
        fig_sigma = display_round(s_base + u)
    elif c > 0:
        sign = 1.0 if passive else -1.0
        # wall adhesion deepens the cohesion term: 2 sqrt(K) grows into
        # Kc = 2 sqrt(K (1 + cw/c)) (the standard adhesion correction)
        if cw:
            Kc = 2.0 * math.sqrt(K * (1.0 + cw / c))
            add("lookup", "Cohesion coefficient with wall adhesion",
                "setup",
                tex=("K_{c} = 2\\sqrt{K\\,(1 + c_w/c)}"
                     f" = 2\\sqrt{{{K:.3f}(1 + {cw:g}/{c:g})}}"
                     f" = {Kc:.3f}"),
                provenance=[{"symbol": "Kc", "value": round(Kc, 3),
                             "means": "cohesion multiplier accounting for "
                                      "the adhesion the soil develops on "
                                      "the wall itself",
                             "source": "the standard earth pressure "
                                       "correction, 2 sqrt(K(1+cw/c))",
                             "arguments": [f"c = {c:g} kPa",
                                           f"cw = {cw:g} kPa"],
                             "whyApplies": "the wall face carries shear "
                                           "too, which relieves the "
                                           "active push and adds to the "
                                           "passive resistance"}],
                viz=[{"op": "highlight", "target": "wall"}])
        else:
            Kc = 2.0 * sq
        s_top = q * K + sign * Kc * c
        s_base = (q + gamma * H) * K + sign * Kc * c
        add("compute", f"Pressure ordinates with cohesion ({side})", "setup",
            tex=("\\sigma_h = (q + \\gamma z)K + K_c\\,c" if passive
                 else "\\sigma_h = (q + \\gamma z)K - K_c\\,c"),
            sub=(f"\\sigma_{{top}} = {display_round(s_top)};\\quad "
                 f"\\sigma_{{base}} = {display_round(s_base)}"),
            result={"sym": "sigma_base", "value": s_base, "unit": "kPa",
                    "display": f"σ@base = {display_round(s_base)} kPa"},
            narration="Cohesion shifts the whole diagram: it relieves the "
                      "active push but adds to the passive resistance.",
            viz=[{"op": "highlight", "target": "active"}])
        if passive:
            P = 0.5 * (s_top + s_base) * H
            zbar = (s_top * H * H / 2.0
                    + 0.5 * (s_base - s_top) * H * H / 3.0) / (P or 1.0)
            add("compute", "Passive thrust from the trapezoid", "results",
                tex="P_p = \\tfrac{1}{2}(\\sigma_{top} + \\sigma_{base})H",
                sub=(f"P_p = \\tfrac{{1}}{{2}}({display_round(s_top)} + "
                     f"{display_round(s_base)})({H:g})"),
                result={"sym": "P_p", "value": P, "unit": "kN/m",
                        "display": f"Pp = {display_round(P)} kN/m"},
                viz=[{"op": "highlight", "target": "resultant"}])
            conclusions = [
                {"quantity": "P_p", "value": display_round(P),
                 "unit": "kN/m", "governing": "Rankine passive with "
                                              "cohesion"},
                {"quantity": "z_bar", "value": display_round(zbar, 3),
                 "unit": "m", "governing": "above the base"}]
        else:
            zc = max(0.0, -s_top / (gamma * K)) if s_top < 0 else 0.0
            # thrust ignoring the tension zone entirely (after cracks open)
            P_crack = 0.5 * s_base * (H - zc) if s_base > 0 else 0.0
            add("compute", "Depth of the tension crack", "setup",
                tex="z_c = \\tfrac{K_c\\,c}{\\gamma K} - \\tfrac{q}"
                    "{\\gamma}",
                sub=f"z_c = {display_round(zc, 3)}\\ \\text{{m}}",
                result={"sym": "zc", "value": zc, "unit": "m",
                        "display": f"z_c = {display_round(zc, 3)} m"},
                narration="Near the surface the cohesion would put the "
                          "soil in tension, which soil cannot carry; "
                          "cracks open there instead, so that zone "
                          "contributes no push.",
                viz=[{"op": "highlight", "target": "crack"}])
            zbar = (H - zc) / 3.0
            add("compute", "Active thrust after the cracks open", "results",
                tex="P_a = \\tfrac{1}{2}\\,\\sigma_{base}\\,(H - z_c)",
                sub=(f"P_a = \\tfrac{{1}}{{2}}({display_round(s_base)})"
                     f"({H:g} - {display_round(zc, 3)})"),
                result={"sym": "P_a", "value": P_crack, "unit": "kN/m",
                        "display": f"Pa = {display_round(P_crack)} kN/m"},
                narration="Design practice keeps only the compressive "
                          "part of the diagram, the triangle below the "
                          "crack depth.",
                viz=[{"op": "highlight", "target": "resultant"}])
            P = P_crack
            conclusions = [
                {"quantity": "P_a", "value": display_round(P),
                 "unit": "kN/m", "governing": "after tension cracks"},
                {"quantity": "z_c", "value": display_round(zc, 3),
                 "unit": "m", "governing": "tension crack depth"},
                {"quantity": "z_bar", "value": display_round(zbar, 3),
                 "unit": "m", "governing": "above the base"}]
        fig_sigma = display_round(s_base)
    else:
        s_top = q * K
        s_base = (q + gamma * H) * K
        add("compute", "Pressure at the top and bottom of the wall", "setup",
            tex="\\sigma_h = (q + \\gamma z)K",
            sub=(f"\\sigma_{{top}} = {display_round(s_top)};\\quad "
                 f"\\sigma_{{base}} = ({q:g} + {gamma:g}\\times{H:g})"
                 f"({K:.3f}) = {display_round(s_base)}"),
            result={"sym": "sigma_base", "value": s_base, "unit": "kPa",
                    "display": f"σ@base = {display_round(s_base)} kPa"},
            narration="The horizontal pressure grows linearly with depth, "
                      "a triangle when there is no surcharge.",
            viz=[{"op": "highlight", "target": "active"}])
        A_rect = s_top * H
        A_tri = 0.5 * (s_base - s_top) * H
        P = A_rect + A_tri
        zbar = ((A_rect * H / 2.0 + A_tri * H / 3.0) / P) if P else H / 3.0
        sym = "P_p" if passive else "P_a"
        sub = (f"P = {display_round(A_tri)}"
               if not q else
               f"P = {display_round(A_rect)} + {display_round(A_tri)}")
        add("compute", f"Thrust and its point of application", "results",
            tex=("P = \\tfrac{1}{2}\\gamma H^2 K + qHK;\\quad "
                 "\\bar z = \\tfrac{\\Sigma A_i z_i}{P}" if q else
                 "P = \\tfrac{1}{2}\\gamma H^2 K;\\quad "
                 "\\bar z = \\tfrac{H}{3}"),
            sub=sub + f" = {display_round(P)}",
            result={"sym": sym, "value": P, "unit": "kN/m",
                    "display": f"{'Pp' if passive else 'Pa'} = "
                               f"{display_round(P)} kN/m"},
            narration="The thrust is the area of the pressure diagram and "
                      "acts through its centroid.",
            viz=[{"op": "highlight", "target": "resultant"}])
        conclusions = [
            {"quantity": sym, "value": display_round(P), "unit": "kN/m",
             "governing": f"Rankine {side}"},
            {"quantity": "z_bar", "value": display_round(zbar, 3),
             "unit": "m", "governing": "above the base"}]
        if alpha:
            a_r = math.radians(alpha)
            Ph = P * math.cos(a_r)
            Pv = P * math.sin(a_r)
            add("compute", "Components of the inclined resultant",
                "results",
                tex="P_h = P\\cos\\alpha;\\quad P_v = P\\sin\\alpha",
                sub=(f"P_h = {display_round(Ph)};\\quad "
                     f"P_v = {display_round(Pv)}"),
                result={"sym": "P_h", "value": Ph, "unit": "kN/m",
                        "display": f"Ph = {display_round(Ph)} kN/m"},
                narration="With a sloping backfill Rankine's resultant "
                          "acts parallel to the ground surface, so it "
                          "carries both a horizontal push and a vertical "
                          "drag on the wall.",
                viz=[{"op": "highlight", "target": "resultant"}])
            conclusions += [
                {"quantity": "P_ah", "value": display_round(Ph),
                 "unit": "kN/m", "governing": "horizontal component"},
                {"quantity": "P_av", "value": display_round(Pv),
                 "unit": "kN/m", "governing": "vertical component"}]
        fig_sigma = display_round(s_base)

    return {
        "results": [],
        "conclusions": conclusions,
        "comparison": None,
        "figure": {"template": "lateral_wall", "H": H, "Dw": Dw if water
                   else None, "gamma": gamma, "phi": phi, "c": c,
                   "alpha": alpha, "q": q, "passive": passive,
                   "sigma_base": fig_sigma,
                   "zc": display_round(zc, 3)
                         if (c > 0 and not passive and not water) else None,
                   "P": display_round(P),
                   "zbar": display_round(zbar, 3)},
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
