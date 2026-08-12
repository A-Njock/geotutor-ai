"""Permeability and seepage: permeameters, pumping tests, flow nets.

Covers the four classic ways permeability enters a problem: the falling
head and constant head laboratory tests, the steady-state pumping test
(unconfined by Dupuit, confined through a constant aquifer thickness)
and the discharge under a structure read off a flow net.
"""

import math
import re

from ..compute import display_round

_FALLING_RE = re.compile(
    r"falling[- ]head|variable[- ]head|stand[- ]?pipe", re.IGNORECASE)
_CONSTANT_RE = re.compile(r"constant[- ]head", re.IGNORECASE)
_PUMP_RE = re.compile(
    r"pump|well|drawdown|aquifer", re.IGNORECASE)
_NET_RE = re.compile(r"flow[- ]?net", re.IGNORECASE)
_CONFINED_RE = re.compile(r"(?<!un)confined|artesian", re.IGNORECASE)

# Observed permeabilities run from intact clay to clean gravel.
_K_LOW, _K_HIGH = 1e-13, 1.0


def _k_sanity(k, add):
    """Warn (do not refuse) when a computed k leaves the physical range."""
    if k < _K_LOW or k > _K_HIGH:
        add("explain", "This permeability is outside the observed range",
            "results",
            tex=f"k = {display_round(k)}\\ \\text{{m/s}}",
            narration="Real soils span roughly 10^-13 m/s for intact clay "
                      "up to about 1 m/s for clean gravel. The value just "
                      "computed falls outside that whole range, which "
                      "almost always means a unit slipped somewhere in the "
                      "lengths, times or volumes. Check the inputs before "
                      "trusting the number.",
            viz=[{"op": "highlight", "target": "specimen"}])


def _k_conclude(add, k, title, why, target):
    """Concluding step showing k in m/s and cm/s."""
    k_cm = display_round(k * 100.0)
    add("conclude", title, "results",
        tex=(f"k = {display_round(k)}\\ \\text{{m/s}} = "
             f"{k_cm}\\ \\text{{cm/s}}"),
        result={"sym": "k", "value": k, "unit": "m/s",
                "display": f"k = {display_round(k)} m/s "
                           f"({k_cm} cm/s)"},
        narration=why,
        viz=[{"op": "highlight", "target": target}])


def build(frame: dict, givens: dict, add, problem_text: str) -> dict:
    text = problem_text or ""
    g = givens.get

    has_net = g("Nf") is not None and g("Nd") is not None
    has_pump = g("q_flow") is not None or (
        _PUMP_RE.search(text) and g("r1") is not None)
    has_falling = (g("h1") is not None and g("h2") is not None) or \
        g("d_pipe") is not None
    has_constant = g("h_const") is not None or g("Q_vol") is not None

    if has_net or _NET_RE.search(text):
        return _flow_net(givens, add)
    if has_pump:
        return _pumping(givens, add, text)
    if _CONSTANT_RE.search(text) and not has_falling:
        return _constant_head(givens, add)
    if _FALLING_RE.search(text) or has_falling:
        return _falling_head(givens, add)
    if has_constant:
        return _constant_head(givens, add)
    return {"error": "Say how the permeability is measured or used: a "
                     "falling head test (standpipe heads h1 and h2), a "
                     "constant head test (head and collected volume), a "
                     "pumping test (rate and two observation wells), or a "
                     "flow net (Nf and Nd)."}


# ----------------------------------------------------------------- falling

def _falling_head(givens, add):
    D_s = givens.get("D_s")
    L_s = givens.get("L_s")
    d_pipe = givens.get("d_pipe")
    h1 = givens.get("h1")
    h2 = givens.get("h2")
    t = givens.get("t_el")
    missing = [n for n, v in (
        ("the specimen diameter", D_s),
        ("the specimen length", L_s),
        ("the standpipe diameter", d_pipe),
        ("the initial head h1", h1),
        ("the final head h2", h2),
        ("the elapsed time", t)) if v is None]
    if missing:
        return {"error": "The falling head test needs "
                         + ", ".join(missing) + "."}
    if h1 <= h2:
        return {"error": "In a falling head test the head must fall: h1 "
                         "must exceed h2. Check which reading came first."}

    a = math.pi * d_pipe ** 2 / 4.0
    add("compute", "Standpipe cross-section", "setup",
        tex="a = \\tfrac{\\pi d^2}{4}",
        sub=f"a = \\tfrac{{\\pi ({d_pipe:g})^2}}{{4}}",
        result={"sym": "a", "value": a, "unit": "m²",
                "display": f"a = {display_round(a)} m²"},
        narration="The standpipe is deliberately narrow: a small area "
                  "makes the water level drop fast enough to time, which "
                  "is what lets this test reach low-permeability soils.",
        viz=[{"op": "highlight", "target": "standpipe"}])

    A = math.pi * D_s ** 2 / 4.0
    add("compute", "Specimen cross-section", "setup",
        tex="A = \\tfrac{\\pi D^2}{4}",
        sub=f"A = \\tfrac{{\\pi ({D_s:g})^2}}{{4}}",
        result={"sym": "A", "value": A, "unit": "m²",
                "display": f"A = {display_round(A)} m²"},
        narration="All the water leaving the standpipe must squeeze "
                  "through this soil face, so the two areas set the ratio "
                  "between how fast the level falls and how fast water "
                  "moves through the soil.",
        viz=[{"op": "highlight", "target": "specimen"}])

    k = (a * L_s) / (A * t) * math.log(h1 / h2)
    add("compute", "Permeability from the falling head record", "results",
        tex="k = \\tfrac{aL}{At}\\,\\ln\\!\\left(\\tfrac{h_1}{h_2}\\right)",
        sub=(f"k = \\tfrac{{({display_round(a)})({L_s:g})}}"
             f"{{({display_round(A)})({t:g})}}"
             f"\\,\\ln\\!\\left(\\tfrac{{{h1:g}}}{{{h2:g}}}\\right)"),
        result={"sym": "k", "value": k, "unit": "m/s",
                "display": f"k = {display_round(k)} m/s"},
        narration="The logarithm is the fingerprint of a self-weakening "
                  "flow: the head that drives the water is the very water "
                  "that is draining away, so the level falls fast at "
                  "first and ever slower as the head decays. Integrating "
                  "Darcy's law through that decay turns the head ratio "
                  "into ln(h1/h2).",
        viz=[{"op": "highlight", "target": "standpipe"}])

    _k_sanity(k, add)
    _k_conclude(add, k, "Permeability from the falling head test",
                "The canonical value stays in m/s; cm/s is shown because "
                "most laboratory reports and textbook charts quote it "
                "that way.", "specimen")

    return {
        "results": [],
        "conclusions": [
            {"quantity": "k", "value": display_round(k), "unit": "m/s",
             "governing": "falling head permeameter"}],
        "comparison": None,
        "figure": {"template": "permeability", "mode": "falling",
                   "D_s": D_s, "L_s": L_s, "d_pipe": d_pipe,
                   "h1": h1, "h2": h2, "k": display_round(k)},
    }


# ---------------------------------------------------------------- constant

def _constant_head(givens, add):
    D_s = givens.get("D_s")
    L_s = givens.get("L_s")
    h = givens.get("h_const", givens.get("H_head"))
    Q = givens.get("Q_vol")
    t = givens.get("t_el")
    missing = [n for n, v in (
        ("the specimen diameter", D_s),
        ("the specimen length", L_s),
        ("the constant head", h),
        ("the collected volume", Q),
        ("the elapsed time", t)) if v is None]
    if missing:
        return {"error": "The constant head test needs "
                         + ", ".join(missing) + "."}

    A = math.pi * D_s ** 2 / 4.0
    add("compute", "Specimen cross-section", "setup",
        tex="A = \\tfrac{\\pi D^2}{4}",
        sub=f"A = \\tfrac{{\\pi ({D_s:g})^2}}{{4}}",
        result={"sym": "A", "value": A, "unit": "m²",
                "display": f"A = {display_round(A)} m²"},
        narration="Darcy's law works with the discharge velocity, flow "
                  "per unit of total cross-section, so the specimen face "
                  "area is the first number needed.",
        viz=[{"op": "highlight", "target": "specimen"}])

    k = (Q * L_s) / (A * h * t)
    add("compute", "Permeability straight from Darcy's law", "results",
        tex="Q = kiAt = k\\,\\tfrac{h}{L}\\,At \\;\\Rightarrow\\; "
            "k = \\tfrac{QL}{Aht}",
        sub=(f"k = \\tfrac{{({Q:g})({L_s:g})}}"
             f"{{({display_round(A)})({h:g})({t:g})}}"),
        result={"sym": "k", "value": k, "unit": "m/s",
                "display": f"k = {display_round(k)} m/s"},
        narration="With the reservoir kept topped up the gradient never "
                  "changes: it is simply the constant head h spread over "
                  "the specimen length L. Darcy's law then says the "
                  "collected volume grows linearly with time, and k is "
                  "read off as the one unknown proportionality constant.",
        viz=[{"op": "highlight", "target": "standpipe"}])

    _k_sanity(k, add)
    _k_conclude(add, k, "Permeability from the constant head test",
                "The canonical value stays in m/s; cm/s is shown because "
                "laboratory practice usually quotes it that way. Constant "
                "head suits permeable soils, where enough water flows to "
                "measure in a reasonable time.", "specimen")

    return {
        "results": [],
        "conclusions": [
            {"quantity": "k", "value": display_round(k), "unit": "m/s",
             "governing": "constant head permeameter (Darcy)"}],
        "comparison": None,
        "figure": {"template": "permeability", "mode": "constant",
                   "D_s": D_s, "L_s": L_s, "h_const": h,
                   "k": display_round(k)},
    }


# ----------------------------------------------------------------- pumping

def _pumping(givens, add, text):
    q = givens.get("q_flow")
    r1 = givens.get("r1")
    r2 = givens.get("r2")
    hw1 = givens.get("hw1")
    hw2 = givens.get("hw2")
    missing = [n for n, v in (
        ("the steady pumping rate", q),
        ("the radius r1 of the nearer observation well", r1),
        ("the radius r2 of the farther observation well", r2),
        ("the water height hw1 at r1", hw1),
        ("the water height hw2 at r2", hw2)) if v is None]
    if missing:
        return {"error": "The pumping test needs "
                         + ", ".join(missing) + "."}
    if r2 <= r1:
        return {"error": "The observation radii must satisfy r2 > r1; "
                         "check which well is farther from the pump."}
    if hw2 <= hw1:
        return {"error": "Water must rise with distance from the pumped "
                         "well (hw2 > hw1), otherwise the drawdown cone "
                         "is inverted and the readings need checking."}

    confined = bool(_CONFINED_RE.search(text))
    if confined:
        b = givens.get("H", givens.get("z"))
        if b is None:
            return {"error": "The confined analysis needs the aquifer "
                             "thickness (the height of the permeable "
                             "layer between its impervious caps)."}
        add("assume", "Confined aquifer: flow through a fixed thickness",
            "setup",
            tex=f"b = {display_round(b, 3)}\\ \\text{{m}}",
            narration="Between its two impervious caps the aquifer stays "
                      "full: pumping lowers the pressure, not the wetted "
                      "thickness. Every cylinder around the well therefore "
                      "passes the flow through the same height b, which "
                      "is why the observation heads enter the formula "
                      "linearly instead of squared.",
            viz=[{"op": "highlight", "target": "wells"}])

        k = q * math.log(r2 / r1) / (2.0 * math.pi * b * (hw2 - hw1))
        add("compute", "Permeability from the confined pumping test",
            "results",
            tex="k = \\tfrac{q\\,\\ln(r_2/r_1)}{2\\pi b\\,(h_2 - h_1)}",
            sub=(f"k = \\tfrac{{({q:g})\\ln({r2:g}/{r1:g})}}"
                 f"{{2\\pi({display_round(b, 3)})({hw2:g}-{hw1:g})}}"),
            result={"sym": "k", "value": k, "unit": "m/s",
                    "display": f"k = {display_round(k)} m/s"},
            narration="Continuity forces the same q through every "
                      "cylinder around the well. The cylinder area 2*pi*"
                      "r*b grows with r, so the gradient must shrink as "
                      "1/r, and integrating Darcy's law between the two "
                      "observation wells leaves the logarithm of the "
                      "radius ratio over the head difference.",
            viz=[{"op": "highlight", "target": "wells"}])
        governing = "confined aquifer pumping test"
    else:
        add("assume", "Dupuit's assumptions for the unconfined aquifer",
            "setup",
            narration="Dupuit's shortcut treats the flow as horizontal "
                      "everywhere, with the gradient equal to the slope "
                      "of the drawdown surface. Near the pumped well the "
                      "flow actually curves steeply downward and the "
                      "assumption is poor, which is exactly why the "
                      "formula is written between two observation wells "
                      "away from the pump, where the errors largely "
                      "cancel.",
            viz=[{"op": "highlight", "target": "wells"}])

        k = q * math.log(r2 / r1) / (math.pi * (hw2 ** 2 - hw1 ** 2))
        add("compute", "Permeability from the unconfined pumping test",
            "results",
            tex="k = \\tfrac{q\\,\\ln(r_2/r_1)}{\\pi (h_2^2 - h_1^2)}",
            sub=(f"k = \\tfrac{{({q:g})\\ln({r2:g}/{r1:g})}}"
                 f"{{\\pi\\left(({hw2:g})^2-({hw1:g})^2\\right)}}"),
            result={"sym": "k", "value": k, "unit": "m/s",
                    "display": f"k = {display_round(k)} m/s"},
            narration="Here the saturated thickness itself is the water "
                      "height h, so the flow area 2*pi*r*h changes with "
                      "both r and h. Integrating Darcy's law with that "
                      "double dependence is what produces the squared "
                      "heights: h dh integrates to h squared over two.",
            viz=[{"op": "highlight", "target": "wells"}])
        governing = "Dupuit unconfined pumping test"

    _k_sanity(k, add)
    _k_conclude(add, k, "Field permeability from the pumping test",
                "A pumping test averages k over a large volume of ground, "
                "which is why field values often disagree with small "
                "laboratory specimens: the ground gets a vote on its own "
                "fabric, layering and fissures.", "wells")

    figure = {"template": "permeability", "mode": "pumping",
              "r1": r1, "r2": r2, "hw1": hw1, "hw2": hw2,
              "confined": confined, "k": display_round(k)}
    if confined:
        figure["b"] = b
    return {
        "results": [],
        "conclusions": [
            {"quantity": "k", "value": display_round(k), "unit": "m/s",
             "governing": governing}],
        "comparison": None,
        "figure": figure,
    }


# ---------------------------------------------------------------- flow net

def _flow_net(givens, add):
    k = givens.get("k_perm")
    H = givens.get("H_head")
    Nf = givens.get("Nf")
    Nd = givens.get("Nd")
    missing = [n for n, v in (
        ("the head difference across the structure", H),
        ("the number of flow channels Nf", Nf),
        ("the number of equipotential drops Nd", Nd)) if v is None]
    if k is None:
        missing.insert(0, "the soil permeability k")
        return {"error": "The flow net fixes only the geometry ratio "
                         "Nf/Nd; the discharge also needs "
                         + ", ".join(missing)
                         + ". A permeability cannot be guessed from the "
                           "drawing, so please provide it."}
    if missing:
        return {"error": "The flow net discharge needs "
                         + ", ".join(missing) + "."}

    add("explain", "Why the net alone fixes the shape of the answer",
        "setup",
        tex="\\Delta h_{drop} = \\tfrac{H}{N_d},\\quad "
            "\\Delta q_{channel} = k\\,\\tfrac{H}{N_d}",
        narration="A properly drawn net is made of curvilinear squares, "
                  "and that is the whole trick: in a square, the flow "
                  "path length equals the width, so every square passes "
                  "the same trickle k times H over Nd per metre of "
                  "structure. Each channel carries that same trickle all "
                  "the way through, and the Nf channels simply add up.",
        viz=[{"op": "highlight", "target": "net"}])

    qv = k * H * Nf / Nd
    add("compute", "Seepage per metre of structure", "results",
        tex="q = kH\\,\\tfrac{N_f}{N_d}",
        sub=f"q = ({k:g})({H:g})\\tfrac{{{Nf:g}}}{{{Nd:g}}}",
        result={"sym": "q", "value": qv, "unit": "m^3/s per metre",
                "display": f"q = {display_round(qv)} m³/s per metre"},
        narration="Only the ratio Nf/Nd matters, not how finely the net "
                  "was drawn: doubling every channel and drop redraws the "
                  "picture but cancels in the ratio. The soil enters only "
                  "through k, and the loading only through the head "
                  "difference H.",
        viz=[{"op": "highlight", "target": "net"}])

    add("conclude", "Seepage under the structure", "results",
        tex=f"q = {display_round(qv)}\\ \\text{{m}}^3\\text{{/s per "
            f"metre}}",
        result={"sym": "q", "value": qv, "unit": "m^3/s per metre",
                "display": f"q = {display_round(qv)} m³/s per metre of "
                           "structure"},
        narration="The answer is a rate per metre run of wall: a real "
                  "structure multiplies this by its length, and over a "
                  "day or a year these small trickles become the volumes "
                  "a dewatering pump must actually handle.",
        viz=[{"op": "highlight", "target": "net"}])

    return {
        "results": [],
        "conclusions": [
            {"quantity": "q", "value": display_round(qv),
             "unit": "m^3/s per metre",
             "governing": f"flow net with Nf/Nd = {Nf:g}/{Nd:g}"}],
        "comparison": None,
        "figure": {"template": "permeability", "mode": "flownet",
                   "Nf": Nf, "Nd": Nd, "H_head": H,
                   "k": display_round(k), "q": display_round(qv)},
    }
