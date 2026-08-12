"""Consolidation of clay layers (Terzaghi's one-dimensional theory).

Covers the classic asks around a loaded clay layer:
- how long the layer takes to reach a given average degree of
  consolidation, from cv, the thickness and the drainage conditions
  (the original path, kept as the default);
- the primary consolidation settlement, from the compression indices
  (Cc, Cr, OCR) or from the coefficient of volume compressibility mv;
- scaling an oedometer time to the field layer at the same degree of
  consolidation;
- cv recovered from permeability and mv when it is not given directly;
- the inverse question: the degree of consolidation reached after a
  stated time.

The time factor comes from the standard closed approximations of
Terzaghi's series solution. Every number is computed here in Python.
"""

import math
import re

from ..compute import display_round

GAMMA_W = 9.81       # kN/m^3, unit weight of water
YEAR_S = 3.156e7     # seconds in one year
YEAR_DAYS = 365.25   # days in one year

_DOUBLE_RE = re.compile(
    r"both faces|both sides|top and bottom|two[- ]way|double[- ]?drain|"
    r"doubly drained|open layer|sand (above|layer[s]? above) and "
    r"(below|beneath)|between (two )?sand", re.IGNORECASE)
_SINGLE_RE = re.compile(
    r"one face|one side|single[- ]?drain|singly drained|impervious|"
    r"impermeable (base|boundary|rock|stratum)|half[- ]closed",
    re.IGNORECASE)

# lab-specimen drainage wording (the specimen, not the field layer)
_LAB_SINGLE_RE = re.compile(
    r"(?:sample|specimen|oedometer|lab(?:oratory)?)[^.]{0,90}"
    r"(?:single[- ]?drain|singly drained|one[- ]way|one face|one side)|"
    r"(?:single[- ]?drain|singly drained|one[- ]way|one face|one side)"
    r"[^.]{0,60}(?:sample|specimen|oedometer)", re.IGNORECASE)

_SETTLE_RE = re.compile(
    r"settlement|settles?\b|how much (?:will|does)?[^.?]{0,50}"
    r"(?:settle|compress)|consolidat\w+ settlement", re.IGNORECASE)

# the unit the answer is asked in (default stays years)
_UNIT_RE = re.compile(
    r"\bin\s+(days|hours|minutes|months|seconds)\b", re.IGNORECASE)
_UNIT_PER_YEAR = {"days": YEAR_DAYS, "hours": YEAR_DAYS * 24.0,
                  "minutes": YEAR_DAYS * 24.0 * 60.0, "months": 12.0,
                  "seconds": YEAR_S}


def _time_factor(U):
    """Terzaghi's Tv(U) by the standard approximations (Das eq. 7.__):
    Tv = pi/4 U^2 for U <= 60 %, else 1.781 - 0.933 log10(100 - U%)."""
    if U <= 0.6:
        return math.pi / 4.0 * U * U, "T_v = \\tfrac{\\pi}{4}U^2"
    return (1.781 - 0.933 * math.log10(100.0 - U * 100.0),
            "T_v = 1.781 - 0.933\\log_{10}(100 - U\\%)")


def _degree_from_time_factor(Tv):
    """Invert Tv(U): parabolic branch below Tv = 0.283 (U = 60 %),
    logarithmic branch above."""
    if Tv < 0.283:
        U = math.sqrt(4.0 * Tv / math.pi)
        return U, "U = \\sqrt{\\tfrac{4 T_v}{\\pi}}"
    Upct = 100.0 - 10.0 ** ((1.781 - Tv) / 0.933)
    return Upct / 100.0, "U\\% = 100 - 10^{(1.781 - T_v)/0.933}"


def _requested_unit(problem_text):
    """The unit the concluding time is asked in, or None for years."""
    m = _UNIT_RE.search(problem_text)
    if not m:
        return None
    return m.group(1).lower()


def _field_drainage(problem_text, H, add):
    """Read the field drainage path from the wording. Returns
    (ways, Hdr) or (None, error_dict)."""
    if _SINGLE_RE.search(problem_text):
        ways, Hdr = 1, H
        why = ("the layer drains through one face only, so the longest "
               "path a water particle must travel is the full thickness")
    elif _DOUBLE_RE.search(problem_text):
        ways, Hdr = 2, H / 2.0
        why = ("the layer drains through both faces, so the longest "
               "path a water particle must travel is half the thickness")
    else:
        return None, {"error": "The drainage conditions decide the "
                               "drainage path: state whether the clay "
                               "drains from one face or both (e.g. sand "
                               "above and below, or an impermeable base)."}
    add("assume", "Drainage path from the boundary conditions", "setup",
        tex=("H_{dr} = \\tfrac{H}{2} = " + f"{display_round(Hdr, 3)}"
             + "\\ \\text{m}" if ways == 2 else
             "H_{dr} = H = " + f"{display_round(Hdr, 3)}\\ \\text{{m}}"),
        narration="Because " + why + ".",
        viz=[{"op": "highlight", "target": "drainage"}])
    return ways, Hdr


def _conclude_time(t_years, add, problem_text):
    """Convert the time to the unit the problem asks for. Returns
    (value_for_conclusion, unit_string)."""
    unit = _requested_unit(problem_text)
    if unit is None:
        return display_round(t_years, 3), "years"
    factor = _UNIT_PER_YEAR[unit]
    t_out = t_years * factor
    add("compute", f"Convert the time to {unit}", "results",
        tex=f"t = {display_round(t_years, 4)}\\ \\text{{years}} \\times "
            f"{factor:g}\\ \\text{{{unit}/year}}",
        result={"sym": "t", "value": t_out, "unit": unit,
                "display": f"t = {display_round(t_out, 4)} {unit}"},
        narration=f"The answer is asked in {unit}, so the time in years "
                  f"is converted before concluding.")
    return display_round(t_out, 4), unit


def build(frame: dict, givens: dict, add, problem_text: str) -> dict:
    cv = givens.get("cv")
    H = givens.get("H", givens.get("z"))
    U = givens.get("U")
    t_lab = givens.get("t_lab")
    H_lab = givens.get("H_lab")
    k_perm = givens.get("k_perm")
    mv = givens.get("mv")
    Cc, Cr = givens.get("Cc"), givens.get("Cr")
    d_sigma = givens.get("d_sigma")

    # elapsed time when the degree of consolidation is the unknown:
    # "t" is taken in years, "t_el" arrives in canonical seconds
    t_given = givens.get("t")
    if t_given is None and givens.get("t_el") is not None:
        t_given = givens["t_el"] / YEAR_S

    # Route 1: lab time scaled to the field layer at the same U
    if t_lab is not None and H_lab is not None:
        return _lab_to_field(givens, add, problem_text)

    # Route 2: cv rebuilt from permeability and compressibility
    if cv is None and k_perm is not None and mv is not None:
        cv_si = k_perm / (mv * GAMMA_W)
        cv = cv_si * YEAR_S
        add("compute", "cv from permeability and compressibility",
            "setup",
            tex="c_v = \\tfrac{k}{m_v \\gamma_w}",
            sub=(f"c_v = \\tfrac{{{k_perm:g}}}{{({mv:g})(9.81)}} = "
                 f"{display_round(cv_si, 4)}\\ \\text{{m}}^2/\\text{{s}}"),
            result={"sym": "cv", "value": cv, "unit": "m^2/year",
                    "display": f"c_v = {display_round(cv, 4)} m^2/year"},
            narration="cv bundles how fast water can escape (k) against "
                      "how much the skeleton compresses per unit stress "
                      "(mv); dividing by the unit weight of water 9.81 "
                      "kN/m^3 gives m^2/s, converted to m^2/year with "
                      "1 year = 3.156e7 s.")
        if U is None and t_given is None and not _SETTLE_RE.search(
                problem_text):
            return {
                "results": [],
                "conclusions": [
                    {"quantity": "c_v", "value": display_round(cv, 4),
                     "unit": "m^2/year",
                     "governing": "cv = k/(mv gamma_w)"}],
                "comparison": None,
                "figure": {"template": "consolidation", "H": H,
                           "cv": display_round(cv, 4)},
            }

    # Route 3: settlement magnitude, from indices or from mv
    wants_settlement = _SETTLE_RE.search(problem_text) is not None
    has_settlement_data = (Cc is not None or Cr is not None
                           or (mv is not None and d_sigma is not None))
    if has_settlement_data and (wants_settlement
                                or (U is None and t_given is None)):
        return _settlement(givens, add, problem_text)

    # Route 4: degree of consolidation reached after a stated time
    if U is None and t_given is not None and cv is not None:
        return _inverse_degree(cv, H, t_given, add, problem_text)

    # Default: time to reach a stated degree of consolidation
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

    ways, Hdr = _field_drainage(problem_text, H, add)
    if ways is None:
        return Hdr  # the error dict

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

    t_value, t_unit = _conclude_time(t, add, problem_text)
    return {
        "results": [],
        "conclusions": [
            {"quantity": "t", "value": t_value, "unit": t_unit,
             "governing": f"U = {U * 100:g} % with "
                          f"{'double' if ways == 2 else 'single'} drainage"},
            {"quantity": "T_v", "value": display_round(Tv, 4), "unit": "",
             "governing": "Terzaghi time factor"}],
        "comparison": None,
        "figure": {"template": "consolidation", "H": H, "Hdr": Hdr,
                   "ways": ways, "cv": cv, "U": display_round(U * 100, 1),
                   "t": display_round(t, 3)},
    }


def _settlement(givens: dict, add, problem_text: str) -> dict:
    """Primary consolidation settlement, by the e-log sigma indices
    (Cc, Cr with OCR) or by mv when the indices are absent."""
    H = givens.get("H", givens.get("z"))
    Cc, Cr = givens.get("Cc"), givens.get("Cr")
    mv = givens.get("mv")
    sigma_v0 = givens.get("sigma_v0")
    d_sigma = givens.get("d_sigma")
    OCR = givens.get("OCR")
    e0 = givens.get("e_void")

    # mv route only when the indices are not given
    if Cc is None and Cr is None:
        missing = [n for n, v in
                   (("mv (coefficient of volume compressibility)", mv),
                    ("the stress increase", d_sigma),
                    ("the clay layer thickness", H)) if v is None]
        if missing:
            return {"error": "The consolidation settlement needs "
                             + ", ".join(missing) + "."}
        S = mv * d_sigma * H
        S_mm = S * 1000.0
        add("compute", "Settlement from the volume compressibility",
            "results",
            tex="S_c = m_v \\, \\Delta\\sigma \\, H",
            sub=(f"S_c = ({mv:g})({d_sigma:g})({display_round(H, 3)}) = "
                 f"{display_round(S, 4)}\\ \\text{{m}}"),
            result={"sym": "S_c", "value": S_mm, "unit": "mm",
                    "display": f"S_c = {display_round(S_mm, 4)} mm"},
            narration="mv is the vertical strain per unit stress "
                      "increase, so strain times thickness gives the "
                      "settlement directly; no logarithm is involved "
                      "because mv is taken constant over this stress "
                      "range.",
            viz=[{"op": "highlight", "target": "layer"}])
        return {
            "results": [],
            "conclusions": [
                {"quantity": "S_c", "value": display_round(S_mm, 4),
                 "unit": "mm",
                 "governing": "S_c = mv d_sigma H"}],
            "comparison": None,
            "figure": {"template": "consolidation", "H": H,
                       "S_mm": display_round(S_mm, 4)},
        }

    # e-log sigma index route
    missing = [n for n, v in (("the initial effective stress", sigma_v0),
                              ("the stress increase", d_sigma),
                              ("the clay layer thickness", H))
               if v is None]
    if e0 is None:
        w, Gs = givens.get("w"), givens.get("Gs")
        if w is not None and Gs is not None:
            if w > 1.0:
                w = w / 100.0
            e0 = w * Gs
            add("assume", "Initial void ratio from w and Gs (saturated)",
                "setup",
                tex=f"e_0 = w G_s = ({w:g})({Gs:g}) = "
                    f"{display_round(e0, 3)}",
                narration="Below the water table the clay is taken as "
                          "fully saturated (S = 1), where Se = w Gs "
                          "collapses to e0 = w Gs.",
                augmented=True)
        else:
            missing.append("the initial void ratio e0 (or w and Gs of "
                           "the saturated clay)")
    if missing:
        return {"error": "The consolidation settlement needs "
                         + ", ".join(missing) + "."}

    sigma_f = sigma_v0 + d_sigma
    add("compute", "Final effective stress after the load", "setup",
        tex="\\sigma'_f = \\sigma'_{v0} + \\Delta\\sigma",
        sub=(f"\\sigma'_f = {sigma_v0:g} + {d_sigma:g} = "
             f"{display_round(sigma_f, 4)}\\ \\text{{kPa}}"),
        narration="Consolidation is driven by the change in effective "
                  "stress, from the present overburden to the value "
                  "after the new load.")

    ratio = H / (1.0 + e0)
    if OCR is None or OCR <= 1.0:
        if Cc is None:
            return {"error": "The consolidation settlement of a normally "
                             "consolidated clay needs Cc (the "
                             "compression index)."}
        if OCR is None:
            add("assume", "Clay treated as normally consolidated",
                "setup", tex="OCR = 1",
                narration="No overconsolidation ratio is given, so the "
                          "clay sits on the virgin compression line and "
                          "the full stress increase follows Cc.",
                augmented=True)
        S = Cc * ratio * math.log10(sigma_f / sigma_v0)
        S_mm = S * 1000.0
        add("compute", "Settlement on the virgin compression line",
            "results",
            tex="S_c = \\tfrac{C_c H}{1 + e_0} \\log_{10}"
                "\\tfrac{\\sigma'_{v0} + \\Delta\\sigma}{\\sigma'_{v0}}",
            sub=(f"S_c = \\tfrac{{({Cc:g})({display_round(H, 3)})}}"
                 f"{{1 + {display_round(e0, 3)}}}"
                 f"\\log_{{10}}\\tfrac{{{display_round(sigma_f, 4)}}}"
                 f"{{{sigma_v0:g}}} = {display_round(S, 4)}\\ \\text{{m}}"),
            result={"sym": "S_c", "value": S_mm, "unit": "mm",
                    "display": f"S_c = {display_round(S_mm, 4)} mm"},
            narration="A normally consolidated clay has never carried "
                      "more than its present stress, so every increment "
                      "moves it down the steep virgin line with slope "
                      "Cc.",
            viz=[{"op": "highlight", "target": "layer"}])
        governing = "NC clay, virgin compression with Cc"
    else:
        sigma_p = OCR * sigma_v0
        add("compute", "Preconsolidation stress from the OCR", "setup",
            tex="\\sigma'_p = OCR \\cdot \\sigma'_{v0}",
            sub=(f"\\sigma'_p = ({OCR:g})({sigma_v0:g}) = "
                 f"{display_round(sigma_p, 4)}\\ \\text{{kPa}}"),
            narration="The clay remembers the largest stress it has "
                      "ever carried; below that memory it recompresses "
                      "along the flat Cr line, above it the virgin Cc "
                      "line takes over.")
        if sigma_f <= sigma_p:
            if Cr is None:
                return {"error": "The settlement of an overconsolidated "
                                 "clay staying below the preconsolidation "
                                 "stress needs Cr (the recompression "
                                 "index)."}
            S = Cr * ratio * math.log10(sigma_f / sigma_v0)
            S_mm = S * 1000.0
            add("compute", "Settlement on the recompression line",
                "results",
                tex="S_c = \\tfrac{C_r H}{1 + e_0} \\log_{10}"
                    "\\tfrac{\\sigma'_{v0} + \\Delta\\sigma}"
                    "{\\sigma'_{v0}}",
                sub=(f"S_c = \\tfrac{{({Cr:g})({display_round(H, 3)})}}"
                     f"{{1 + {display_round(e0, 3)}}}"
                     f"\\log_{{10}}\\tfrac{{{display_round(sigma_f, 4)}}}"
                     f"{{{sigma_v0:g}}} = "
                     f"{display_round(S, 4)}\\ \\text{{m}}"),
                result={"sym": "S_c", "value": S_mm, "unit": "mm",
                        "display": f"S_c = {display_round(S_mm, 4)} mm"},
                narration="The final stress stays below the "
                          "preconsolidation memory, so the whole "
                          "increment rides the flat recompression line "
                          "with slope Cr; that is why overconsolidated "
                          "clays settle so much less.",
                viz=[{"op": "highlight", "target": "layer"}])
            governing = "OC clay staying below sigma_p, Cr only"
        else:
            if Cr is None or Cc is None:
                need = [n for n, v in
                        (("Cr (recompression index)", Cr),
                         ("Cc (compression index)", Cc)) if v is None]
                return {"error": "The settlement of an overconsolidated "
                                 "clay loaded past the preconsolidation "
                                 "stress needs " + " and ".join(need)
                                 + "."}
            S1 = Cr * ratio * math.log10(OCR)
            S2 = Cc * ratio * math.log10(sigma_f / sigma_p)
            S = S1 + S2
            S_mm = S * 1000.0
            add("compute", "Recompression up to the preconsolidation "
                           "stress, then virgin compression", "results",
                tex="S_c = \\tfrac{C_r H}{1 + e_0}\\log_{10}(OCR) + "
                    "\\tfrac{C_c H}{1 + e_0}\\log_{10}"
                    "\\tfrac{\\sigma'_{v0} + \\Delta\\sigma}{\\sigma'_p}",
                sub=(f"S_c = {display_round(S1, 4)} + "
                     f"{display_round(S2, 4)} = "
                     f"{display_round(S, 4)}\\ \\text{{m}}"),
                result={"sym": "S_c", "value": S_mm, "unit": "mm",
                        "display": f"S_c = {display_round(S_mm, 4)} mm"},
                narration="The load crosses the preconsolidation stress, "
                          "so the settlement comes in two legs: a small "
                          "recompression leg along Cr from the present "
                          "stress up to sigma_p, then the steep virgin "
                          "leg along Cc from sigma_p to the final "
                          "stress. Adding the two legs gives the total.",
                viz=[{"op": "highlight", "target": "layer"}])
            governing = "OC clay crossing sigma_p, Cr then Cc"

    return {
        "results": [],
        "conclusions": [
            {"quantity": "S_c", "value": display_round(S_mm, 4),
             "unit": "mm", "governing": governing}],
        "comparison": None,
        "figure": {"template": "consolidation", "H": H,
                   "S_mm": display_round(S_mm, 4),
                   "sigma_v0": sigma_v0, "d_sigma": d_sigma},
    }


def _lab_to_field(givens: dict, add, problem_text: str) -> dict:
    """Scale an oedometer time to the field layer at the same degree of
    consolidation: t scales with the square of the drainage path."""
    t_lab = givens.get("t_lab")
    H_lab = givens.get("H_lab")
    H = givens.get("H", givens.get("z"))
    if H is None:
        return {"error": "Scaling the laboratory time to the field "
                         "needs the field clay layer thickness."}

    # laboratory drainage: oedometer specimens sit between two porous
    # stones, so double drainage unless the text says otherwise
    if _LAB_SINGLE_RE.search(problem_text):
        Hdr_lab = H_lab
        add("assume", "Laboratory specimen drained through one face",
            "setup",
            tex="H_{dr,lab} = H_{lab} = "
                + f"{display_round(Hdr_lab, 4)}\\ \\text{{m}}",
            narration="The text states single drainage for the "
                      "specimen, so its drainage path is the full "
                      "specimen thickness.")
    else:
        Hdr_lab = H_lab / 2.0
        add("assume", "Oedometer specimen taken as doubly drained",
            "setup",
            tex="H_{dr,lab} = \\tfrac{H_{lab}}{2} = "
                + f"{display_round(Hdr_lab, 4)}\\ \\text{{m}}",
            narration="An oedometer specimen sits between two porous "
                      "stones, so it drains through top and bottom and "
                      "the drainage path is half the specimen "
                      "thickness.",
            augmented=True)

    ways, Hdr = _field_drainage(problem_text, H, add)
    if ways is None:
        return Hdr  # the error dict

    t_field_s = t_lab * (Hdr / Hdr_lab) ** 2
    t_years = t_field_s / YEAR_S
    add("compute", "Field time from the square of the drainage paths",
        "results",
        tex="T_v = \\tfrac{c_v t}{H_{dr}^2}\\ \\text{equal at equal } U "
            "\\;\\Rightarrow\\; t_{field} = t_{lab}\\left("
            "\\tfrac{H_{dr,field}}{H_{dr,lab}}\\right)^2",
        sub=(f"t_{{field}} = ({t_lab:g})\\left(\\tfrac"
             f"{{{display_round(Hdr, 4)}}}{{{display_round(Hdr_lab, 4)}}}"
             f"\\right)^2 = {display_round(t_field_s, 4)}\\ \\text{{s}}"),
        result={"sym": "t", "value": t_years, "unit": "year",
                "display": f"t = {display_round(t_years, 4)} years"},
        narration="At the same average degree of consolidation the time "
                  "factor Tv is the same in the oedometer and in the "
                  "ground, and cv is a soil property shared by both. So "
                  "the time scales with the square of the drainage "
                  "path: a field path a thousand times longer means a "
                  "million times the waiting time.",
        viz=[{"op": "highlight", "target": "layer"}])

    t_value, t_unit = _conclude_time(t_years, add, problem_text)
    return {
        "results": [],
        "conclusions": [
            {"quantity": "t", "value": t_value, "unit": t_unit,
             "governing": "same U, t scales with the drainage path "
                          "squared"}],
        "comparison": None,
        "figure": {"template": "consolidation", "H": H, "Hdr": Hdr,
                   "ways": ways, "t": display_round(t_years, 3)},
    }


def _inverse_degree(cv, H, t_years, add, problem_text: str) -> dict:
    """Degree of consolidation reached after a stated time: Tv from the
    definition, then U from the inverted Terzaghi approximations."""
    if H is None:
        return {"error": "The degree of consolidation after a given "
                         "time needs the clay layer thickness."}

    ways, Hdr = _field_drainage(problem_text, H, add)
    if ways is None:
        return Hdr  # the error dict

    Tv = cv * t_years / (Hdr * Hdr)
    add("compute", "Time factor reached after the elapsed time",
        "setup",
        tex="T_v = \\tfrac{c_v t}{H_{dr}^2}",
        sub=(f"T_v = \\tfrac{{({cv:g})({display_round(t_years, 4)})}}"
             f"{{({display_round(Hdr, 3)})^2}} = {Tv:.4f}"),
        narration="The elapsed time is turned into the dimensionless "
                  "time factor; the drainage path enters squared, so "
                  "the drainage conditions matter as much as the clock.",
        viz=[{"op": "highlight", "target": "isochrone"}])

    U, u_tex = _degree_from_time_factor(Tv)
    Upct = U * 100.0
    add("compute", "Degree of consolidation from the time factor",
        "results",
        tex=u_tex,
        sub=f"U = {display_round(Upct, 4)}\\ \\%",
        result={"sym": "U", "value": Upct, "unit": "%",
                "display": f"U = {display_round(Upct, 4)} %"},
        narration="Terzaghi's solution is inverted: the parabolic "
                  "branch serves below Tv = 0.283 (U under 60 percent), "
                  "the logarithmic branch above. Early consolidation is "
                  "fast and the tail is slow, which is why the last few "
                  "percent take the longest.",
        viz=[{"op": "highlight", "target": "layer"}])

    return {
        "results": [],
        "conclusions": [
            {"quantity": "U", "value": display_round(Upct, 4),
             "unit": "%",
             "governing": f"t = {display_round(t_years, 4)} years with "
                          f"{'double' if ways == 2 else 'single'} "
                          "drainage"},
            {"quantity": "T_v", "value": display_round(Tv, 4), "unit": "",
             "governing": "Terzaghi time factor"}],
        "comparison": None,
        "figure": {"template": "consolidation", "H": H, "Hdr": Hdr,
                   "ways": ways, "cv": cv,
                   "U": display_round(Upct, 1),
                   "t": display_round(t_years, 3)},
    }
