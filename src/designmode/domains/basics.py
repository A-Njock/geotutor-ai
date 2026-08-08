"""Phase relations from a sample's weight, volume and moisture data.

Mirrors the canonical chain (Das, ch. 3): moist unit weight, dry unit
weight, void ratio, porosity, degree of saturation, volume of water.
"""

from ..compute import display_round

GAMMA_W = 9.81  # kN/m^3


def build(frame: dict, givens: dict, add, problem_text: str) -> dict:
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
