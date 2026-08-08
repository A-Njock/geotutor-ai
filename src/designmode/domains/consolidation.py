"""Time-rate of consolidation (Terzaghi's one-dimensional theory).

Covers the classic ask: how long a clay layer takes to reach a given
average degree of consolidation, from cv, the layer thickness and the
drainage conditions. The time factor comes from the standard closed
approximations of Terzaghi's series solution.
"""

import math
import re

from ..compute import display_round

_DOUBLE_RE = re.compile(
    r"both faces|both sides|top and bottom|two[- ]way|double[- ]?drain|"
    r"doubly drained|open layer|sand (above|layer[s]? above) and "
    r"(below|beneath)|between (two )?sand", re.IGNORECASE)
_SINGLE_RE = re.compile(
    r"one face|one side|single[- ]?drain|singly drained|impervious|"
    r"impermeable (base|boundary|rock|stratum)|half[- ]closed",
    re.IGNORECASE)


def _time_factor(U):
    """Terzaghi's Tv(U) by the standard approximations (Das eq. 7.__):
    Tv = pi/4 U^2 for U <= 60 %, else 1.781 - 0.933 log10(100 - U%)."""
    if U <= 0.6:
        return math.pi / 4.0 * U * U, "T_v = \\tfrac{\\pi}{4}U^2"
    return (1.781 - 0.933 * math.log10(100.0 - U * 100.0),
            "T_v = 1.781 - 0.933\\log_{10}(100 - U\\%)")


def build(frame: dict, givens: dict, add, problem_text: str) -> dict:
    cv = givens.get("cv")
    H = givens.get("H", givens.get("z"))
    U = givens.get("U")
    missing = [n for n, v in (("cv (coefficient of consolidation)", cv),
                              ("the clay layer thickness", H),
                              ("the degree of consolidation U", U))
               if v is None]
    if missing:
        return {"error": "The consolidation time needs "
                         + ", ".join(missing) + "."}
    if U > 1.0:
        U = U / 100.0
        add("assume", "Degree of consolidation read as a percentage",
            "setup", tex=f"U = {U:g}", augmented=True)
    if U >= 1.0:
        return {"error": "Full consolidation (U = 100 percent) takes "
                         "infinite time in Terzaghi's theory; ask for a "
                         "degree below 100 percent."}

    if _SINGLE_RE.search(problem_text):
        ways, Hdr = 1, H
        why = ("the layer drains through one face only, so the longest "
               "path a water particle must travel is the full thickness")
    elif _DOUBLE_RE.search(problem_text):
        ways, Hdr = 2, H / 2.0
        why = ("the layer drains through both faces, so the longest "
               "path a water particle must travel is half the thickness")
    else:
        return {"error": "The drainage conditions decide the drainage "
                         "path: state whether the clay drains from one "
                         "face or both (e.g. sand above and below, or an "
                         "impermeable base)."}
    add("assume", "Drainage path from the boundary conditions", "setup",
        tex=("H_{dr} = \\tfrac{H}{2} = " + f"{display_round(Hdr, 3)}"
             + "\\ \\text{m}" if ways == 2 else
             "H_{dr} = H = " + f"{display_round(Hdr, 3)}\\ \\text{{m}}"),
        narration="Because " + why + ".",
        viz=[{"op": "highlight", "target": "drainage"}])

    Tv, tv_tex = _time_factor(U)
    add("lookup", "Time factor for the target degree of consolidation",
        "setup",
        tex=tv_tex + f" = {Tv:.4f}",
        provenance=[{"symbol": "Tv", "value": round(Tv, 4),
                     "means": "dimensionless time in Terzaghi's "
                              "one-dimensional consolidation solution",
                     "source": "the standard closed approximation of "
                               "Terzaghi's series (parabolic below 60 "
                               "percent, logarithmic above)",
                     "arguments": [f"U = {U * 100:g} %"],
                     "whyApplies": "one-dimensional drainage with a "
                                   "uniform initial excess pressure, the "
                                   "textbook idealization of a loaded "
                                   "clay layer"}],
        viz=[{"op": "highlight", "target": "isochrone"}])

    t = Tv * Hdr * Hdr / cv
    add("compute", "Time from the definition of the time factor",
        "results",
        tex="T_v = \\tfrac{c_v t}{H_{dr}^2} \\;\\Rightarrow\\; "
            "t = \\tfrac{T_v H_{dr}^2}{c_v}",
        sub=(f"t = \\tfrac{{({Tv:.4f})({display_round(Hdr, 3)})^2}}"
             f"{{{cv:g}}}"),
        result={"sym": "t", "value": t, "unit": "year",
                "display": f"t = {display_round(t, 3)} years"},
        narration="The time scales with the square of the drainage path: "
                  "halving the path, as double drainage does, cuts the "
                  "waiting time by four.",
        viz=[{"op": "highlight", "target": "layer"}])

    return {
        "results": [],
        "conclusions": [
            {"quantity": "t", "value": display_round(t, 3), "unit": "years",
             "governing": f"U = {U * 100:g} % with "
                          f"{'double' if ways == 2 else 'single'} drainage"},
            {"quantity": "T_v", "value": display_round(Tv, 4), "unit": "",
             "governing": "Terzaghi time factor"}],
        "comparison": None,
        "figure": {"template": "consolidation", "H": H, "Hdr": Hdr,
                   "ways": ways, "cv": cv, "U": display_round(U * 100, 1),
                   "t": display_round(t, 3)},
    }
