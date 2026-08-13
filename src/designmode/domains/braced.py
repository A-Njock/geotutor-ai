"""Braced cut: Peck apparent-pressure envelope and strut loads.

Sand: sigma_a = 0.65 gamma H Ka (uniform). Clay with gamma H / c < 4:
sigma_a = 0.3 gamma H rising over the top quarter, then constant (else
gamma H - 4c). The wall is turned into beams with a hinge at the middle
strut, exactly as the textbook does; a symmetric strut layout uses the
textbook's symmetry argument, an unsymmetric one is solved by moments.
Parts c/d (section moduli) run when the allowable steel stress is given.
"""

import math

from ..compute import display_round


def build(frame: dict, givens: dict, add, problem_text: str) -> dict:
    H = givens.get("H")
    gamma = givens.get("gamma")
    s = givens.get("s")
    phi = givens.get("phi", 0.0)
    c = givens.get("c", givens.get("su"))
    # struts in order, as many as the problem states (two to five)
    depths = [givens.get(k) for k in ("dA", "dB", "dC", "dD", "dE")]
    depths = [d for d in depths if d is not None]
    missing = [n for n, v in (("H", H), ("gamma", gamma),
                              ("strut spacing s", s)) if v is None]
    if len(depths) < 2:
        missing.append("the strut depths (at least two, top strut first)")
    if missing:
        return {"error": "The braced-cut check needs the cut depth H, "
                         "gamma, the strut depths and the strut spacing; "
                         "missing: " + ", ".join(missing) + "."}
    if sorted(depths) != depths or \
            len({round(d, 3) for d in depths}) != len(depths):
        return {"error": "The strut depths must be distinct and in order "
                         "from the top strut down."}
    if depths[-1] >= H:
        return {"error": "Every strut must sit above the base of the cut."}
    dA, dB = depths[0], depths[1]
    dC = depths[2] if len(depths) >= 3 else None

    is_clay = (c or 0) > 0 and phi <= 0.5
    if not is_clay and phi <= 0:
        return {"error": "Either phi' (sand) or an undrained strength "
                         "(clay) is needed to build the envelope."}

    # ---- envelope ---------------------------------------------------------
    if is_clay:
        ratio = gamma * H / c
        if ratio < 4:
            sigma_a = 0.3 * gamma * H
            env_tex = "\\sigma_a = 0.3\\,\\gamma H"
            env_sub = f"\\sigma_a = 0.3({gamma:g})({H:g})"
            which = "stiff clay envelope"
        else:
            # soft-to-medium clay: gamma H - 4c, but never below Peck's
            # 0.3 gamma H floor, which governs when the stability number
            # is only just above 4
            raw = gamma * H - 4.0 * c
            floor = 0.3 * gamma * H
            if raw >= floor:
                sigma_a = raw
                env_tex = "\\sigma_a = \\gamma H - 4c"
                env_sub = f"\\sigma_a = ({gamma:g})({H:g}) - 4({c:g})"
            else:
                sigma_a = floor
                env_tex = ("\\sigma_a = \\max(\\gamma H - 4c,\\ "
                           "0.3\\,\\gamma H) = 0.3\\,\\gamma H")
                env_sub = (f"\\gamma H - 4c = {display_round(raw)} < "
                           f"0.3\\gamma H = {display_round(floor)}")
            which = "soft-to-medium clay envelope"
        add("compute", "Which envelope applies?", "setup",
            tex="\\tfrac{\\gamma H}{c} = \\tfrac{(%g)(%g)}{%g}" % (gamma, H, c),
            result={"sym": "ratio", "value": ratio, "unit": "",
                    "display": f"{display_round(ratio, 3)}"
                               + (" < 4" if ratio < 4 else " ≥ 4")},
            narration="Peck's clay envelopes split on the stability number "
                      "γH/c; it decides whether the cut behaves as soft or "
                      "stiff clay.",
            provenance=[{"symbol": "γH/c", "value": display_round(ratio, 3),
                         "means": "stability number of the cut",
                         "source": "Peck's (1969) apparent-pressure "
                                   "diagrams, built from strut-load "
                                   "measurements in real excavations",
                         "arguments": [f"γ = {gamma:g} kN/m³",
                                       f"H = {H:g} m", f"c = {c:g} kPa"],
                         "whyApplies": "selects between the soft/medium and "
                                       "stiff clay envelopes"}],
            viz=[{"op": "highlight", "target": "walls"}])
    else:
        Ka = math.tan(math.radians(45.0 - phi / 2.0)) ** 2
        add("lookup", "Active earth-pressure coefficient", "setup",
            tex="K_a = \\tan^2\\!\\left(45 - \\tfrac{\\phi'}{2}\\right)"
                f" = \\tan^2\\!\\left(45 - \\tfrac{{{phi:g}}}{{2}}\\right)",
            result={"sym": "Ka", "value": Ka, "unit": "",
                    "display": f"{display_round(Ka, 3)}"},
            provenance=[{"symbol": "Ka", "value": display_round(Ka, 3),
                         "means": "ratio of horizontal to vertical effective "
                                  "stress at active failure",
                         "source": "Rankine's active state",
                         "arguments": [f"φ' = {phi:g}°"],
                         "whyApplies": "the sand behind the flexible wall "
                                       "reaches the active state"}],
            viz=[{"op": "highlight", "target": "walls"}])
        sigma_a = 0.65 * gamma * H * Ka
        env_tex = "\\sigma_a = 0.65\\,\\gamma H K_a"
        env_sub = f"\\sigma_a = 0.65({gamma:g})({H:g})({display_round(Ka, 3)})"
        which = "sand envelope"

    add("compute", "Apparent-pressure envelope", "setup",
        tex=env_tex, sub=env_sub,
        result={"sym": "sigma_a", "value": sigma_a, "unit": "kPa",
                "display": f"{display_round(sigma_a)} kPa"},
        narration="Peck's envelope is not a real pressure distribution: it "
                  "is the envelope that reproduces the largest strut loads "
                  "measured in real cuts, which is why it is safe to design "
                  "each strut from it.",
        viz=[{"op": "highlight", "target": "envelope"}])

    # ---- loads from the envelope over a depth range -----------------------
    z_tri = 0.25 * H if is_clay else 0.0  # rising part of the clay envelope

    def load_and_moment(z0, z1, about):
        """Resultant of the envelope between z0..z1 and its moment about
        depth `about` (kN/m and kN·m/m per metre of wall)."""
        R = M = 0.0
        if z_tri > 0 and z0 < z_tri:
            a, bnd = z0, min(z1, z_tri)
            wa, wb = sigma_a * a / z_tri, sigma_a * bnd / z_tri
            R1 = 0.5 * (wa + wb) * (bnd - a)
            zc = a + (bnd - a) * (wa + 2 * wb) / (3 * (wa + wb)) \
                if (wa + wb) > 0 else (a + bnd) / 2
            R += R1
            M += R1 * abs(about - zc)
        if z1 > z_tri:
            a = max(z0, z_tri)
            R2 = sigma_a * (z1 - a)
            zc = (a + z1) / 2
            R += R2
            M += R2 * abs(about - zc)
        return R, M

    n = len(depths)
    names = ["A", "B", "C", "D", "E"][:n]
    if n != 3:
        return _n_strut_beams(add, depths, H, s, load_and_moment, names,
                              which, is_clay, sigma_a, gamma, phi, c,
                              z_tri, givens)

    # ---- top beam: surface to the hinge at strut B ------------------------
    add("explain", "Turn the wall into beams with a hinge at B", "beams",
        narration="The wall spans three struts, which makes it statically "
                  "indeterminate. Assuming a hinge at the middle strut "
                  "splits it into two simple beams that statics alone can "
                  "solve.",
        augmented=True,
        viz=[{"op": "highlight", "target": "beam_top"},
             {"op": "highlight", "target": "beam_bot"}])

    R_top, M_topB = load_and_moment(0.0, dB, dB)
    A = M_topB / (dB - dA)
    B1 = R_top - A
    add("compute", "Top beam: moments about B give A", "beams",
        tex="\\sum M_{B_1} = 0 \\Rightarrow A = "
            "\\tfrac{\\text{envelope load} \\times \\text{arm}}{d_B - d_A}",
        sub=f"A = \\tfrac{{{display_round(M_topB)}}}{{{dB:g} - {dA:g}}}",
        result={"sym": "A", "value": A, "unit": "kN/m",
                "display": f"A = {display_round(A)} kN/m"},
        narration="Taking moments about the hinge reaction eliminates it, "
                  "leaving the top strut reaction directly.",
        viz=[{"op": "highlight", "target": "beam_top"},
             {"op": "highlight", "target": "strutA"}])
    add("compute", "Top beam: vertical equilibrium gives B₁", "beams",
        tex="B_1 = \\text{envelope load} - A",
        sub=f"B_1 = {display_round(R_top)} - {display_round(A)}",
        result={"sym": "B1", "value": B1, "unit": "kN/m",
                "display": f"B₁ = {display_round(B1)} kN/m"},
        narration="What the top strut does not carry, the hinge at B must.",
        viz=[{"op": "highlight", "target": "beam_top"},
             {"op": "highlight", "target": "strutB"}])

    # ---- bottom beam ------------------------------------------------------
    symmetric = abs(dA - (H - dC)) < 1e-6 and abs((dB - dA) - (dC - dB)) < 1e-6
    R_bot, M_botB = load_and_moment(dB, H, dB)
    if symmetric and is_clay:
        C, B2 = A, B1
        add("compute", "Bottom beam by symmetry", "beams",
            tex="B_2 = B_1,\\qquad C = A",
            result={"sym": "C", "value": C, "unit": "kN/m",
                    "display": f"C = {display_round(C)} kN/m"},
            narration="The strut layout mirrors about mid-depth, so the "
                      "textbook takes the lower beam's reactions as the "
                      "mirror of the upper one's.",
            provenance=[{"symbol": "B₂, C", "value": "",
                         "means": "reactions of the lower beam",
                         "source": "the symmetry argument used in the "
                                   "course text for mirrored strut layouts",
                         "arguments": [f"struts at {dA:g}, {dB:g}, {dC:g} m "
                                       f"in a {H:g} m cut"],
                         "whyApplies": "strut depths are symmetric about "
                                       "mid-depth"}],
            viz=[{"op": "highlight", "target": "beam_bot"},
                 {"op": "highlight", "target": "strutC"}])
    else:
        C = M_botB / (dC - dB)
        B2 = R_bot - C
        add("compute", "Bottom beam: moments about B give C", "beams",
            tex="\\sum M_{B_2} = 0 \\Rightarrow C = "
                "\\tfrac{\\text{envelope load} \\times \\text{arm}}{d_C - d_B}",
            sub=f"C = \\tfrac{{{display_round(M_botB)}}}{{{dC:g} - {dB:g}}}",
            result={"sym": "C", "value": C, "unit": "kN/m",
                    "display": f"C = {display_round(C)} kN/m"},
            narration="The lower beam repeats the same trick about its own "
                      "hinge reaction.",
            viz=[{"op": "highlight", "target": "beam_bot"},
                 {"op": "highlight", "target": "strutC"}])
        add("compute", "Bottom beam: vertical equilibrium gives B₂", "beams",
            tex="B_2 = \\text{envelope load} - C",
            sub=f"B_2 = {display_round(R_bot)} - {display_round(C)}",
            result={"sym": "B2", "value": B2, "unit": "kN/m",
                    "display": f"B₂ = {display_round(B2)} kN/m"},
            viz=[{"op": "highlight", "target": "beam_bot"},
                 {"op": "highlight", "target": "strutB"}])

    # ---- strut loads ------------------------------------------------------
    PA, PB, PC = A * s, (B1 + B2) * s, C * s
    add("compute", "Strut loads", "results",
        tex=(f"P_A = ({display_round(A)})({s:g}),\\quad "
             f"P_B = ({display_round(B1)} + {display_round(B2)})({s:g}),"
             f"\\quad P_C = ({display_round(C)})({s:g})"),
        result={"sym": "PB", "value": PB, "unit": "kN",
                "display": f"PB = {display_round(PB)} kN"},
        narration="Reactions are per metre of wall; multiplying by the "
                  "horizontal strut spacing gives the force each strut "
                  "actually carries.",
        viz=[{"op": "compare", "methods": [
            {"method": "Strut A", "q_ult": display_round(PA)},
            {"method": "Strut B", "q_ult": display_round(PB)},
            {"method": "Strut C", "q_ult": display_round(PC)}]}])

    conclusions = [
        {"quantity": "P_A", "value": display_round(PA), "unit": "kN", "governing": which},
        {"quantity": "P_B", "value": display_round(PB), "unit": "kN", "governing": which},
        {"quantity": "P_C", "value": display_round(PC), "unit": "kN", "governing": which},
    ]

    # ---- sheet pile and wale section moduli (clay parts c/d) --------------
    sigma_all = givens.get("sigma_all")
    if sigma_all and is_clay and n == 3:
        x0 = B1 / sigma_a
        M_max = B1 * x0 - sigma_a * x0 * x0 / 2.0
        add("compute", "Point of zero shear and maximum moment", "results",
            tex="x = \\tfrac{B_1}{\\sigma_a};\\qquad "
                "M_{max} = B_1 x - \\tfrac{\\sigma_a x^2}{2}",
            sub=(f"x = \\tfrac{{{display_round(B1)}}}{{{display_round(sigma_a)}}}"
                 f" = {display_round(x0, 3)}\\ \\text{{m}}"),
            result={"sym": "M_max", "value": M_max, "unit": "kN-m/m",
                    "display": f"{display_round(M_max)} kN·m/m"},
            narration="The bending moment peaks where the shear passes "
                      "through zero, just below the middle strut.",
            viz=[{"op": "highlight", "target": "beam_bot"}])
        S_sp = M_max / sigma_all
        add("compute", "Sheet-pile section modulus", "results",
            tex="S = \\tfrac{M_{max}}{\\sigma_{all}}",
            sub=f"S = \\tfrac{{{display_round(M_max)}}}{{{sigma_all:g}}}",
            result={"sym": "S_sp", "value": S_sp, "unit": "m^3/m",
                    "display": f"{display_round(S_sp * 1e5, 3)}×10⁻⁵ m³/m"},
            viz=[{"op": "highlight", "target": "walls"}])
        M_wale = (B1 + B2) * s * s / 8.0
        S_w = M_wale / sigma_all
        add("compute", "Wale at level B", "results",
            tex="M_{max} = \\tfrac{(B_1 + B_2) s^2}{8};\\qquad "
                "S = \\tfrac{M_{max}}{\\sigma_{all}}",
            sub=(f"M = \\tfrac{{({display_round(B1)} + {display_round(B2)})"
                 f"({s:g})^2}}{{8}} = {display_round(M_wale)}"),
            result={"sym": "S_w", "value": S_w, "unit": "m^3",
                    "display": f"{display_round(S_w * 1e3, 3)}×10⁻³ m³"},
            narration="The wale spans between struts as a simple beam "
                      "loaded by the wall reaction at level B.",
            viz=[{"op": "highlight", "target": "strutB"}])
        conclusions.append({"quantity": "S_sheetpile",
                            "value": display_round(S_sp * 1e5, 3),
                            "unit": "×10⁻⁵ m³/m", "governing": which})
        conclusions.append({"quantity": "S_wale",
                            "value": display_round(S_w * 1e3, 3),
                            "unit": "×10⁻³ m³", "governing": which})

    return {
        "results": [],
        "conclusions": conclusions,
        "comparison": None,
        "figure": {
            "template": "braced_cut",
            "H": H, "Bcut": givens.get("B"), "dA": dA, "dB": dB, "dC": dC,
            "struts": depths,
            "envelope": "clay" if is_clay else "sand",
            "z_tri": z_tri, "sigma_a": display_round(sigma_a),
            "gamma": gamma, "phi": phi if not is_clay else None,
            "c": c if is_clay else None,
            "loads": {"A": display_round(PA), "B": display_round(PB),
                      "C": display_round(PC)},
            "loads_list": [display_round(PA), display_round(PB),
                           display_round(PC)],
        },
    }


# ---------------------------------------------------------------------------
# general strut count: hinges at every interior strut (2, 4 or 5 struts)
# ---------------------------------------------------------------------------

def _n_strut_beams(add, depths, H, s, load_and_moment, names, which,
                   is_clay, sigma_a, gamma, phi, c, z_tri, givens):
    n = len(depths)
    R = [0.0] * n

    if n == 2:
        add("explain", "One beam on two struts", "beams",
            narration="With two struts the wall is a single beam: the "
                      "cantilevers above the top strut and below the "
                      "bottom one lean on the same two supports, so "
                      "statics alone solves it.",
            augmented=True,
            viz=[{"op": "highlight", "target": "beam_top"}])
        # the pivot lies inside the loaded span, so the moment must keep
        # its sign: loads above the lower strut turn one way, loads below
        # it the other
        pieces = []
        if z_tri > 0:
            pieces.append((0.5 * sigma_a * z_tri, 2.0 * z_tri / 3.0))
        pieces.append((sigma_a * (H - z_tri), (z_tri + H) / 2.0))
        R_all = sum(p[0] for p in pieces)
        M_signed = sum(p[0] * (depths[1] - p[1]) for p in pieces)
        R[0] = M_signed / (depths[1] - depths[0])
        R[1] = R_all - R[0]
        M_about_2 = M_signed
        add("compute", "Moments about the lower strut give A", "beams",
            tex="\\sum M_B = 0 \\Rightarrow A = \\tfrac{\\text{envelope "
                "load} \\times \\text{arm}}{d_B - d_A}",
            sub=(f"A = \\tfrac{{{display_round(M_about_2)}}}"
                 f"{{{depths[1]:g} - {depths[0]:g}}}"),
            result={"sym": "A", "value": R[0], "unit": "kN/m",
                    "display": f"A = {display_round(R[0])} kN/m"},
            viz=[{"op": "highlight", "target": "strutA"}])
        add("compute", "Vertical equilibrium gives B", "beams",
            tex="B = \\text{envelope load} - A",
            sub=f"B = {display_round(R_all)} - {display_round(R[0])}",
            result={"sym": "B", "value": R[1], "unit": "kN/m",
                    "display": f"B = {display_round(R[1])} kN/m"},
            viz=[{"op": "highlight", "target": "strutB"}])
    else:
        add("explain", f"Hinges at every interior strut split the wall "
            f"into {n - 1} beams", "beams",
            narration=f"A wall on {n} struts is statically indeterminate. "
                      "The textbook device generalizes: assume a hinge at "
                      "each interior strut, so the wall becomes a chain "
                      "of simple beams, each solvable by moments alone. "
                      "Each strut then carries the reactions handed to it "
                      "by its neighbouring beams.",
            augmented=True,
            viz=[{"op": "highlight", "target": "beam_top"},
                 {"op": "highlight", "target": "beam_bot"}])

        # top beam: surface (cantilever) to the hinge at strut 2
        R_load, M1 = load_and_moment(0.0, depths[1], depths[1])
        R[0] = M1 / (depths[1] - depths[0])
        R[1] += R_load - R[0]
        add("compute", "Top beam: moments about the hinge give A", "beams",
            tex="\\sum M = 0 \\Rightarrow A = \\tfrac{\\text{load} \\times"
                " \\text{arm}}{d_B - d_A}",
            sub=(f"A = \\tfrac{{{display_round(M1)}}}{{{depths[1]:g} - "
                 f"{depths[0]:g}}} = {display_round(R[0])}"),
            result={"sym": "A", "value": R[0], "unit": "kN/m",
                    "display": f"A = {display_round(R[0])} kN/m"},
            viz=[{"op": "highlight", "target": "strutA"}])

        for i in range(1, n - 2):
            z0, z1 = depths[i], depths[i + 1]
            Rl, Ml = load_and_moment(z0, z1, z1)
            near = Ml / (z1 - z0)
            R[i] += near
            R[i + 1] += Rl - near
            add("compute", f"Beam {names[i]}{names[i + 1]}: a simple span "
                "between hinges", "beams",
                tex="R_{near} = \\tfrac{\\text{load} \\times \\text{arm}}"
                    "{\\text{span}}",
                sub=(f"R_{{{names[i]}}} += {display_round(near)},\\quad "
                     f"R_{{{names[i + 1]}}} += {display_round(Rl - near)}"),
                result={"sym": f"R{names[i]}", "value": near,
                        "unit": "kN/m",
                        "display": f"{names[i]} share = "
                                   f"{display_round(near)} kN/m"},
                viz=[{"op": "highlight", "target": "beam_bot"}])

        # bottom beam: hinge at strut n-1 to the base (cantilever below
        # the last strut)
        z0 = depths[n - 2]
        Rl, Ml = load_and_moment(z0, H, z0)
        last = Ml / (depths[n - 1] - z0)
        R[n - 1] += last
        R[n - 2] += Rl - last
        add("compute", "Bottom beam: moments about its hinge give the "
            f"last strut {names[n - 1]}", "beams",
            tex="\\sum M = 0 \\Rightarrow R_{last} = \\tfrac{\\text{load} "
                "\\times \\text{arm}}{\\text{span}}",
            sub=(f"{names[n - 1]} = \\tfrac{{{display_round(Ml)}}}"
                 f"{{{depths[n - 1]:g} - {z0:g}}} = {display_round(last)}"),
            result={"sym": names[n - 1], "value": last, "unit": "kN/m",
                    "display": f"{names[n - 1]} = {display_round(last)} "
                               "kN/m"},
            narration="The soil below the last strut hangs from it as a "
                      "cantilever, which is why the bottom strut usually "
                      "carries the biggest load.",
            viz=[{"op": "highlight", "target": "strutC"}])

    loads = [r * s for r in R]
    add("compute", "Strut loads", "results",
        tex=",\\quad ".join(
            f"P_{names[i]} = ({display_round(R[i])})({s:g})"
            for i in range(n)),
        result={"sym": f"P{names[-1]}", "value": loads[-1], "unit": "kN",
                "display": f"P{names[-1]} = "
                           f"{display_round(loads[-1])} kN"},
        narration="Reactions are per metre of wall; the horizontal strut "
                  "spacing turns them into the force each strut carries.",
        viz=[{"op": "compare", "methods": [
            {"method": f"Strut {names[i]}", "q_ult": display_round(loads[i])}
            for i in range(n)]}])

    conclusions = [
        {"quantity": f"P_{names[i]}", "value": display_round(loads[i]),
         "unit": "kN", "governing": which} for i in range(n)]

    return {
        "results": [],
        "conclusions": conclusions,
        "comparison": None,
        "figure": {
            "template": "braced_cut",
            "H": H, "Bcut": givens.get("B"),
            "dA": depths[0], "dB": depths[1],
            "dC": depths[2] if n >= 3 else None,
            "struts": depths,
            "envelope": "clay" if is_clay else "sand",
            "z_tri": z_tri, "sigma_a": display_round(sigma_a),
            "gamma": gamma, "phi": phi if not is_clay else None,
            "c": c if is_clay else None,
            "loads": {names[i]: display_round(loads[i]) for i in range(n)},
            "loads_list": [display_round(x) for x in loads],
        },
    }
