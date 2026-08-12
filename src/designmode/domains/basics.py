"""Phase relations from a sample's weight, volume and moisture data.

Mirrors the canonical chain (Das, ch. 3): moist unit weight, dry unit
weight, void ratio, porosity, degree of saturation, volume of water.
"""

import math
import re

from ..compute import display_round

GAMMA_W = 9.81  # kN/m^3
RHO_W = 1.0     # Mg/m^3

# raw laboratory measurements that route through the _from_lab pre-chain
LAB_KEYS = (
    "m_tin", "m_wet_tot", "m_dry_tot", "m_wet", "m_dry",
    "D_s", "L_s", "rho_bulk", "rho_dry", "m_wax", "rho_wax",
    "e_max", "e_min",
)

_DENSITY_ASK = re.compile(
    r"density|kg/m(?:\^?3|³)|Mg/m(?:\^?3|³)|g/cm(?:\^?3|³)",
    re.IGNORECASE)


def build(frame: dict, givens: dict, add, problem_text: str) -> dict:
    # raw lab measurements first: they get derived into V, W, w and then
    # flow into the standard chains below
    if any(givens.get(k) is not None for k in LAB_KEYS):
        return _from_lab(frame, givens, add, problem_text)
    V = givens.get("V")
    W = givens.get("W")
    w = givens.get("w")
    Gs = givens.get("Gs")
    # no weights, but the dimensionless triple: e with Gs and (S or w)
    if (V is None or W is None) and givens.get("e_void") is not None \
            and Gs is not None:
        return _from_void_ratio(frame, givens, add)
    missing = [n for n, v in (("V", V), ("W", W), ("w", w), ("Gs", Gs))
               if v is None]
    if missing:
        return {"error": "Phase relations need the sample volume, weight, "
                         "moisture content and Gs; missing: "
                         + ", ".join(missing) + ". Alternatively give the "
                         "void ratio with Gs and the saturation or "
                         "moisture content."}
    if w > 1.0:
        w = w / 100.0
        add("assume", "Moisture content read as a percentage", "setup",
            tex=f"w = {w:g}", augmented=True,
            narration="The moisture content was given in percent and is "
                      "used as a fraction from here on.")

    return _from_sample(frame, givens, add, V, W, w, Gs)


def _from_void_ratio(frame, givens, add):
    """Unit weights straight from e, Gs and S (or w): no sample needed."""
    e = givens["e_void"]
    Gs = givens["Gs"]
    S = givens.get("S_r")
    w = givens.get("w")
    if S is None and w is None:
        return {"error": "With the void ratio and Gs, either the degree "
                         "of saturation or the moisture content is needed "
                         "to fix how much water sits in the voids."}
    if S is not None and S > 1.0:
        S = S / 100.0
        add("assume", "Saturation read as a percentage", "setup",
            tex=f"S = {S:g}", augmented=True)
    if w is not None and w > 1.0:
        w = w / 100.0
        add("assume", "Moisture content read as a percentage", "setup",
            tex=f"w = {w:g}", augmented=True)

    add("explain", "Idealize one unit volume of solids", "phases",
        narration="With no sample weights given, the cleanest picture is "
                  "a block with exactly one unit volume of solids: the "
                  "voids then occupy a volume equal to e, and every unit "
                  "weight falls out of that block.",
        augmented=True,
        viz=[{"op": "highlight", "target": "phases"}])

    if S is None:
        S = w * Gs / e
        add("compute", "Degree of saturation from the moisture content",
            "phases",
            tex="S e = w\\,G_s \\;\\Rightarrow\\; S = \\tfrac{w G_s}{e}",
            sub=f"S = \\tfrac{{({w:g})({Gs:g})}}{{{e:g}}}",
            result={"sym": "S", "value": S * 100, "unit": "%",
                    "display": f"S = {display_round(S * 100, 3)} %"},
            narration="The identity Se = wGs ties the four dimensionless "
                      "quantities together; three of them fix the fourth.",
            viz=[{"op": "highlight", "target": "water"}])
        if S > 1.000001:
            return {"error": "These values imply a degree of saturation "
                             "above 100 percent, which is not physically "
                             "possible; please check e, Gs and w."}
    elif w is None:
        w = S * e / Gs
        add("compute", "Moisture content from the saturation", "phases",
            tex="S e = w\\,G_s \\;\\Rightarrow\\; w = \\tfrac{S e}{G_s}",
            sub=f"w = \\tfrac{{({S:g})({e:g})}}{{{Gs:g}}}",
            result={"sym": "w", "value": w * 100, "unit": "%",
                    "display": f"w = {display_round(w * 100, 3)} %"},
            narration="The same identity Se = wGs, read the other way "
                      "around.",
            viz=[{"op": "highlight", "target": "water"}])

    gamma_d = Gs * GAMMA_W / (1.0 + e)
    add("compute", "Dry unit weight", "phases",
        tex="\\gamma_d = \\tfrac{G_s\\,\\gamma_w}{1+e}",
        sub=f"\\gamma_d = \\tfrac{{({Gs:g})({GAMMA_W})}}{{1+{e:g}}}",
        result={"sym": "gamma_d", "value": gamma_d, "unit": "kN/m^3",
                "display": f"{display_round(gamma_d)} kN/m³"},
        narration="Only the solids weigh anything when the soil is dry: "
                  "their weight Gs times gamma w spreads over the whole "
                  "block of volume one plus e.",
        viz=[{"op": "highlight", "target": "solids"}])

    gamma = (Gs + S * e) * GAMMA_W / (1.0 + e)
    add("compute", "Bulk (moist) unit weight", "phases",
        tex="\\gamma = \\tfrac{(G_s + S e)\\,\\gamma_w}{1+e}",
        sub=(f"\\gamma = \\tfrac{{({Gs:g} + {display_round(S, 3)}"
             f"\\times{e:g})({GAMMA_W})}}{{1+{e:g}}}"),
        result={"sym": "gamma", "value": gamma, "unit": "kN/m^3",
                "display": f"{display_round(gamma)} kN/m³"},
        narration="Adding the water that fills a fraction S of the voids "
                  "puts Se more weight on the same block.",
        viz=[{"op": "highlight", "target": "water"}])

    gamma_sat = (Gs + e) * GAMMA_W / (1.0 + e)
    add("compute", "Saturated unit weight, for reference", "phases",
        tex="\\gamma_{sat} = \\tfrac{(G_s + e)\\,\\gamma_w}{1+e}",
        sub=f"\\gamma_{{sat}} = \\tfrac{{({Gs:g} + {e:g})({GAMMA_W})}}{{1+{e:g}}}",
        result={"sym": "gamma_sat", "value": gamma_sat, "unit": "kN/m^3",
                "display": f"{display_round(gamma_sat)} kN/m³"},
        narration="If the voids ever fill completely, S becomes one and "
                  "the bulk unit weight rises to this ceiling.",
        viz=[{"op": "highlight", "target": "voids"}])

    n = e / (1.0 + e)
    add("compute", "Porosity", "phases",
        tex="n = \\tfrac{e}{1+e}",
        sub=f"n = \\tfrac{{{e:g}}}{{1+{e:g}}}",
        result={"sym": "n", "value": n, "unit": "",
                "display": f"{display_round(n, 3)}"},
        viz=[{"op": "highlight", "target": "voids"}])

    add("conclude", "The unit weights from the dimensionless triple",
        "results",
        tex=(f"\\gamma = {display_round(gamma)}\\ \\text{{kN/m}}^3,\\quad "
             f"\\gamma_d = {display_round(gamma_d)}\\ \\text{{kN/m}}^3,\\quad "
             f"\\gamma_{{sat}} = {display_round(gamma_sat)}\\ "
             f"\\text{{kN/m}}^3,\\quad w = {display_round(w * 100, 3)}\\%,"
             f"\\quad n = {display_round(n, 3)}"),
        narration="Every answer came from one unit volume of solids; no "
                  "sample weight was ever needed.",
        viz=[{"op": "highlight", "target": "phases"}])

    return {
        "results": [],
        "conclusions": [
            {"quantity": "gamma", "value": display_round(gamma),
             "unit": "kN/m³", "governing": "bulk, at the given saturation"},
            {"quantity": "gamma_d", "value": display_round(gamma_d),
             "unit": "kN/m³", "governing": "dry"},
            {"quantity": "gamma_sat", "value": display_round(gamma_sat),
             "unit": "kN/m³", "governing": "fully saturated"},
        ],
        "comparison": None,
        "figure": {
            "template": "phase_diagram",
            "Gs": Gs, "w": display_round(w, 4),
            "e": display_round(e, 3), "n": display_round(n, 3),
            "S": display_round(S * 100, 3),
            "gamma": display_round(gamma),
            "gamma_d": display_round(gamma_d),
        },
    }


def _from_sample(frame, givens, add, V, W, w, Gs):
    gamma = W / V
    add("compute", "Moist unit weight", "setup",
        tex="\\gamma = \\tfrac{W}{V}",
        sub=f"\\gamma = \\tfrac{{{W:g}}}{{{V:g}}}",
        result={"sym": "gamma", "value": gamma, "unit": "kN/m^3",
                "display": f"{display_round(gamma)} kN/m³"},
        narration="The moist unit weight is simply the sample's total "
                  "weight over its total volume.",
        viz=[{"op": "highlight", "target": "total"}])

    gamma_d = gamma / (1.0 + w)
    add("compute", "Dry unit weight", "setup",
        tex="\\gamma_d = \\tfrac{\\gamma}{1+w}",
        sub=f"\\gamma_d = \\tfrac{{{display_round(gamma)}}}{{1+{w:g}}}",
        result={"sym": "gamma_d", "value": gamma_d, "unit": "kN/m^3",
                "display": f"{display_round(gamma_d)} kN/m³"},
        narration="Removing the water weight leaves the dry unit weight; "
                  "the moisture content links the two.",
        viz=[{"op": "highlight", "target": "solids"}])

    add("explain", "Idealize the sample into three phases", "phases",
        narration="From here the sample is pictured as three stacked "
                  "blocks: solids at the bottom, water above them, air on "
                  "top. Volumes on one side, weights on the other.",
        augmented=True,
        viz=[{"op": "highlight", "target": "phases"}])

    e = Gs * GAMMA_W / gamma_d - 1.0
    add("compute", "Void ratio", "phases",
        tex="\\gamma_d = \\tfrac{G_s\\,\\gamma_w}{1+e}"
            "\\;\\Rightarrow\\; e = \\tfrac{G_s\\,\\gamma_w}{\\gamma_d} - 1",
        sub=f"e = \\tfrac{{({Gs:g})({GAMMA_W})}}{{{display_round(gamma_d)}}} - 1",
        result={"sym": "e", "value": e, "unit": "",
                "display": f"{display_round(e, 3)}"},
        narration="The dry unit weight ties the solids' weight to the total "
                  "volume, which is what exposes the void ratio.",
        viz=[{"op": "highlight", "target": "voids"}])

    n = e / (1.0 + e)
    add("compute", "Porosity", "phases",
        tex="n = \\tfrac{e}{1+e}",
        sub=f"n = \\tfrac{{{display_round(e, 3)}}}{{1+{display_round(e, 3)}}}",
        result={"sym": "n", "value": n, "unit": "",
                "display": f"{display_round(n, 3)}"},
        narration="Porosity restates the same void volume against the "
                  "total volume instead of the solids.",
        viz=[{"op": "highlight", "target": "voids"}])

    S = w * Gs / e
    add("compute", "Degree of saturation", "phases",
        tex="S = \\tfrac{w\\,G_s}{e}",
        sub=f"S = \\tfrac{{({w:g})({Gs:g})}}{{{display_round(e, 3)}}}",
        result={"sym": "S", "value": S * 100, "unit": "%",
                "display": f"{display_round(S * 100, 3)} %"},
        narration="Saturation says how much of the void space the water "
                  "actually fills.",
        viz=[{"op": "highlight", "target": "water"}])

    Ws = W / (1.0 + w)
    Vw = (W - Ws) / GAMMA_W
    add("compute", "Volume occupied by water", "phases",
        tex="V_w = \\tfrac{W - W/(1+w)}{\\gamma_w}",
        sub=f"V_w = \\tfrac{{{W:g} - {W:g}/(1+{w:g})}}{{{GAMMA_W}}}",
        result={"sym": "Vw", "value": Vw, "unit": "m^3",
                "display": f"{display_round(Vw * 1000, 3)}×10⁻³ m³"},
        narration="Subtracting the solids' weight isolates the water "
                  "weight, and the unit weight of water converts it to a "
                  "volume.",
        viz=[{"op": "highlight", "target": "water"}])

    add("conclude", "All six answers", "results",
        tex=(f"\\gamma = {display_round(gamma)}\\ \\text{{kN/m}}^3,\\quad "
             f"\\gamma_d = {display_round(gamma_d)}\\ \\text{{kN/m}}^3,\\quad "
             f"e = {display_round(e, 3)},\\quad n = {display_round(n, 3)},\\quad "
             f"S = {display_round(S * 100, 3)}\\%,\\quad "
             f"V_w = {display_round(Vw * 1000, 3)}\\times 10^{{-3}}\\ \\text{{m}}^3"),
        narration="The six quantities chain off one another: unit weight "
                  "first, then the dry unit weight, and everything else "
                  "follows from the phase diagram.",
        viz=[{"op": "highlight", "target": "phases"}])

    return {
        "results": [],
        "conclusions": [
            {"quantity": "gamma", "value": display_round(gamma), "unit": "kN/m³", "governing": "phase relations"},
            {"quantity": "e", "value": display_round(e, 3), "unit": "", "governing": "phase relations"},
            {"quantity": "S", "value": display_round(S * 100, 3), "unit": "%", "governing": "phase relations"},
        ],
        "comparison": None,
        "figure": {
            "template": "phase_diagram",
            "V": V, "W": W, "w": w, "Gs": Gs,
            "gamma": display_round(gamma), "gamma_d": display_round(gamma_d),
            "e": display_round(e, 3), "n": display_round(n, 3),
            "S": display_round(S * 100, 3),
            "Vw": display_round(Vw * 1000, 3),
        },
    }


def _density_index_step(add, e, e_max, e_min):
    """One teaching step for I_D; returns the fraction."""
    I_D = (e_max - e) / (e_max - e_min)
    add("compute", "Density index", "phases",
        tex="I_D = \\tfrac{e_{max} - e}{e_{max} - e_{min}}",
        sub=(f"I_D = \\tfrac{{{e_max:g} - {display_round(e, 3)}}}"
             f"{{{e_max:g} - {e_min:g}}}"),
        result={"sym": "I_D", "value": round(I_D, 3), "unit": "",
                "display": f"I_D = {round(I_D, 3)} "
                           f"({display_round(I_D * 100, 3)} %)"},
        narration="The density index places this packing between the "
                  "loosest and densest states the soil can take: zero at "
                  "e max, one at e min.",
        viz=[{"op": "highlight", "target": "voids"}])
    return I_D


def _from_lab(frame, givens, add, problem_text):
    """Pre-chain for raw laboratory data: tin weighings, specimen
    dimensions, measured densities, wax coatings and the limit void
    ratios. Each measurement is derived in its own step, then the run
    flows into the standard chains wherever it naturally can."""
    m_tin = givens.get("m_tin")
    m_wet_tot = givens.get("m_wet_tot")
    m_dry_tot = givens.get("m_dry_tot")
    m_wet = givens.get("m_wet")
    m_dry = givens.get("m_dry")
    D_s = givens.get("D_s")
    L_s = givens.get("L_s")
    rho_bulk = givens.get("rho_bulk")
    rho_dry = givens.get("rho_dry")
    m_wax = givens.get("m_wax")
    rho_wax = givens.get("rho_wax")
    e_max = givens.get("e_max")
    e_min = givens.get("e_min")
    V = givens.get("V")
    W_tot = givens.get("W")
    w = givens.get("w")
    Gs = givens.get("Gs")
    e = givens.get("e_void")

    density_asked = bool(_DENSITY_ASK.search(problem_text or ""))
    wax_mode = rho_wax is not None or m_wax is not None

    if w is not None and w > 1.0:
        w = w / 100.0
        add("assume", "Moisture content read as a percentage", "setup",
            tex=f"w = {w:g}", augmented=True,
            narration="The moisture content was given in percent and is "
                      "used as a fraction from here on.")

    # ---- moisture content from the oven weighings -----------------------
    if w is None and m_wet_tot is not None and m_dry_tot is not None \
            and m_tin is not None and not wax_mode:
        w = (m_wet_tot - m_dry_tot) / (m_dry_tot - m_tin)
        add("compute", "Moisture content from the tin weighings", "setup",
            tex="w = \\tfrac{m_{wet+tin} - m_{dry+tin}}"
                "{m_{dry+tin} - m_{tin}}",
            sub=(f"w = \\tfrac{{{m_wet_tot:g} - {m_dry_tot:g}}}"
                 f"{{{m_dry_tot:g} - {m_tin:g}}}"),
            result={"sym": "w", "value": w * 100, "unit": "%",
                    "display": f"w = {display_round(w * 100, 4)} %"},
            narration="The water the oven drove off is the drop between "
                      "the wet and dry weighings; dividing it by the dry "
                      "soil alone, tin subtracted, gives the moisture "
                      "content.",
            viz=[{"op": "highlight", "target": "water"}])
    elif w is None and m_wet is not None and m_dry is not None:
        w = (m_wet - m_dry) / m_dry
        add("compute", "Moisture content from the wet and dry masses",
            "setup",
            tex="w = \\tfrac{m_{wet} - m_{dry}}{m_{dry}}",
            sub=f"w = \\tfrac{{{m_wet:g} - {m_dry:g}}}{{{m_dry:g}}}",
            result={"sym": "w", "value": w * 100, "unit": "%",
                    "display": f"w = {display_round(w * 100, 4)} %"},
            narration="The mass lost on drying is the water; against the "
                      "dry soil it is the moisture content.",
            viz=[{"op": "highlight", "target": "water"}])

    # soil mass alone when only the totals with the tin were weighed
    if m_wet is None and m_wet_tot is not None and m_tin is not None \
            and not wax_mode:
        m_wet = m_wet_tot - m_tin
        add("compute", "Wet soil mass, tin removed", "setup",
            tex="m_{wet} = m_{wet+tin} - m_{tin}",
            sub=f"m_{{wet}} = {m_wet_tot:g} - {m_tin:g}",
            result={"sym": "m_wet", "value": m_wet, "unit": "kg",
                    "display": f"m = {display_round(m_wet, 4)} kg"},
            narration="Only the totals were weighed, so the tin comes off "
                      "first to leave the soil itself.",
            viz=[{"op": "highlight", "target": "total"}])

    # ---- the ask is only the water content: answer it and stop ----------
    have_volume_route = any(x is not None for x in
                            (V, D_s, L_s, rho_bulk, rho_dry))
    if w is not None and not have_volume_route and Gs is None \
            and e is None and e_max is None:
        add("conclude", "The moisture content", "results",
            tex=f"w = {display_round(w * 100, 4)}\\%",
            narration="With no volume or Gs in the problem, the moisture "
                      "content is the whole answer: it came straight from "
                      "the three weighings.",
            viz=[{"op": "highlight", "target": "water"}])
        return {
            "results": [],
            "conclusions": [
                {"quantity": "w", "value": display_round(w * 100, 4),
                 "unit": "%", "governing": "oven moisture content"},
            ],
            "comparison": None,
            "figure": {"template": "phase_diagram", "Gs": None,
                       "w": display_round(w, 4)},
        }

    # ---- specimen volume ------------------------------------------------
    if V is None and D_s is not None and L_s is not None:
        V = math.pi * D_s ** 2 / 4.0 * L_s
        add("compute", "Specimen volume from its dimensions", "setup",
            tex="V = \\tfrac{\\pi D^2}{4}\\,L",
            sub=f"V = \\tfrac{{\\pi ({D_s:g})^2}}{{4}} \\times {L_s:g}",
            result={"sym": "V", "value": V, "unit": "m^3",
                    "display": f"V = {display_round(V * 1000, 4)}"
                               "×10⁻³ m³"},
            narration="A cylindrical specimen's volume is its cross "
                      "section times its length.",
            viz=[{"op": "highlight", "target": "total"}])

    # ---- wax coated specimen: peel the wax volume off -------------------
    if wax_mode:
        if m_wax is None and m_wet_tot is not None and m_wet is not None:
            m_wax = m_wet_tot - m_wet
            add("assume", "Wax mass taken as coated minus bare", "setup",
                tex=f"m_{{wax}} = {m_wet_tot:g} - {m_wet:g} "
                    f"= {display_round(m_wax, 4)}\\ \\text{{kg}}",
                augmented=True,
                narration="The wax was not weighed on its own, so its "
                          "mass is taken as the difference between the "
                          "coated and the bare specimen.")
        if m_wax is not None and rho_wax is not None and V is not None:
            V_before = V
            V_wax = m_wax / (1000.0 * rho_wax)
            V = V - V_wax
            add("compute", "Soil volume with the wax shell removed",
                "setup",
                tex="V_{soil} = V - \\tfrac{m_{wax}}{\\rho_{wax}}",
                sub=(f"V_{{soil}} = "
                     f"{display_round(V_before * 1000, 4)}\\times10^{{-3}}"
                     f" - \\tfrac{{{display_round(m_wax, 4)}/1000}}"
                     f"{{{rho_wax:g}}}"),
                result={"sym": "V", "value": V, "unit": "m^3",
                        "display": f"V = {display_round(V * 1000, 4)}"
                                   "×10⁻³ m³"},
                narration="The displaced volume includes the wax shell; "
                          "its own mass over its own density is the "
                          "volume to strip away before any phase "
                          "relation is written.",
                viz=[{"op": "highlight", "target": "total"}])

    # ---- weight from mass -----------------------------------------------
    if W_tot is None and m_wet is not None:
        W_tot = 9.81 * m_wet / 1000.0
        add("compute", "Specimen weight from its mass", "setup",
            tex="W = m\\,g",
            sub=f"W = \\tfrac{{{m_wet:g} \\times 9.81}}{{1000}}",
            result={"sym": "W", "value": W_tot, "unit": "kN",
                    "display": f"W = {display_round(W_tot, 4)} kN"},
            narration="Mass in kilograms becomes weight in kilonewtons "
                      "through g and the factor of one thousand.",
            viz=[{"op": "highlight", "target": "total"}])

    # ---- bulk density when mass and volume are both in hand -------------
    if rho_bulk is None and m_wet is not None and V is not None:
        rho_bulk = (m_wet / 1000.0) / V
        add("compute", "Bulk density", "setup",
            tex="\\rho = \\tfrac{m}{V}",
            sub=(f"\\rho = \\tfrac{{{m_wet:g}/1000}}"
                 f"{{{display_round(V * 1000, 4)}\\times10^{{-3}}}}"),
            result={"sym": "rho", "value": rho_bulk, "unit": "Mg/m^3",
                    "display": f"ρ = {display_round(rho_bulk)} Mg/m³"},
            narration="Mass over volume is the bulk density, kept in "
                      "megagrams per cubic metre so the numbers stay "
                      "friendly.",
            viz=[{"op": "highlight", "target": "total"}])

    # ---- full sample in hand: flow into the standard chain --------------
    if V is not None and W_tot is not None and w is not None \
            and Gs is not None:
        res = _from_sample(frame, givens, add, V, W_tot, w, Gs)
        if not isinstance(res, dict) or "error" in res:
            return res
        gamma = W_tot / V
        if e_max is not None and e_min is not None:
            gamma_d = gamma / (1.0 + w)
            e_now = Gs * GAMMA_W / gamma_d - 1.0
            I_D = _density_index_step(add, e_now, e_max, e_min)
            res["conclusions"].insert(0, {
                "quantity": "I_D", "value": round(I_D, 3), "unit": "",
                "governing": f"density index, "
                             f"{display_round(I_D * 100, 3)} % toward "
                             "the densest state"})
        if density_asked:
            rho = rho_bulk if rho_bulk is not None else gamma / GAMMA_W
            if rho_bulk is None:
                add("compute", "Bulk density, as the problem asks",
                    "results",
                    tex="\\rho = \\tfrac{\\gamma}{g}",
                    sub=f"\\rho = \\tfrac{{{display_round(gamma)}}}{{9.81}}",
                    result={"sym": "rho", "value": rho, "unit": "Mg/m^3",
                            "display": f"ρ = {display_round(rho)} Mg/m³"},
                    narration="The problem speaks in densities, so the "
                              "unit weight is read back through g into "
                              "Mg/m³.",
                    viz=[{"op": "highlight", "target": "total"}])
            res["conclusions"].append({
                "quantity": "rho", "value": display_round(rho),
                "unit": "Mg/m^3", "governing": "bulk density"})
        return res

    # ---- dimensionless triple in hand: reuse that chain -----------------
    if rho_bulk is None and rho_dry is None and e is not None \
            and Gs is not None \
            and (givens.get("S_r") is not None or w is not None):
        res = _from_void_ratio(frame, givens, add)
        if not isinstance(res, dict) or "error" in res:
            return res
        if e_max is not None and e_min is not None:
            I_D = _density_index_step(add, e, e_max, e_min)
            res["conclusions"].insert(0, {
                "quantity": "I_D", "value": round(I_D, 3), "unit": "",
                "governing": f"density index, "
                             f"{display_round(I_D * 100, 3)} % toward "
                             "the densest state"})
        return res

    # ---- density route: no sample volume or weight needed ---------------
    if rho_bulk is not None or rho_dry is not None or e is not None:
        return _from_density(givens, add, rho_bulk, rho_dry, w, Gs, e,
                             e_max, e_min, density_asked)

    # ---- honest dead end -------------------------------------------------
    missing = []
    if w is None:
        missing.append("the moisture content, or the tin weighings "
                       "(wet total, dry total, tin) to derive it")
    if V is None:
        missing.append("a volume: V directly, or the specimen diameter "
                       "and length, or a measured density")
    if W_tot is None and m_wet is None:
        missing.append("the specimen mass or weight")
    if Gs is None and e is None:
        missing.append("Gs, or a void ratio, to open up the phase "
                       "relations")
    return {"error": "The lab data given does not reach the asked "
                     "quantities; still needed: " + "; ".join(missing)
                     + "."}


def _from_density(givens, add, rho_bulk, rho_dry, w, Gs, e,
                  e_max, e_min, density_asked):
    """Chain from a measured density: unit weights, then e, S and the
    density index as far as the data allows."""
    gamma = None
    gamma_d = None
    S = None
    n = None

    if rho_bulk is not None:
        gamma = GAMMA_W * rho_bulk
        add("compute", "Bulk unit weight from the bulk density", "setup",
            tex="\\gamma = \\rho\\,g",
            sub=f"\\gamma = {rho_bulk:g} \\times 9.81",
            result={"sym": "gamma", "value": gamma, "unit": "kN/m^3",
                    "display": f"{display_round(gamma)} kN/m³"},
            narration="Multiplying the density in Mg/m³ by g turns it "
                      "straight into a unit weight in kN/m³.",
            viz=[{"op": "highlight", "target": "total"}])

    if rho_dry is None and rho_bulk is not None and w is not None:
        rho_dry = rho_bulk / (1.0 + w)
        add("compute", "Dry density", "phases",
            tex="\\rho_d = \\tfrac{\\rho}{1+w}",
            sub=f"\\rho_d = \\tfrac{{{rho_bulk:g}}}{{1+{w:g}}}",
            result={"sym": "rho_d", "value": rho_dry, "unit": "Mg/m^3",
                    "display": f"ρ_d = {display_round(rho_dry)} Mg/m³"},
            narration="Stripping the water mass out leaves the dry "
                      "density; the moisture content links the two.",
            viz=[{"op": "highlight", "target": "solids"}])

    if rho_dry is not None:
        gamma_d = GAMMA_W * rho_dry
        add("compute", "Dry unit weight", "phases",
            tex="\\gamma_d = \\rho_d\\,g",
            sub=f"\\gamma_d = {display_round(rho_dry)} \\times 9.81",
            result={"sym": "gamma_d", "value": gamma_d, "unit": "kN/m^3",
                    "display": f"{display_round(gamma_d)} kN/m³"},
            narration="The dry density reads back through g the same "
                      "way the bulk one did.",
            viz=[{"op": "highlight", "target": "solids"}])

    if e is None and Gs is not None and rho_dry is not None:
        e = Gs * RHO_W / rho_dry - 1.0
        add("compute", "Void ratio from the dry density", "phases",
            tex="\\rho_d = \\tfrac{G_s\\,\\rho_w}{1+e} "
                "\\;\\Rightarrow\\; e = \\tfrac{G_s\\,\\rho_w}{\\rho_d} - 1",
            sub=f"e = \\tfrac{{({Gs:g})(1.0)}}{{{display_round(rho_dry)}}} - 1",
            result={"sym": "e", "value": e, "unit": "",
                    "display": f"{display_round(e, 3)}"},
            narration="With water at one megagram per cubic metre, the "
                      "dry density exposes the void ratio directly.",
            viz=[{"op": "highlight", "target": "voids"}])

    if e is not None and e > 0:
        n = e / (1.0 + e)
        add("compute", "Porosity", "phases",
            tex="n = \\tfrac{e}{1+e}",
            sub=f"n = \\tfrac{{{display_round(e, 3)}}}"
                f"{{1+{display_round(e, 3)}}}",
            result={"sym": "n", "value": n, "unit": "",
                    "display": f"{display_round(n, 3)}"},
            viz=[{"op": "highlight", "target": "voids"}])
        if w is not None and Gs is not None:
            S = w * Gs / e
            add("compute", "Degree of saturation", "phases",
                tex="S = \\tfrac{w\\,G_s}{e}",
                sub=f"S = \\tfrac{{({w:g})({Gs:g})}}"
                    f"{{{display_round(e, 3)}}}",
                result={"sym": "S", "value": S * 100, "unit": "%",
                        "display": f"{display_round(S * 100, 3)} %"},
                narration="Saturation says how much of the void space "
                          "the water actually fills.",
                viz=[{"op": "highlight", "target": "water"}])

    I_D = None
    if e_max is not None and e_min is not None:
        if e is None:
            return {"error": "The density index needs the in-place void "
                             "ratio; give it directly, or give a dry "
                             "density (or bulk density with moisture "
                             "content) together with Gs."}
        I_D = _density_index_step(add, e, e_max, e_min)

    conclusions = []
    tex_bits = []
    if I_D is not None:
        conclusions.append({
            "quantity": "I_D", "value": round(I_D, 3), "unit": "",
            "governing": f"density index, "
                         f"{display_round(I_D * 100, 3)} % toward the "
                         "densest state"})
        tex_bits.append(f"I_D = {round(I_D, 3)} "
                        f"= {display_round(I_D * 100, 3)}\\%")
    if density_asked and rho_bulk is not None:
        conclusions.append({
            "quantity": "rho", "value": display_round(rho_bulk),
            "unit": "Mg/m^3", "governing": "bulk density"})
        tex_bits.append(f"\\rho = {display_round(rho_bulk)}\\ "
                        "\\text{Mg/m}^3")
    if gamma is not None:
        conclusions.append({
            "quantity": "gamma", "value": display_round(gamma),
            "unit": "kN/m³", "governing": "bulk, from the density"})
        tex_bits.append(f"\\gamma = {display_round(gamma)}\\ "
                        "\\text{kN/m}^3")
    if gamma_d is not None:
        conclusions.append({
            "quantity": "gamma_d", "value": display_round(gamma_d),
            "unit": "kN/m³", "governing": "dry"})
        tex_bits.append(f"\\gamma_d = {display_round(gamma_d)}\\ "
                        "\\text{kN/m}^3")
    if not conclusions:
        return {"error": "The measured density could not be carried to "
                         "any asked quantity; a moisture content or Gs "
                         "is needed to go further."}

    add("conclude", "What the measured density gives", "results",
        tex=",\\quad ".join(tex_bits),
        narration="Everything here flowed from the weighed density: "
                  "unit weights first, then the void space once Gs "
                  "entered the picture.",
        viz=[{"op": "highlight", "target": "phases"}])

    return {
        "results": [],
        "conclusions": conclusions,
        "comparison": None,
        "figure": {
            "template": "phase_diagram",
            "Gs": Gs,
            "w": display_round(w, 4) if w is not None else None,
            "e": display_round(e, 3) if e is not None else None,
            "n": display_round(n, 3) if n is not None else None,
            "S": display_round(S * 100, 3) if S is not None else None,
            "gamma": display_round(gamma) if gamma is not None else None,
            "gamma_d": (display_round(gamma_d)
                        if gamma_d is not None else None),
        },
    }
