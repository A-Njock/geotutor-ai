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
    missing = [n for n, v in (("V", V), ("W", W), ("w", w), ("Gs", Gs))
               if v is None]
    if missing:
        return {"error": "Phase relations need the sample volume, weight, "
                         "moisture content and Gs; missing: "
                         + ", ".join(missing) + "."}
    if w > 1.0:
        w = w / 100.0
        add("assume", "Moisture content read as a percentage", "setup",
            tex=f"w = {w:g}", augmented=True,
            narration="The moisture content was given in percent and is "
                      "used as a fraction from here on.")

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
