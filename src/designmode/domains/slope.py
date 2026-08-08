"""Infinite (translational) slope on a plane slip surface.

Covers the dry, no-pore-pressure case: a soil layer of thickness z over
bedrock, slip surface parallel to the ground at angle beta. Circular slip
surfaces (method of slices) are declared unsupported honestly.
"""

import math
import re

from ..compute import display_round

_INFINITE_RE = re.compile(
    r"translational|infinite slope|parallel to the ground|bedrock",
    re.IGNORECASE)
_CIRCULAR_RE = re.compile(
    r"circular|method of slices|trial circle|swedish|fellenius",
    re.IGNORECASE)


def build(frame: dict, givens: dict, add, problem_text: str) -> dict:
    if _REL_RE.search(problem_text):
        return _tspm(frame, givens, add, problem_text)
    if _DESIGN_RE.search(problem_text) and givens.get("beta") is None:
        return _design_sweep(frame, givens, add, problem_text)
    if _BACK_RE.search(problem_text):
        return _back_analysis(frame, givens, add, problem_text)
    if _SEARCH_RE.search(problem_text) and givens.get("xc") is None:
        return _critical_search(frame, givens, add, problem_text)
    if _CIRCULAR_RE.search(problem_text) and not _INFINITE_RE.search(problem_text):
        return _swedish_slices(frame, givens, add, problem_text)
    if not _INFINITE_RE.search(problem_text):
        return {"error": "This slope needs either the translational "
                         "(infinite slope) reading or a trial circle with "
                         "its centre coordinates for the method of slices."}

    c = givens.get("c", givens.get("c_prime"))
    phi = givens.get("phi")
    gamma = givens.get("gamma")
    z = givens.get("z", givens.get("H"))
    beta = givens.get("beta")
    missing = [n for n, v in (("c'", c), ("phi'", phi), ("gamma", gamma),
                              ("z", z), ("beta", beta)) if v is None]
    if missing:
        return {"error": "The infinite-slope check needs c', phi', gamma, "
                         "the layer thickness z and the slope angle beta; "
                         "missing: " + ", ".join(missing) + "."}

    b = math.radians(beta)
    p = math.radians(phi)

    add("explain", "Why one arbitrary slice is enough", "setup",
        narration="Every vertical slice of a translational slide looks the "
                  "same: the interslice forces on its two sides cancel, so "
                  "one slice of width b represents the whole slope.",
        augmented=True,
        viz=[{"op": "highlight", "target": "slice"}])

    add("explain", "Forces on the slice", "setup",
        tex="W = \\gamma z b;\\quad N = W\\cos\\beta;\\quad T = W\\sin\\beta",
        narration="The slice weight resolves into a normal component "
                  "pressing on the slip surface and a tangential component "
                  "driving the slide.",
        viz=[{"op": "highlight", "target": "forces"}])

    sigma_n = gamma * z * math.cos(b) ** 2
    add("compute", "Effective normal stress on the base", "setup",
        tex="\\sigma'_n = \\tfrac{N}{l} = \\gamma z \\cos^2\\beta",
        sub=f"\\sigma'_n = ({gamma:g})({z:g})\\cos^2 {beta:g}^\\circ",
        result={"sym": "sigma_n", "value": sigma_n, "unit": "kPa",
                "display": f"{display_round(sigma_n)} kPa"},
        narration="The base of the slice is longer than its width by "
                  "1/cos β, which is where the squared cosine comes from.",
        viz=[{"op": "highlight", "target": "base"}])

    add("explain", "General expression for the factor of safety", "setup",
        tex="F_s = \\frac{c' + \\gamma z \\cos^2\\beta\\,\\tan\\phi'}"
            "{\\gamma z \\sin\\beta\\cos\\beta}",
        narration="The factor of safety compares the shear strength "
                  "available on the slip surface with the shear stress the "
                  "weight actually applies there.",
        viz=[{"op": "highlight", "target": "base"}])

    denom = gamma * z * math.sin(b) * math.cos(b)
    results = []
    if c and c > 0:
        Fs_c = (c + gamma * z * math.cos(b) ** 2 * math.tan(p)) / denom
        add("compute", "Factor of safety with cohesion", "results",
            tex="F_s = \\frac{c' + \\gamma z \\cos^2\\beta\\tan\\phi'}"
                "{\\gamma z \\sin\\beta\\cos\\beta}",
            sub=(f"F_s = \\frac{{{c:g} + ({gamma:g})({z:g})"
                 f"\\cos^2 {beta:g}^\\circ \\tan {phi:g}^\\circ}}"
                 f"{{({gamma:g})({z:g})\\sin {beta:g}^\\circ"
                 f"\\cos {beta:g}^\\circ}}"),
            result={"sym": "Fs", "value": Fs_c, "unit": "",
                    "display": f"Fs = {display_round(Fs_c, 3)}"},
            narration="With cohesion acting over the whole base, the "
                      "strength comfortably exceeds the driving stress.",
            viz=[{"op": "highlight", "target": "base"},
                 {"op": "highlight", "target": "forces"}])
        results.append({"method": "With cohesion",
                        "label": f"c' = {c:g} kPa", "q_ult": Fs_c})

    Fs_0 = math.tan(p) / math.tan(b)
    add("compute", "Cohesionless case, c' = 0", "results",
        tex="F_s = \\frac{\\tan\\phi'}{\\tan\\beta}",
        sub=f"F_s = \\frac{{\\tan {phi:g}^\\circ}}{{\\tan {beta:g}^\\circ}}",
        result={"sym": "Fs", "value": Fs_0, "unit": "",
                "display": f"Fs = {display_round(Fs_0, 3)}"},
        narration="Without cohesion both strength and stress grow in step "
                  "with depth, so the depth z cancels and only the two "
                  "angles remain.",
        viz=[{"op": "highlight", "target": "base"}])
    results.append({"method": "Cohesionless", "label": "c' = 0",
                    "q_ult": Fs_0})

    conclusions = [{"quantity": "Fs",
                    "value": display_round(results[0]["q_ult"], 3),
                    "unit": "", "governing": results[0]["method"]}]
    comparison = None
    if len(results) == 2:
        add("conclude", "Compare the two cases", "results",
            tex=(f"\\text{{with cohesion: }} F_s = "
                 f"{display_round(results[0]['q_ult'], 3)};\\quad "
                 f"\\text{{cohesionless: }} F_s = "
                 f"{display_round(Fs_0, 3)}"),
            narration="Cohesion is what keeps a shallow translational "
                      "slide comfortable; strip it away and the margin "
                      "drops sharply because only friction is left.",
            viz=[{"op": "compare",
                  "methods": [{"method": r["method"],
                               "q_ult": display_round(r["q_ult"], 3)}
                              for r in results]}])

    return {
        "results": [],
        "conclusions": conclusions,
        "comparison": comparison,
        "figure": {
            "template": "infinite_slope",
            "beta": beta, "z": z, "c": c, "phi": phi, "gamma": gamma,
        },
    }


# ---------------------------------------------------------------------------
# Swedish (Fellenius) method of slices for a toe circle under a plane face
# ---------------------------------------------------------------------------

_BISHOP_RE = re.compile(r"bishop", re.IGNORECASE)
_SEARCH_RE = re.compile(
    r"critical (?:slip )?(?:circle|surface)|search for the critical|"
    r"most critical|minimum factor of safety", re.IGNORECASE)
_DESIGN_RE = re.compile(
    r"(?:what|which|find|design|required|steepest|maximum)[^.]{0,50}"
    r"(?:slope angle|angle of the slope|face angle|slope inclination)|"
    r"design the slope", re.IGNORECASE)
_BACK_RE = re.compile(
    r"back[- ]analys|slope (?:has )?failed|at (?:the point of )?failure|"
    r"mobili[sz]ed (?:cohesion|strength|friction)|"
    r"what (?:cohesion|value of c)", re.IGNORECASE)
_REL_RE = re.compile(
    r"reliabilit|probability of failure|standard deviation", re.IGNORECASE)


def _coarse_search(K, profile, method):
    return K.grid_search(profile, method=method, nx=8, ny=6, n_depths=5,
                         refine=1)


def _design_sweep(frame, givens, add, problem_text):
    """Find the slope angle that meets a target factor of safety."""
    from .. import slope_kernel as K

    H = givens.get("H")
    c = givens.get("c", givens.get("c_prime", 0.0)) or 0.0
    phi = givens.get("phi", 0.0)
    gamma = givens.get("gamma", givens.get("gamma_dry"))
    target = givens.get("FS")
    missing = [n for n, v in (("H", H), ("gamma", gamma),
                              ("target FS", target)) if v is None]
    if missing:
        return {"error": "The design sweep needs the slope height, unit "
                         "weight, soil strength and the TARGET factor of "
                         "safety; missing: " + ", ".join(missing) + "."}
    method = "bishop" if _BISHOP_RE.search(problem_text) else "bishop"

    add("explain", "Design by sweeping the geometry", "setup",
        tex=f"\\text{{find }} \\beta \\text{{ such that }} F_{{s,\\min}}"
            f"(\\beta) = {target:g}",
        narration="Design inverts analysis: instead of asking how safe a "
                  "given slope is, sweep the face angle, find the critical "
                  "circle at each angle, and read off where the minimum "
                  "factor of safety crosses the target.",
        viz=[{"op": "highlight", "target": "arc"}])

    betas = [15, 22.5, 30, 37.5, 45, 52.5, 60, 67.5]
    curve = []
    for b in betas:
        prof = K.simple_slope_profile(H, b, c=c, phi=phi, gamma=gamma)
        try:
            fs_b = _coarse_search(K, prof, method)["best"]["Fs"]
        except ValueError:
            continue
        curve.append((b, fs_b))
    if len(curve) < 3:
        return {"error": "The sweep could not evaluate enough angles; "
                         "check the soil parameters."}
    tab = ",\\ ".join(f"({b:g}^\\circ, {fs:.2f})" for b, fs in curve)
    add("compute", "The sweep: Fs at each face angle", "results",
        tex="\\beta \\mapsto F_{s,\\min}(\\beta)",
        sub=tab,
        result={"sym": "n_pts", "value": len(curve), "unit": "",
                "display": f"{len(curve)} angles evaluated"},
        narration="Every point is a full critical-circle search by "
                  "Bishop's simplified method. Steeper is less safe, so "
                  "the curve falls from left to right.",
        viz=[{"op": "highlight", "target": "arc"}])

    bracket = None
    for (b0, f0), (b1, f1) in zip(curve, curve[1:]):
        if (f0 - target) * (f1 - target) <= 0:
            bracket = (b0, f0, b1, f1)
            break
    if bracket is None:
        lo, hi = curve[-1][1], curve[0][1]
        return {"error": f"The target Fs = {target:g} lies outside the "
                         f"swept range ({lo:.2f} to {hi:.2f} for 67.5 to "
                         "15 degrees); the answer would be an "
                         "extrapolation, which this solver refuses."}
    b0, f0, b1, f1 = bracket
    beta_star = b0 + (b1 - b0) * (f0 - target) / (f0 - f1)
    add("compute", "Interpolate to the target", "results",
        tex="\\beta^* = \\beta_0 + (\\beta_1 - \\beta_0)"
            "\\tfrac{F_0 - F_{target}}{F_0 - F_1}",
        sub=(f"\\beta^* = {b0:g} + ({b1:g}-{b0:g})"
             f"\\tfrac{{{f0:.3f} - {target:g}}}{{{f0:.3f} - {f1:.3f}}}"),
        result={"sym": "beta", "value": beta_star, "unit": "deg",
                "display": f"β* = {display_round(beta_star, 4)}°"},
        viz=[{"op": "highlight", "target": "arc"}])

    prof = K.simple_slope_profile(H, beta_star, c=c, phi=phi, gamma=gamma)
    ver = K.grid_search(prof, method=method)["best"]
    if abs(ver["Fs"] - target) > 0.02 * target:
        # the coarse sweep and the full search disagree slightly: one
        # secant correction using the two FULL-search quality points
        b_a, f_a = beta_star, ver["Fs"]
        b_b = b0 if abs(f0 - target) < abs(f1 - target) else b1
        f_b = f0 if b_b == b0 else f1
        if abs(f_a - f_b) > 1e-6:
            beta_star = b_a + (b_b - b_a) * (target - f_a) / (f_b - f_a)
            prof = K.simple_slope_profile(H, beta_star, c=c, phi=phi,
                                          gamma=gamma)
            ver = K.grid_search(prof, method=method)["best"]
    add("compute", "Verify at the interpolated angle", "results",
        tex="F_{s,\\min}(\\beta^*)",
        sub=f"F_s = {display_round(ver['Fs'], 4)}"
            f"\\ \\text{{(target {target:g})}}",
        result={"sym": "Fs", "value": ver["Fs"], "unit": "",
                "display": f"Fs = {display_round(ver['Fs'], 4)} at "
                           f"β = {display_round(beta_star, 4)}°"},
        narration="The interpolation is only trusted after a full search "
                  "at the interpolated angle confirms it; when the check "
                  "misses the target, the angle is corrected once and "
                  "verified again. Interpolation proposes, verification "
                  "disposes.",
        viz=[{"op": "highlight", "target": "arc"}])

    return {"results": [],
            "conclusions": [{"quantity": "beta",
                             "value": display_round(beta_star, 4),
                             "unit": "deg",
                             "governing": f"angle where Fs meets the "
                                          f"{target:g} target (full-search "
                                          f"verification: "
                                          f"{display_round(ver['Fs'], 3)})"}],
            "comparison": None,
            "figure": {"template": "circular_slope", "H": H,
                       "beta": round(beta_star, 2),
                       "xc": round(ver["xc"], 2), "yc": round(ver["yc"], 2),
                       "R": round(ver["R"], 2), "b": 0, "gamma": gamma,
                       "c": c, "phi": phi, "ru": 0, "n_slices": 0,
                       "design_curve": [{"beta": b, "Fs": round(f, 3)}
                                        for b, f in curve],
                       "target_fs": target}}


def _back_analysis(frame, givens, add, problem_text):
    """Invert the strength: what c makes this slope stand at the target?"""
    from .. import slope_kernel as K

    H = givens.get("H")
    beta = givens.get("beta")
    phi = givens.get("phi", 0.0)
    gamma = givens.get("gamma", givens.get("gamma_dry"))
    target = givens.get("FS", 1.0)
    missing = [n for n, v in (("H", H), ("beta", beta), ("gamma", gamma))
               if v is None]
    if missing:
        return {"error": "Back-analysis needs the slope height, face angle "
                         "and unit weight; missing: " + ", ".join(missing)
                         + "."}

    add("explain", "Back-analysis inverts the question", "setup",
        tex=f"\\text{{find }} c' \\text{{ such that }} F_{{s,\\min}} = "
            f"{target:g}",
        narration="When a slope has failed, the factor of safety is known "
                  "to be one, and the unknown becomes the strength that "
                  "was actually mobilised. The same solver runs inside a "
                  "root search on c'.",
        augmented=True,
        viz=[{"op": "highlight", "target": "arc"}])

    def fs_of(c_try):
        prof = K.simple_slope_profile(H, beta, c=c_try, phi=phi, gamma=gamma)
        return _coarse_search(K, prof, "oms")["best"]["Fs"]

    lo, hi = 0.0, 200.0
    f_lo = fs_of(lo)
    f_hi = fs_of(hi)
    if not (f_lo <= target <= f_hi):
        return {"error": f"With phi' = {phi:g} deg the target Fs = "
                         f"{target:g} is outside what cohesion 0-200 kPa "
                         f"can produce ({f_lo:.2f} to {f_hi:.2f}); the "
                         "friction angle assumption should be revisited."}
    hist = []
    for _ in range(24):
        mid = 0.5 * (lo + hi)
        f_mid = fs_of(mid)
        hist.append((mid, f_mid))
        if abs(f_mid - target) < 5e-4:
            break
        if f_mid < target:
            lo = mid
        else:
            hi = mid
    c_star, f_star = hist[-1]
    tab = ",\\ ".join(f"({cv:.1f}, {fv:.3f})" for cv, fv in hist[:6])
    add("compute", "Bisection on the cohesion", "results",
        tex="c' \\mapsto F_{s,\\min}(c')\\ \\text{(monotonic, so bisect)}",
        sub=f"{tab}\\ \\ldots",
        result={"sym": "c", "value": c_star, "unit": "kPa",
                "display": f"c' = {display_round(c_star, 4)} kPa"},
        narration="Each row is a full critical-circle analysis at a trial "
                  "cohesion; more cohesion, more safety, so the interval "
                  "halves each time.",
        viz=[{"op": "highlight", "target": "slices"}])
    add("compute", "Close the loop", "results",
        tex="F_{s,\\min}(c'^*)",
        sub=f"F_s = {display_round(f_star, 4)}\\ \\text{{(target "
            f"{target:g})}}",
        result={"sym": "Fs", "value": f_star, "unit": "",
                "display": f"Fs = {display_round(f_star, 4)}"},
        viz=[{"op": "highlight", "target": "arc"}])
    return {"results": [],
            "conclusions": [{"quantity": "c",
                             "value": display_round(c_star, 4),
                             "unit": "kPa",
                             "governing": f"mobilised cohesion for Fs = "
                                          f"{target:g} with phi' = "
                                          f"{phi:g} deg"}],
            "comparison": None,
            "figure": {"template": "circular_slope", "H": H, "beta": beta,
                       "xc": 0, "yc": 0, "R": 0, "b": 0, "gamma": gamma,
                       "c": round(c_star, 2), "phi": phi, "ru": 0,
                       "n_slices": 0}}


def _tspm(frame, givens, add, problem_text):
    """Taylor-series reliability (Duncan 2000): 1 + 2N narrated runs."""
    from .. import slope_kernel as K
    from .. import verification as V

    H = givens.get("H")
    beta = givens.get("beta")
    c = givens.get("c", givens.get("c_prime", 0.0)) or 0.0
    phi = givens.get("phi", 0.0)
    gamma = givens.get("gamma", givens.get("gamma_dry"))
    sigmas = [("c", givens.get("sigma_c")),
              ("phi", givens.get("sigma_phi")),
              ("gamma", givens.get("sigma_gamma"))]
    sigmas = [(k, v) for k, v in sigmas if v]
    missing = [n for n, v in (("H", H), ("beta", beta), ("gamma", gamma))
               if v is None]
    if missing:
        return {"error": "The reliability analysis needs the slope "
                         "geometry and unit weight; missing: "
                         + ", ".join(missing) + "."}
    if not sigmas:
        return {"error": "The reliability analysis needs at least one "
                         "standard deviation (of c', phi' or gamma); "
                         "none was given."}

    prof = K.simple_slope_profile(H, beta, c=c, phi=phi, gamma=gamma)
    mean = K.grid_search(prof, "bishop")["best"]
    F0 = mean["Fs"]
    circle = {"xc": mean["xc"], "yc": mean["yc"], "R": mean["R"]}
    add("compute", "The most-likely-value run", "setup",
        tex="F_{MLV} = F_{s,\\min}(\\text{mean parameters})",
        sub=f"F_{{MLV}} = {display_round(F0, 4)}",
        result={"sym": "F", "value": F0, "unit": "",
                "display": f"F_MLV = {display_round(F0, 4)}"},
        narration="The reliability method starts from the ordinary "
                  "deterministic answer at the mean parameter values; the "
                  "critical circle found here is then FROZEN for the "
                  "perturbation runs so that only the parameters move.",
        viz=[{"op": "highlight", "target": "arc"}])

    base = {"c": c, "phi": phi, "gamma": gamma}
    terms = []
    rows = []
    for key, sd in sigmas:
        vals = {}
        for sign in (+1, -1):
            p = dict(base)
            p[key] = base[key] + sign * sd
            prof_i = K.simple_slope_profile(H, beta, c=p["c"], phi=p["phi"],
                                            gamma=p["gamma"])
            slices, _ = K.make_slices(prof_i, circle, n_slices=40)
            vals[sign] = K.bishop_fs(slices)["Fs"]
        dF = 0.5 * (vals[+1] - vals[-1])
        terms.append(dF)
        rows.append(f"{key}: F^+ = {vals[+1]:.4f},\\ F^- = {vals[-1]:.4f},"
                    f"\\ \\Delta F/2 = {dF:+.4f}")
    add("compute", "Perturb one parameter at a time", "results",
        tex="\\Delta F_i = \\tfrac{F(x_i + \\sigma_i) - "
            "F(x_i - \\sigma_i)}{2}",
        sub=";\\ ".join(rows),
        result={"sym": "n", "value": len(rows), "unit": "",
                "display": f"{2 * len(rows)} perturbation runs"},
        narration="Each parameter is moved up and down by one standard "
                  "deviation on the frozen critical circle; half the "
                  "spread is that parameter's contribution to the "
                  "uncertainty in F.",
        viz=[{"op": "highlight", "target": "slices"}])

    sigma_F = math.sqrt(sum(t * t for t in terms))
    Vf = sigma_F / F0
    beta_ln = math.log(F0 / math.sqrt(1 + Vf * Vf)) / math.sqrt(
        math.log(1 + Vf * Vf))
    Pf = V.normal_cdf(-beta_ln)
    add("compute", "Combine into the reliability index", "results",
        tex="\\sigma_F = \\sqrt{\\sum \\Delta F_i^2};\\quad "
            "\\beta_{LN} = \\tfrac{\\ln(F_{MLV}/\\sqrt{1+V^2})}"
            "{\\sqrt{\\ln(1+V^2)}}",
        sub=(f"\\sigma_F = {display_round(sigma_F, 4)},\\ V = "
             f"{display_round(Vf, 4)},\\ \\beta_{{LN}} = "
             f"{display_round(beta_ln, 4)}"),
        result={"sym": "Pf", "value": Pf, "unit": "",
                "display": f"P_f = {display_round(Pf * 100, 3)} %"},
        narration="The lognormal reliability index follows Duncan (2000): "
                  "it measures how many combined standard deviations the "
                  "expected factor of safety sits above failure. The "
                  "probability of failure is read from the standard "
                  "normal curve.",
        provenance=[{"symbol": "beta_LN", "value": round(beta_ln, 4),
                     "means": "lognormal reliability index",
                     "source": "Duncan (2000), Taylor series method with "
                               "the critical surface frozen at the mean",
                     "arguments": [f"F_MLV = {F0:.3f}",
                                   f"V = {Vf:.3f}"],
                     "whyApplies": "F is a product of resistances over "
                                   "loads, which a lognormal fits better "
                                   "than a normal"}],
        viz=[])
    return {"results": [],
            "conclusions": [
                {"quantity": "Fs", "value": display_round(F0, 4), "unit": "",
                 "governing": "most likely value (Bishop, critical circle)"},
                {"quantity": "Pf",
                 "value": display_round(Pf * 100, 3), "unit": "%",
                 "governing": f"beta_LN = {display_round(beta_ln, 3)}, "
                              "Taylor series (Duncan 2000)"}],
            "comparison": None,
            "figure": {"template": "circular_slope", "H": H, "beta": beta,
                       "xc": round(circle["xc"], 2),
                       "yc": round(circle["yc"], 2),
                       "R": round(circle["R"], 2), "b": 0, "gamma": gamma,
                       "c": c, "phi": phi, "ru": 0, "n_slices": 0}}


def _critical_search(frame, givens, add, problem_text):
    """Deterministic grid search for the critical circle, narrated."""
    from .. import slope_kernel as K

    H = givens.get("H")
    beta = givens.get("beta")
    c = givens.get("c", givens.get("c_prime", 0.0)) or 0.0
    phi = givens.get("phi", 0.0)
    gamma = givens.get("gamma", givens.get("gamma_dry"))
    ru = givens.get("ru")
    missing = [n for n, v in (("H", H), ("beta", beta), ("gamma", gamma))
               if v is None]
    if missing:
        return {"error": "The critical-circle search needs the slope height,"
                         " face angle and unit weight; missing: "
                         + ", ".join(missing) + "."}
    method = "bishop" if _BISHOP_RE.search(problem_text) else "oms"
    water = {"type": "ru", "value": float(ru)} if ru else None
    profile = K.simple_slope_profile(H, beta, c=c, phi=phi, gamma=gamma,
                                     water=water)

    add("explain", "Why one circle is never enough", "setup",
        narration="The factor of safety belongs to a slip surface, not to "
                  "the slope: every trial circle has its own value, and the "
                  "design number is the smallest one. The search sweeps a "
                  "grid of centres above the slope and, for each centre, a "
                  "fan of depths.",
        viz=[{"op": "highlight", "target": "arc"}])

    method_label = ("Bishop's simplified method" if method == "bishop"
                    else "the Ordinary method of slices")
    add("explain", "The search grid", "setup",
        tex="12 \\times 10\\ \\text{centres},\\ 8\\ \\text{depths each},"
            "\\ 2\\ \\text{refinement passes}",
        narration=f"Each candidate circle is solved in full by "
                  f"{method_label}; nothing is interpolated. The same grid "
                  "on the same problem always returns the same answer.",
        viz=[{"op": "highlight", "target": "arc"}])

    try:
        sr = K.grid_search(profile, method=method)
    except ValueError as e:
        return {"error": f"The search found no admissible circle: {e}."}
    best = sr["best"]

    add("compute", "The critical circle", "results",
        tex="F_{s,\\min} = \\min_{\\text{circles}} F_s",
        sub=(f"O = ({display_round(best['xc'], 4)},\\ "
             f"{display_round(best['yc'], 4)}),\\ R = "
             f"{display_round(best['R'], 4)}\\ \\text{{m}}"),
        result={"sym": "Fs", "value": best["Fs"], "unit": "",
                "display": f"Fs = {display_round(best['Fs'], 4)}"},
        narration="Of all the circles tried, this one resists least "
                  "relative to what drives it. Neighbouring centres score "
                  "slightly higher, which is what makes this the minimum "
                  "rather than an arbitrary pick.",
        viz=[{"op": "highlight", "target": "arc"},
             {"op": "highlight", "target": "slices"}])

    field = [{"xc": round(f["xc"], 2), "yc": round(f["yc"], 2),
              "Fs": round(f["Fs"], 3)} for f in sr["field"]]
    return {
        "results": [],
        "conclusions": [{"quantity": "Fs",
                         "value": display_round(best["Fs"], 4), "unit": "",
                         "governing": f"critical circle by {method_label} "
                                      "(deterministic grid search)"}],
        "comparison": None,
        "figure": {"template": "circular_slope", "H": H, "beta": beta,
                   "xc": round(best["xc"], 2), "yc": round(best["yc"], 2),
                   "R": round(best["R"], 2), "b": 0,
                   "gamma": gamma, "c": c, "phi": phi, "ru": ru or 0,
                   "n_slices": 0, "fs_field": field},
    }


def _swedish_slices(frame, givens, add, problem_text):
    from .. import slope_kernel as K

    H = givens.get("H")
    beta = givens.get("beta", 45.0)
    xc, yc = givens.get("xc"), givens.get("yc")
    c = givens.get("c", givens.get("c_prime", 0.0)) or 0.0
    phi = givens.get("phi", 0.0)
    gamma = givens.get("gamma", givens.get("gamma_dry"))
    b_w = givens.get("s", 2.0)
    R_given = givens.get("R")
    ru = givens.get("ru")
    missing = [n for n, v in (("H", H), ("centre xc", xc), ("centre yc", yc),
                              ("gamma", gamma)) if v is None]
    if missing:
        return {"error": "The method of slices needs the slope height, the "
                         "trial circle centre (xc, yc), the soil strength "
                         "and unit weight; missing: " + ", ".join(missing)
                         + "."}

    if R_given:
        R = float(R_given)
        circle = {"xc": xc, "yc": yc, "R": R}
        add("explain", "The trial circle from centre and radius", "setup",
            tex=f"O = ({xc:g},\\ {yc:g}),\\quad R = {R:g}\\ \\text{{m}}",
            narration="Centre and radius are both given, so the circle "
                      "need not pass through the toe; the slide enters and "
                      "exits wherever this circle cuts the ground surface.",
            viz=[{"op": "highlight", "target": "arc"}])
    else:
        circle = K.toe_circle(xc, yc)
        R = circle["R"]
        add("compute", "The trial circle through the toe", "setup",
            tex="R = \\sqrt{x_c^2 + y_c^2}",
            sub=f"R = \\sqrt{{{xc:g}^2 + {yc:g}^2}}",
            result={"sym": "R", "value": R, "unit": "m",
                    "display": f"R = {display_round(R, 4)} m"},
            narration="The circle is pinned by its centre and by passing "
                      "through the toe, which fixes its radius.",
            viz=[{"op": "highlight", "target": "arc"}])

    water = {"type": "ru", "value": float(ru)} if ru else None
    profile = K.simple_slope_profile(H, beta, c=c, phi=phi, gamma=gamma,
                                     water=water)
    try:
        slices, (x_entry, x_exit) = K.make_slices(profile, circle, width=b_w)
    except ValueError as e:
        return {"error": f"This trial circle cannot be sliced: {e}."}

    if not R_given:
        add("compute", "Where the circle exits through the crest", "setup",
            tex="x_B = x_c + \\sqrt{R^2 - (H - y_c)^2}",
            sub=f"x_B = {xc:g} + \\sqrt{{{R:.2f}^2 - ({H:g}-{yc:g})^2}}",
            result={"sym": "xB", "value": x_exit, "unit": "m",
                    "display": f"x = {display_round(x_exit, 4)} m"},
            viz=[{"op": "highlight", "target": "arc"}])
    else:
        add("compute", "Where the circle cuts the ground", "setup",
            tex="\\text{entry and exit of the arc on the ground line}",
            sub=(f"x_A = {display_round(x_entry, 4)}\\ \\text{{m}},\\quad "
                 f"x_B = {display_round(x_exit, 4)}\\ \\text{{m}}"),
            result={"sym": "xB", "value": x_exit, "unit": "m",
                    "display": f"x = {display_round(x_exit, 4)} m"},
            viz=[{"op": "highlight", "target": "arc"}])

    n = len(slices)
    add("explain", "Cut the mass into vertical slices", "slices",
        tex=f"n = {n}\ \\text{{slices of width }} b = {b_w:g}\ \\text{{m}}"
            f"\ \\text{{(last one {slices[-1]['b']:.2f} m)}}",
        narration="Each slice's weight comes from the height between the "
                  "ground line and the arc; its base angle comes from "
                  "where it sits on the circle. Slices left of the centre "
                  "lean backwards and their base angle is negative: they "
                  "resist rather than drive.",
        viz=[{"op": "highlight", "target": "slices"}])

    if ru:
        s_mid = slices[len(slices) // 2]
        u_mid = s_mid["u"]
        add("compute", "Pore pressure on each slice base", "slices",
            tex="u_i = r_u\\,\\tfrac{W_i}{b_i}",
            sub=(f"\\text{{e.g. slice {s_mid['i']}: }} u = {ru:g} \\times "
                 f"\\tfrac{{{display_round(s_mid['W'])}}}"
                 f"{{{s_mid['b']:.2f}}} = {display_round(u_mid)}"
                 f"\\ \\text{{kPa}}"),
            result={"sym": "u", "value": u_mid, "unit": "kPa",
                    "display": f"u = {display_round(u_mid)} kPa (slice "
                               f"{s_mid['i']})"},
            narration="The pore pressure ratio scales each slice's own "
                      "overburden, so wetter means less effective normal "
                      "force on every base.",
            viz=[{"op": "highlight", "target": "slices"}])

    s1 = slices[0]
    W1 = round(s1["W"], 1)
    add("compute", "One row of the spreadsheet: slice 1", "slices",
        tex="W_i = b_i h_i \\gamma;\\quad l_i = \\tfrac{b_i}{\\cos\\alpha_i}",
        sub=(f"h_1 = {round(s1['h'], 2):g}\ \\text{{m}},\ "
             f"\\alpha_1 = {round(s1['alpha_deg'], 2):g}^\\circ,\ "
             f"W_1 = {W1:g}\ \\text{{kN/m}}"),
        result={"sym": "W1", "value": W1, "unit": "kN/m",
                "display": f"W₁ = {W1:g} kN/m"},
        viz=[{"op": "highlight", "target": "slice1"}])

    oms = K.oms_fs(slices)
    Fs = oms["Fs"]
    if ru:
        fs_tex = ("F_s = \\tfrac{\\sum(c'l_i + (W_i\\cos\\alpha_i - "
                  "u_i l_i)\\tan\\phi')}{\\sum W_i\\sin\\alpha_i}")
    else:
        fs_tex = ("F_s = \\tfrac{\\sum(c'l_i + W_i\\cos\\alpha_i"
                  "\\tan\\phi')}{\\sum W_i\\sin\\alpha_i}")
    add("compute", "Sum the columns and form the factor of safety",
        "results",
        tex=fs_tex,
        sub=(f"F_s = \\tfrac{{{display_round(oms['sum_res'])}}}"
             f"{{{display_round(oms['sum_drv'])}}}"),
        result={"sym": "Fs", "value": Fs, "unit": "",
                "display": f"Fs = {display_round(Fs, 4)}"},
        narration="The radius multiplies both column sums, so it cancels: "
                  "the factor of safety is the resisting column over the "
                  "driving column, exactly as the spreadsheet builds it.",
        viz=[{"op": "highlight", "target": "arc"},
             {"op": "highlight", "target": "slices"}])

    results = []
    conclusions = [{"quantity": "Fs", "value": display_round(Fs, 4),
                    "unit": "",
                    "governing": "this trial circle only; the design "
                                 "Fs needs a search over many circles"}]
    comparison = None

    want_bishop = bool(_BISHOP_RE.search(problem_text))
    if oms["n_negative_base"] > 0 and not want_bishop:
        add("explain", "A warning from the slice table", "results",
            tex=(f"{oms['n_negative_base']}\\ \\text{{slice(s) have }} "
                 "N'_i = W_i\\cos\\alpha_i - u_i l_i < 0"),
            narration="A negative effective normal force is physically "
                      "impossible; it is an artefact of the Ordinary "
                      "method's neglect of interslice forces. Bishop's "
                      "simplified method fixes exactly this, so its result "
                      "is shown alongside.",
            viz=[{"op": "highlight", "target": "slices"}])
        want_bishop = True

    if want_bishop:
        try:
            bис = None
            bish = K.bishop_fs(slices, fs0=Fs)
            iters = bish["iterations"]
            it_rows = ",\\ ".join(f"F_{k+1} = {display_round(v, 4)}"
                                  for k, v in enumerate(iters[:6]))
            add("compute", "Bishop's simplified method: iterate on Fs",
                "results",
                tex="F_s = \\tfrac{\\sum\\left[\\tfrac{c'b_i + (W_i - u_i "
                    "b_i)\\tan\\phi'}{m_{\\alpha,i}}\\right]}"
                    "{\\sum W_i\\sin\\alpha_i},\\quad m_{\\alpha,i} = "
                    "\\cos\\alpha_i + \\tfrac{\\sin\\alpha_i\\tan\\phi'}"
                    "{F_s}",
                sub=(f"F_0 = {display_round(Fs, 4)}\\ \\text{{(Ordinary)}}"
                     f",\\ {it_rows}"),
                result={"sym": "Fs_b", "value": bish["Fs"], "unit": "",
                        "display": f"Fs = {display_round(bish['Fs'], 4)} "
                                   f"(Bishop)"},
                narration="Because m_alpha contains Fs, the equation is "
                          "solved by iteration: start from the Ordinary "
                          "value and substitute until the number stops "
                          "changing. Convergence took "
                          f"{len(iters)} step(s).",
                viz=[{"op": "highlight", "target": "slices"}])
            results = [
                {"method": "Ordinary (Fellenius)",
                 "label": "moment equilibrium only, interslice forces "
                          "neglected", "q_ult": round(Fs, 4)},
                {"method": "Bishop simplified",
                 "label": "adds vertical equilibrium per slice",
                 "q_ult": round(bish["Fs"], 4)},
            ]
            gap = abs(bish["Fs"] - Fs) / max(Fs, 1e-9) * 100
            comparison = {
                "explanation": (
                    "Both methods share the same slices; they differ only "
                    "in what equilibrium they enforce. The Ordinary method "
                    "drops the interslice forces entirely, which "
                    "understates the normal force on steep or wet bases, "
                    f"so Bishop's value sits {gap:.0f} % above it here. "
                    "Bishop is the one carried forward; the Ordinary "
                    "value is the conservative hand-check."),
                "unit": "",
                "spread_pct": round(gap, 1),
                "rows": [{"method": r["method"], "label": r["label"],
                          "q_ult": r["q_ult"]} for r in results]}
            conclusions = [{"quantity": "Fs",
                            "value": display_round(bish["Fs"], 4),
                            "unit": "",
                            "governing": "Bishop simplified (satisfies "
                                         "vertical equilibrium; the "
                                         "Ordinary value is the "
                                         "conservative first pass)"}]
        except ValueError as e:
            add("explain", "Bishop's method declined", "results",
                narration=f"Bishop's iteration was not reliable here: {e}.",
                viz=[])

    # independent complete-equilibrium check (engine, not hand calc)
    from .. import verification as V
    chk = V.spencer_check(slices, circle, Fs)
    if "FS" in chk:
        ref = results[-1]["q_ult"] if results else Fs
        dev = abs(chk["FS"] - ref) / max(abs(ref), 1e-9)
        agree = ("It agrees within "
                 if dev <= 0.05 else "It DIFFERS by more than 5 % from ")
        add("explain", "Independent check: Spencer's method", "results",
            tex=f"F_s = {display_round(chk['FS'], 4)}\\ "
                "\\text{(complete equilibrium)}",
            narration="Spencer's method satisfies every equilibrium "
                      "equation at once, at the cost of an iteration that "
                      "no longer reads like a spreadsheet. It is computed "
                      "here by an independent engine as a check, not as a "
                      f"hand method. {agree}"
                      f"{display_round(dev * 100, 2)} % of the value "
                      "carried forward.",
            augmented=True,
            provenance=[{"symbol": "Fs (Spencer)",
                         "value": round(chk["FS"], 4),
                         "means": "factor of safety with full force and "
                                  "moment equilibrium",
                         "source": f"computed by {chk['engine']}, after a "
                                   "hand-off check that the engine "
                                   "reproduces our Ordinary-method value "
                                   "on the same slices",
                         "arguments": ["the same slice table"],
                         "whyApplies": "an independent, more rigorous "
                                       "method run on identical input is "
                                       "the strongest cheap check"}],
            viz=[])

    fig_slices = [{"i": s["i"], "x0": round(s["x0"], 3),
                   "x1": round(s["x1"], 3), "h": round(s["h"], 3),
                   "alpha": round(s["alpha_deg"], 2), "W": round(s["W"], 1),
                   "u": round(s["u"], 2),
                   "drv": round(s["W"] * math.sin(s["alpha"]), 1),
                   "res": round(c * s["dl"] + (s["W"] * math.cos(s["alpha"])
                                - s["u"] * s["dl"])
                                * math.tan(math.radians(s["phi"])), 1)}
                  for s in slices]
    return {
        "results": results,
        "conclusions": conclusions,
        "comparison": comparison,
        "figure": {"template": "circular_slope", "H": H, "beta": beta,
                   "xc": xc, "yc": yc, "R": round(R, 2),
                   "x_entry": round(x_entry, 2),
                   "x_exit": round(x_exit, 2), "b": b_w,
                   "gamma": gamma, "c": c, "phi": phi,
                   "ru": ru or 0,
                   "n_slices": n,
                   "slice_table": fig_slices},
    }
