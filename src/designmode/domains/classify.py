"""Soil classification: USCS (ASTM D2487), AASHTO (M145) and BS 5930.

Given sieve fractions and Atterberg limits (or qualitative field cues on
the fines), the builder walks the classification chart step by step and
names the group symbol and group name. Every number and every branch
decision is computed here in full precision.
"""

import re

from ..compute import display_round

_USCS_RE = re.compile(r"\buscs\b|unified", re.I)
_AASHTO_RE = re.compile(r"aashto", re.I)
_BS_RE = re.compile(r"\bbs\b|british", re.I)

# keys that may arrive as fractions of one instead of percentages
_PCT_KEYS = ("P200", "P4", "LL", "PL", "PI")

_GRADE_WORD = {"W": "Well-graded", "P": "Poorly graded"}
_FINES_WORD = {"M": "silt", "C": "clay"}
_FINE_BASE = {
    "CL": "Lean clay", "ML": "Silt", "CH": "Fat clay",
    "MH": "Elastic silt", "CL-ML": "Silty clay",
    "OL": "Organic silt", "OH": "Organic clay",
}


def build(frame: dict, givens: dict, add, problem_text: str) -> dict:
    g = dict(givens)
    cue_text = problem_text + " " + " ".join(
        str(a) for a in (frame.get("assumptions_made") or []))

    # --- percentages given as fractions of one -------------------------
    scaled = [k for k in _PCT_KEYS
              if g.get(k) is not None and 0 < g[k] <= 2.0]
    for k in scaled:
        g[k] = g[k] * 100.0
    if scaled:
        add("assume", "Fractions read as percentages", "setup",
            tex=",\\; ".join(f"{k} = {g[k]:g}\\%" for k in scaled),
            augmented=True,
            narration="The values of " + ", ".join(scaled) + " were given "
                      "as fractions of one; they are used as percentages "
                      "from here on.")

    # --- which classification system ----------------------------------
    if _USCS_RE.search(problem_text):
        system = "USCS"
    elif _AASHTO_RE.search(problem_text):
        system = "AASHTO"
    elif _BS_RE.search(problem_text):
        system = "BS 5930"
    else:
        system = "USCS"
        add("assume", "Classification system", "setup",
            augmented=True,
            narration="No system was named, so the Unified Soil "
                      "Classification System (ASTM D2487) is used; it is "
                      "the default in most geotechnical practice. Ask for "
                      "AASHTO or BS 5930 explicitly if you need those.")

    P200 = g.get("P200")
    if P200 is None:
        return {"error": "Classification needs the fines content: the "
                         "percent passing the 0.075 mm (No. 200) sieve."}
    if not 0 <= P200 <= 100:
        return {"error": "The percent passing the No. 200 sieve must lie "
                         "between 0 and 100."}

    P4 = g.get("P4")
    if P4 is not None and P4 < P200:
        return {"error": "The percent passing the No. 4 sieve cannot be "
                         "smaller than the percent passing the No. 200 "
                         "sieve; please check the two values."}
    p4_assumed = P4 is None
    if p4_assumed:
        P4 = 100.0
    gravel = max(0.0, 100.0 - P4)
    sand = max(0.0, P4 - P200)
    fines = P200
    if p4_assumed and (fines < 50 or (100.0 - fines) >= 15):
        add("assume", "Coarse fraction taken as sand", "setup",
            augmented=True,
            narration="No No. 4 sieve split was given, so the whole "
                      "coarse fraction is treated as sand. Give the "
                      "percent passing 4.75 mm if gravel matters here.")

    add("compute", "Split the sample into gravel, sand and fines",
        "fractions",
        tex="\\text{gravel} = 100 - P_4,\\quad "
            "\\text{sand} = P_4 - P_{200},\\quad "
            "\\text{fines} = P_{200}",
        sub=f"\\text{{gravel}} = {display_round(gravel, 3):g}\\%,\\; "
            f"\\text{{sand}} = {display_round(sand, 3):g}\\%,\\; "
            f"\\text{{fines}} = {display_round(fines, 3):g}\\%",
        result={"sym": "fines", "value": fines, "unit": "%",
                "display": f"fines = {display_round(fines, 3):g} %"},
        narration="Two sieves cut the sample into three families: what "
                  "stays on the 4.75 mm sieve is gravel, what passes it "
                  "but stays on the 0.075 mm sieve is sand, and what "
                  "passes both is fines. Every chart below keys off "
                  "these three numbers.",
        viz=[{"op": "highlight", "target": "fractions"}])

    # --- Atterberg limits and gradation numbers ------------------------
    LL = g.get("LL")
    PL = g.get("PL")
    PI = g.get("PI")
    if PI is None and LL is not None and PL is not None:
        PI = LL - PL
        add("compute", "Plasticity index from the two limits", "chart",
            tex="PI = LL - PL",
            sub=f"PI = {LL:g} - {PL:g}",
            result={"sym": "PI", "value": PI, "unit": "",
                    "display": f"PI = {display_round(PI, 3):g}"},
            narration="The plasticity index is the moisture range over "
                      "which the fines behave plastically: liquid limit "
                      "minus plastic limit.",
            viz=[{"op": "highlight", "target": "chart"}])

    D10 = g.get("D10")
    D30 = g.get("D30")
    D60 = g.get("D60")
    Cu = g.get("Cu")
    Cz = g.get("Cz")
    if Cz is None:
        Cz = g.get("Cc")  # many texts print the curvature coefficient Cc
    if Cu is None and D10 and D60:
        Cu = D60 / D10
        add("compute", "Uniformity coefficient", "fractions",
            tex="C_u = \\tfrac{D_{60}}{D_{10}}",
            sub=f"C_u = \\tfrac{{{D60:g}}}{{{D10:g}}}",
            result={"sym": "Cu", "value": Cu, "unit": "",
                    "display": f"Cu = {display_round(Cu, 3):g}"},
            narration="Cu measures how wide the grain-size curve is: the "
                      "60 percent passing size over the 10 percent "
                      "passing size.",
            viz=[{"op": "highlight", "target": "fractions"}])
    if Cz is None and D10 and D30 and D60:
        Cz = D30 ** 2 / (D10 * D60)
        add("compute", "Coefficient of curvature", "fractions",
            tex="C_z = \\tfrac{D_{30}^2}{D_{10} D_{60}}",
            sub=f"C_z = \\tfrac{{({D30:g})^2}}{{({D10:g})({D60:g})}}",
            result={"sym": "Cz", "value": Cz, "unit": "",
                    "display": f"Cz = {display_round(Cz, 3):g}"},
            narration="Cz checks the shape of the curve between those "
                      "sizes; a smooth, well-filled curve keeps Cz "
                      "between 1 and 3.",
            viz=[{"op": "highlight", "target": "fractions"}])

    cue, cue_why = _cue(cue_text)

    args = dict(add=add, gravel=gravel, sand=sand, fines=fines,
                LL=LL, PI=PI, Cu=Cu, Cz=Cz, cue=cue, cue_why=cue_why)
    if system == "AASHTO":
        return _aashto(**args)
    if system == "BS 5930":
        return _bs(**args)
    return _uscs(**args)


# ----------------------------------------------------------------------
# qualitative fines cues

def _cue(text):
    t = text.lower()
    if re.search(r"organic|odou?r|dark", t):
        return "O", ("the description mentions organic matter, odor or a "
                     "dark color")
    if re.search(r"high\s+dry\s+strength|no\s+dilatancy", t):
        return "C", ("high dry strength (or no dilatancy reaction) is the "
                     "field signature of clay fines")
    if re.search(r"(quick|rapid)[^.\n]{0,40}dilatanc|dilatanc[^.\n]{0,40}"
                 r"(quick|rapid)", t):
        return "M", ("a quick dilatancy reaction is the field signature "
                     "of silt fines")
    return None, None


def _fines_letter(add, LL, PI, cue, cue_why, context):
    """Return ('M'|'C'|'CM', label) for the fines, or an error dict.

    Uses the A-line when LL and PI are known; falls back to a stated
    field cue otherwise.
    """
    if LL is not None and PI is not None:
        pi_a = 0.73 * (LL - 20.0)
        add("lookup", "Place the fines against the A-line", "chart",
            tex="PI_A = 0.73\\,(LL - 20)",
            sub=f"PI_A = 0.73\\,({LL:g} - 20) = {display_round(pi_a, 3):g}",
            provenance=[{"symbol": "A-line", "value": display_round(pi_a, 3),
                         "means": "the PI that separates clays (above) "
                                  "from silts (below) at this LL",
                         "source": "Casagrande plasticity chart, "
                                   "ASTM D2487",
                         "arguments": [f"LL = {LL:g}", f"PI = {PI:g}"],
                         "whyApplies": "the fines' plastic behavior, not "
                                       "their grain size, decides between "
                                       "silt and clay"}],
            narration="On the plasticity chart the A-line splits clay "
                      "behavior from silt behavior. The soil's point at "
                      f"LL = {LL:g}, PI = {PI:g} sits "
                      + ("above" if PI >= pi_a else "below")
                      + " the A-line.",
            viz=[{"op": "highlight", "target": "chart"}])
        if PI > 7 and PI >= pi_a:
            return "C", "above the A-line with PI over 7"
        if PI < 4 or PI < pi_a:
            return "M", "below the A-line or PI under 4"
        return "CM", "in the hatched CL-ML band, PI between 4 and 7 " \
                     "above the A-line"
    if cue in ("M", "C"):
        letter = cue
        add("assume", "Fines judged from the stated field cue", "chart",
            augmented=True,
            narration="No Atterberg limits were given for the fines, so "
                      "the stated field behavior stands in: " + cue_why
                      + ". Run the limits to confirm this call.",
            viz=[{"op": "highlight", "target": "chart"}])
        return letter, "field cue: " + cue_why
    if cue == "O":
        add("assume", "Fines judged organic from the description", "chart",
            augmented=True,
            narration="No Atterberg limits were given; the description "
                      "suggests organic fines (" + cue_why + "). For a "
                      "coarse soil the organic tag does not change the "
                      "letter, so silt is used for the second symbol.",
            viz=[{"op": "highlight", "target": "chart"}])
        return "M", "organic cue, treated as silt for the " + context
    return {"error": "The fines need either the Atterberg limits (LL and "
                     "PL or PI) or a qualitative cue (dilatancy speed, "
                     "dry strength, organic signs) to be named silt or "
                     "clay."}


# ----------------------------------------------------------------------
# USCS, ASTM D2487

def _uscs(add, gravel, sand, fines, LL, PI, Cu, Cz, cue, cue_why):
    if fines < 50.0:
        out = _uscs_coarse(add, gravel, sand, fines, LL, PI, Cu, Cz,
                           cue, cue_why)
    else:
        out = _uscs_fine(add, gravel, sand, fines, LL, PI, cue, cue_why)
    if "error" in out:
        return out
    symbol, name = out["symbol"], out["name"]
    add("conclude", "USCS group symbol and name", "results",
        tex=f"\\textbf{{{symbol}}}\\;:\\; \\text{{{name}}}",
        narration=f"Per ASTM D2487 the soil classifies as {symbol}, "
                  f"{name.lower()}. The symbol carries the whole story: "
                  "the first letter is the dominant fraction, the second "
                  "is the gradation or the fines' behavior.",
        viz=[{"op": "highlight", "target": "fractions"},
             {"op": "highlight", "target": "chart"}])
    return _package("USCS (ASTM D2487)", symbol, name, gravel, sand,
                    fines, LL, PI)


def _uscs_coarse(add, gravel, sand, fines, LL, PI, Cu, Cz, cue, cue_why):
    prefix = "G" if gravel > sand else "S"
    word = "gravel" if prefix == "G" else "sand"
    other = sand if prefix == "G" else gravel
    other_word = "sand" if prefix == "G" else "gravel"
    add("explain", "Coarse-grained soil: pick the dominant fraction",
        "fractions",
        narration=f"With {display_round(fines, 3):g}% fines, under 50, "
                  "the soil is coarse-grained. Gravel at "
                  f"{display_round(gravel, 3):g}% versus sand at "
                  f"{display_round(sand, 3):g}% makes this a {word}, so "
                  f"the first letter is {prefix}.",
        viz=[{"op": "highlight", "target": "fractions"}])

    cu_lim = 4.0 if prefix == "G" else 6.0

    def grade_letter():
        if Cu is None or Cz is None:
            return None
        well = (Cu >= cu_lim) and (1.0 <= Cz <= 3.0)
        gl = "W" if well else "P"
        add("lookup", "Well graded or poorly graded", "fractions",
            tex=f"C_u \\ge {cu_lim:g} \\;\\text{{and}}\\; 1 \\le C_z \\le 3"
                "\\;\\Rightarrow\\; \\text{well graded}",
            sub=f"C_u = {display_round(Cu, 3):g},\\; "
                f"C_z = {display_round(Cz, 3):g}",
            provenance=[{"symbol": "Cu, Cz limits",
                         "value": f"Cu >= {cu_lim:g}, 1 <= Cz <= 3",
                         "means": "the gradation test for a well-graded "
                                  + word,
                         "source": "ASTM D2487, Table 1",
                         "arguments": [f"Cu = {display_round(Cu, 3):g}",
                                       f"Cz = {display_round(Cz, 3):g}"],
                         "whyApplies": "with few fines, packing quality "
                                       "is what the second letter must "
                                       "report"}],
            narration=("Both tests pass, so the " + word + " is well "
                       "graded: letter W."
                       if well else
                       "The gradation test fails "
                       + (f"(Cu = {display_round(Cu, 3):g} is under "
                          f"{cu_lim:g})" if Cu < cu_lim else
                          f"(Cz = {display_round(Cz, 3):g} falls outside "
                          "1 to 3)")
                       + ", so the " + word + " is poorly graded: "
                       "letter P."),
            viz=[{"op": "highlight", "target": "fractions"}])
        return gl

    if fines < 5.0:
        gl = grade_letter()
        if gl is None:
            return {"error": "With under 5% fines the group turns on the "
                             "gradation: give Cu and Cz, or D10, D30 and "
                             "D60 so they can be computed."}
        symbol = prefix + gl
        name = f"{_GRADE_WORD[gl]} {word}"
        if other >= 15.0:
            name += f" with {other_word}"
        return {"symbol": symbol, "name": name}

    if fines <= 12.0:
        gl = grade_letter()
        if gl is None:
            return {"error": "With 5 to 12% fines the group takes a dual "
                             "symbol, and the first half needs Cu and Cz "
                             "(or D10, D30 and D60)."}
        fl = _fines_letter(add, LL, PI, cue, cue_why, "dual symbol")
        if isinstance(fl, dict):
            return fl
        letter, how = fl
        if letter == "CM":
            letter = "M"  # borderline fines: report the silty half
        add("explain", "Borderline fines call for a dual symbol",
            "fractions",
            narration=f"Fines at {display_round(fines, 3):g}% sit in the "
                      "5 to 12% window: too many to ignore, too few to "
                      "govern. D2487 answers with a dual symbol, "
                      "gradation first, fines second.",
            viz=[{"op": "highlight", "target": "fractions"}])
        symbol = f"{prefix}{gl}-{prefix}{letter}"
        name = f"{_GRADE_WORD[gl]} {word} with {_FINES_WORD[letter]}"
        if other >= 15.0:
            name += f" and {other_word}"
        return {"symbol": symbol, "name": name}

    fl = _fines_letter(add, LL, PI, cue, cue_why, "second letter")
    if isinstance(fl, dict):
        return fl
    letter, how = fl
    if letter == "CM":
        symbol = f"{prefix}C-{prefix}M"
        name = f"Silty, clayey {word}"
    else:
        symbol = prefix + letter
        name = ("Silty " if letter == "M" else "Clayey ") + word
    if other >= 15.0:
        name += f" with {other_word}"
    return {"symbol": symbol, "name": name}


def _uscs_fine(add, gravel, sand, fines, LL, PI, cue, cue_why):
    add("explain", "Fine-grained soil: the chart takes over", "chart",
        narration=f"With {display_round(fines, 3):g}% fines, at least "
                  "half the soil passes the No. 200 sieve, so grain size "
                  "steps aside and the plasticity chart decides "
                  "everything.",
        viz=[{"op": "highlight", "target": "chart"}])

    if cue == "O":
        symbol = "OH" if (LL is not None and LL >= 50) else "OL"
        add("assume", "Organic fines from the description", "chart",
            augmented=True,
            narration="The description flags organic soil: " + cue_why
                      + ". D2487 then swaps the mineral letter for O; "
                      "confirm with the oven-dried liquid limit test "
                      "when possible.",
            viz=[{"op": "highlight", "target": "chart"}])
    elif LL is None or PI is None:
        if cue in ("M", "C"):
            symbol = "ML" if cue == "M" else "CL"
            add("assume", "Fines judged from the stated field cue",
                "chart", augmented=True,
                narration="No Atterberg limits were given, so the field "
                          "behavior stands in: " + cue_why + ". Low "
                          "plasticity is assumed; run the limits to "
                          "confirm.",
                viz=[{"op": "highlight", "target": "chart"}])
        else:
            return {"error": "A fine-grained soil needs the Atterberg "
                             "limits (LL and PL or PI), or at least a "
                             "field cue such as dilatancy speed, dry "
                             "strength or organic signs."}
    else:
        pi_a = 0.73 * (LL - 20.0)
        add("lookup", "Place the soil on the plasticity chart", "chart",
            tex="PI_A = 0.73\\,(LL - 20)",
            sub=f"PI_A = 0.73\\,({LL:g} - 20) = {display_round(pi_a, 3):g}",
            provenance=[{"symbol": "A-line",
                         "value": display_round(pi_a, 3),
                         "means": "the PI separating clays (above) from "
                                  "silts (below) at this LL",
                         "source": "Casagrande plasticity chart, "
                                   "ASTM D2487",
                         "arguments": [f"LL = {LL:g}", f"PI = {PI:g}"],
                         "whyApplies": "for fine soils the chart position "
                                       "is the classification"}],
            narration=f"At LL = {LL:g} the A-line sits at PI = "
                      f"{display_round(pi_a, 3):g}. The soil's PI of "
                      f"{PI:g} puts it "
                      + ("above" if PI >= pi_a else "below")
                      + " the line, and LL "
                      + ("at or past" if LL >= 50 else "under")
                      + " 50 fixes the high or low plasticity side.",
            viz=[{"op": "highlight", "target": "chart"}])
        if LL < 50:
            if PI > 7 and PI >= pi_a:
                symbol = "CL"
            elif PI < 4 or PI < pi_a:
                symbol = "ML"
            else:
                symbol = "CL-ML"
        else:
            symbol = "CH" if PI >= pi_a else "MH"

    base = _FINE_BASE[symbol]
    plus200 = 100.0 - fines
    coarse_word = "sand" if sand >= gravel else "gravel"
    if plus200 >= 30.0:
        name = ("Sandy " if coarse_word == "sand" else "Gravelly ") \
               + base[0].lower() + base[1:]
    elif plus200 >= 15.0:
        name = base + f" with {coarse_word}"
    else:
        name = base
    if plus200 >= 15.0:
        add("compute", "Name modifier from the retained fraction",
            "fractions",
            tex="100 - P_{200}",
            sub=f"100 - {display_round(fines, 3):g} = "
                f"{display_round(plus200, 3):g}\\%",
            narration=f"{display_round(plus200, 3):g}% of the soil is "
                      "retained on the No. 200 sieve, so D2487 appends "
                      "the dominant coarse fraction to the name.",
            viz=[{"op": "highlight", "target": "fractions"}])
    return {"symbol": symbol, "name": name}


# ----------------------------------------------------------------------
# AASHTO M145

def _aashto(add, gravel, sand, fines, LL, PI, Cu, Cz, cue, cue_why):
    F = fines
    add("explain", "AASHTO reads the soil as a road subgrade", "fractions",
        narration="AASHTO M145 sorts soils by how they behave under a "
                  "pavement: granular groups A-1 to A-3, then silt-clay "
                  "groups A-4 to A-7. The split falls at 35% passing the "
                  "No. 200 sieve.",
        viz=[{"op": "highlight", "target": "fractions"}])

    if F <= 35.0:
        if PI is None or PI <= 6.0:
            if PI is not None and PI == 0 and F <= 10.0:
                symbol, desc = "A-3", "Fine sand"
            elif F <= 15.0:
                symbol, desc = "A-1-a", "Stone fragments, gravel and sand"
            elif F <= 25.0:
                symbol, desc = "A-1-b", "Stone fragments, gravel and sand"
            else:
                symbol, desc = "A-2-4", "Silty or clayey gravel and sand"
            add("lookup", "Granular soil with non-plastic fines",
                "fractions",
                narration=f"With {display_round(F, 3):g}% fines (35% or "
                          "less) and a plasticity index of 6 or less, "
                          "the soil lands in the clean granular groups.",
                viz=[{"op": "highlight", "target": "fractions"}])
        else:
            if LL is None:
                return {"error": "An A-2 soil needs the liquid limit to "
                                 "pick its subgroup (A-2-4 to A-2-7)."}
            subg = ("4" if (LL <= 40 and PI <= 10) else
                    "5" if PI <= 10 else
                    "6" if LL <= 40 else "7")
            symbol = "A-2-" + subg
            desc = "Silty or clayey gravel and sand"
            add("lookup", "Granular soil with plastic fines: A-2 "
                "subgroup", "chart",
                narration=f"Fines are {display_round(F, 3):g}%, still "
                          "35% or less, but plastic. LL and PI pick the "
                          f"subgroup: A-2-{subg}.",
                viz=[{"op": "highlight", "target": "chart"}])
    else:
        if LL is None or PI is None:
            return {"error": "A silt-clay soil (over 35% fines) needs LL "
                             "and PI to pick between A-4, A-5, A-6 and "
                             "A-7."}
        if PI <= 10.0:
            symbol = "A-4" if LL <= 40 else "A-5"
            desc = "Silty soils"
        elif LL <= 40.0:
            symbol, desc = "A-6", "Clayey soils"
        else:
            branch = "A-7-5" if PI <= LL - 30.0 else "A-7-6"
            symbol, desc = branch, "Clayey soils"
            add("lookup", "A-7 splits on the plastic limit", "chart",
                tex="PI \\le LL - 30 \\Rightarrow \\text{A-7-5},\\quad "
                    "PI > LL - 30 \\Rightarrow \\text{A-7-6}",
                sub=f"PI = {PI:g},\\; LL - 30 = {LL - 30:g}",
                narration="Both A-7 branches are high-plasticity clays; "
                          "A-7-6, the more troublesome one, has the "
                          "higher PI relative to its LL and swells more.",
                viz=[{"op": "highlight", "target": "chart"}])
        if symbol in ("A-4", "A-5", "A-6"):
            add("lookup", "Silt-clay group from LL and PI", "chart",
                narration=f"With {display_round(F, 3):g}% fines, over "
                          f"35%, the soil is a silt-clay material. LL = "
                          f"{LL:g} and PI = {PI:g} place it in {symbol}.",
                viz=[{"op": "highlight", "target": "chart"}])

    # group index with the standard clamps
    if symbol.startswith("A-1") or symbol == "A-3":
        GI = 0
        add("compute", "Group index", "results",
            tex="GI = 0",
            result={"sym": "GI", "value": 0, "unit": "",
                    "display": "GI = 0"},
            narration="A-1 and A-3 soils take a group index of zero by "
                      "definition.",
            viz=[{"op": "highlight", "target": "fractions"}])
    else:
        LLv = LL if LL is not None else 0.0
        PIv = PI if PI is not None else 0.0
        t1 = min(max(F - 35.0, 0.0), 40.0)
        t2 = min(max(LLv - 40.0, 0.0), 20.0)
        t3 = min(max(F - 15.0, 0.0), 40.0)
        t4 = min(max(PIv - 10.0, 0.0), 20.0)
        if symbol in ("A-2-6", "A-2-7"):
            gi_raw = 0.01 * t3 * t4
            sub_tex = f"GI = 0.01\\,({t3:g})({t4:g})"
        else:
            gi_raw = t1 * (0.2 + 0.005 * t2) + 0.01 * t3 * t4
            sub_tex = (f"GI = ({t1:g})\\,[0.2 + 0.005({t2:g})] + "
                       f"0.01\\,({t3:g})({t4:g})")
        GI = max(0, int(gi_raw + 0.5))  # round half up, never banker's
        add("compute", "Group index", "results",
            tex="GI = (F-35)[0.2 + 0.005(LL-40)] + 0.01(F-15)(PI-10)",
            sub=sub_tex + f" = {display_round(gi_raw, 3):g}",
            result={"sym": "GI", "value": GI, "unit": "",
                    "display": f"GI = {GI}"},
            narration="Each bracket is clamped to its standard range and "
                      "floored at zero, then the total is rounded to the "
                      "nearest whole number. A bigger index means a "
                      "poorer subgrade."
                      + (" A-2-6 and A-2-7 keep only the PI term."
                         if symbol in ("A-2-6", "A-2-7") else ""),
            viz=[{"op": "highlight", "target": "chart"}])

    full = f"{symbol} ({GI})"
    rating = ("excellent to good" if symbol.startswith(("A-1", "A-2"))
              or symbol == "A-3" else "fair to poor")
    name = f"{desc}, {rating} as subgrade"
    add("conclude", "AASHTO group and group index", "results",
        tex=f"\\textbf{{{full}}}",
        narration=f"The soil classifies as {full}: {desc.lower()}, rated "
                  f"{rating} as a subgrade. The group index in "
                  "parentheses grades it within the group.",
        viz=[{"op": "highlight", "target": "fractions"},
             {"op": "highlight", "target": "chart"}])
    out = _package("AASHTO M145", full, name, gravel, sand, fines, LL, PI)
    out["conclusions"] = [
        {"quantity": "group_symbol", "value": symbol, "unit": "",
         "governing": "AASHTO M145"},
        {"quantity": "group_name", "value": name, "unit": "",
         "governing": "AASHTO M145"},
        {"quantity": "group_index", "value": GI, "unit": "",
         "governing": "AASHTO M145"},
    ]
    return out


# ----------------------------------------------------------------------
# BS 5930

_BS_BAND = (("L", 35.0, "low"), ("I", 50.0, "intermediate"),
            ("H", 70.0, "high"), ("V", 90.0, "very high"),
            ("E", float("inf"), "extremely high"))


def _bs(add, gravel, sand, fines, LL, PI, Cu, Cz, cue, cue_why):
    if fines < 50.0:
        # coarse soils keep the same letters as the Unified chart
        out = _uscs_coarse(add, gravel, sand, fines, LL, PI, Cu, Cz,
                           cue, cue_why)
        if "error" in out:
            return out
        symbol, name = out["symbol"], out["name"]
        add("conclude", "BS 5930 coarse soil group", "results",
            tex=f"\\textbf{{{symbol}}}\\;:\\; \\text{{{name}}}",
            narration=f"BS 5930 keeps the same letters for coarse soils, "
                      f"so the group is {symbol}, {name.lower()}.",
            viz=[{"op": "highlight", "target": "fractions"}])
        return _package("BS 5930", symbol, name, gravel, sand, fines,
                        LL, PI)

    if LL is None:
        return {"error": "BS 5930 names a fine soil by its liquid limit "
                         "band, so LL is required (with PL or PI for the "
                         "clay or silt call)."}
    if PI is None and cue not in ("M", "C", "O"):
        return {"error": "The clay or silt call needs PI (or PL with "
                         "LL), or a field cue such as dilatancy or dry "
                         "strength."}

    if PI is not None:
        pi_a = 0.73 * (LL - 20.0)
        letter = "C" if PI >= pi_a else "M"
        add("lookup", "Clay or silt from the A-line", "chart",
            tex="PI_A = 0.73\\,(LL - 20)",
            sub=f"PI_A = 0.73\\,({LL:g} - 20) = {display_round(pi_a, 3):g}",
            narration=f"The point at LL = {LL:g}, PI = {PI:g} sits "
                      + ("above" if PI >= pi_a else "below")
                      + " the A-line, so the soil is a "
                      + ("clay." if PI >= pi_a else "silt."),
            viz=[{"op": "highlight", "target": "chart"}])
    else:
        letter = "C" if cue == "C" else "M"
        add("assume", "Clay or silt from the stated field cue", "chart",
            augmented=True,
            narration="No PI was given, so the field behavior stands "
                      "in: " + cue_why + ".",
            viz=[{"op": "highlight", "target": "chart"}])

    band = next(b for b in _BS_BAND if LL < b[1] or b[1] == float("inf"))
    band_letter, _, band_word = band
    add("lookup", "Plasticity band from the liquid limit", "chart",
        tex="LL < 35: L,\\; 35\\text{-}50: I,\\; 50\\text{-}70: H,\\; "
            "70\\text{-}90: V,\\; > 90: E",
        sub=f"LL = {LL:g} \\Rightarrow \\text{{{band_letter}}}",
        provenance=[{"symbol": "band " + band_letter, "value": band_word,
                     "means": "the BS plasticity range holding this LL",
                     "source": "BS 5930 fine-soil chart",
                     "arguments": [f"LL = {LL:g}"],
                     "whyApplies": "BS grades fine soils by liquid limit "
                                   "bands rather than a single split at "
                                   "50"}],
        narration=f"BS 5930 slices the LL axis into five bands; LL = "
                  f"{LL:g} falls in the {band_word} plasticity band, "
                  f"letter {band_letter}.",
        viz=[{"op": "highlight", "target": "chart"}])

    symbol = letter + band_letter
    kind = "Clay" if letter == "C" else "Silt"
    name = f"{kind} of {band_word} plasticity"
    add("conclude", "BS 5930 fine soil group", "results",
        tex=f"\\textbf{{{symbol}}}\\;:\\; \\text{{{name}}}",
        narration=f"Putting the two letters together: {symbol}, "
                  f"{name.lower()}.",
        viz=[{"op": "highlight", "target": "chart"}])
    return _package("BS 5930", symbol, name, gravel, sand, fines, LL, PI)


# ----------------------------------------------------------------------

def _package(system, symbol, name, gravel, sand, fines, LL, PI):
    return {
        "results": [],
        "conclusions": [
            {"quantity": "group_symbol", "value": symbol, "unit": "",
             "governing": system},
            {"quantity": "group_name", "value": name, "unit": "",
             "governing": system},
        ],
        "comparison": None,
        "figure": {
            "template": "classification",
            "system": system,
            "gravel": display_round(gravel, 3),
            "sand": display_round(sand, 3),
            "fines": display_round(fines, 3),
            "LL": None if LL is None else display_round(LL, 4),
            "PI": None if PI is None else display_round(PI, 4),
            "symbol": symbol,
            "name": name,
        },
    }
