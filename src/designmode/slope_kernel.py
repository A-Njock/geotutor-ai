"""Pure slope-stability kernel: geometry, slicing, OMS and Bishop.

No narration, no LLM, no I/O — fast enough to sit inside a critical-circle
search. The narrated step chains in domains/slope.py are wrappers that call
this kernel and explain each number it produces.

Formulations mirror xslope 0.2.1 solve.py (oms, bishop) restricted to slice
weight + pore pressure, so factors of safety are directly comparable with the
xslope benchmark corpus:
    OMS:    Fs = sum(c dl + (W cos(a) - u dl) tan(phi)) / sum(W sin(a))
    Bishop: Fs = sum([c b + (W - u b) tan(phi)] / m_a) / sum(W sin(a)),
            m_a = cos(a) + sin(a) tan(phi) / Fs   (iterated)

Model contract (plain dicts, all SI: m, kN/m^3, kPa, degrees):
    profile = {
      "ground":  [(x, y), ...]            ascending x, piecewise linear
      "layers":  [ {"c":, "phi":, "gamma":, "gamma_sat": optional,
                    "bottom": [(x, y), ...] or None}, ... ]  top to bottom;
                 the last layer's bottom may be None (extends down forever)
      "water":   {"type": "none"}
               | {"type": "ru",    "value": ru}
               | {"type": "piezo", "line": [(x, y), ...]}
    }
    circle  = {"xc":, "yc":, "R":}
GAMMA_W = 9.81 unless a problem states 9.8/10 (pass gamma_w explicitly).
"""

import math

GAMMA_W = 9.81


# ---------------------------------------------------------------------------
# geometry helpers
# ---------------------------------------------------------------------------

def interp(poly, x):
    """Piecewise-linear interpolation on [(x, y), ...]; clamps beyond ends."""
    if x <= poly[0][0]:
        return poly[0][1]
    if x >= poly[-1][0]:
        return poly[-1][1]
    for (x0, y0), (x1, y1) in zip(poly, poly[1:]):
        if x0 <= x <= x1:
            if x1 == x0:
                return y1
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return poly[-1][1]


def arc_y(circle, x):
    """Lower branch of the trial circle at x (None outside the circle)."""
    dx = x - circle["xc"]
    s = circle["R"] ** 2 - dx * dx
    if s < 0:
        return None
    return circle["yc"] - math.sqrt(s)


def circle_ground_intersections(ground, circle, samples=2000):
    """The two x where the arc's lower branch meets the ground surface.

    Scans f(x) = ground(x) - arc(x) over the arc's footprint for sign
    changes, then bisects. Returns (x_left, x_right) or None if the arc
    does not cut the ground in two points.
    """
    xc, R = circle["xc"], circle["R"]
    lo = max(xc - R, ground[0][0])
    hi = min(xc + R, ground[-1][0])
    if hi <= lo:
        return None

    def f(x):
        a = arc_y(circle, x)
        if a is None:
            return None
        return ground_y(ground, x) - a

    def ground_y(g, x):
        return interp(g, x)

    xs = [lo + (hi - lo) * i / samples for i in range(samples + 1)]
    roots = []
    prev_x, prev_f = None, None
    for x in xs:
        fx = f(x)
        if fx is None:
            prev_x, prev_f = None, None
            continue
        if prev_f is not None and (prev_f == 0 or (prev_f > 0) != (fx > 0)):
            a, b = prev_x, x
            fa = prev_f
            for _ in range(80):
                m = 0.5 * (a + b)
                fm = f(m)
                if fm is None:
                    break
                if (fa > 0) != (fm > 0):
                    b = m
                else:
                    a, fa = m, fm
            roots.append(0.5 * (a + b))
        prev_x, prev_f = x, fx
    # dedupe near-identical roots
    ded = []
    for r in roots:
        if not ded or abs(r - ded[-1]) > 1e-6 * max(1.0, R):
            ded.append(r)
    if len(ded) < 2:
        # a circle that exits exactly at a profile endpoint (e.g. through the
        # toe at the very start of the ground line) touches f = 0 there
        # without a sign change — accept near-zero endpoints as roots
        eps = 1e-6 * max(1.0, R)
        for xe in (lo, hi):
            fe = f(xe)
            if fe is not None and abs(fe) < eps:
                if not any(abs(xe - r) < eps for r in ded):
                    ded.append(xe)
        ded.sort()
    if len(ded) < 2:
        return None
    return ded[0], ded[-1]


def _layer_at(profile, x, y):
    """Index of the layer containing point (x, y)."""
    for i, lay in enumerate(profile["layers"]):
        bot = lay.get("bottom")
        if bot is None or y >= interp(bot, x):
            return i
    return len(profile["layers"]) - 1


def _column_weight(profile, x, y_bot, y_top):
    """Weight per unit width of the soil column between y_bot and y_top at x.

    Total unit weights (buoyancy is handled through pore pressure u); below
    the piezometric line a layer's gamma_sat is used when it declares one.
    """
    if y_top <= y_bot:
        return 0.0
    water = profile.get("water") or {"type": "none"}
    y_wt = None
    if water.get("type") == "piezo" and water.get("line"):
        y_wt = interp(water["line"], x)
    w = 0.0
    y_hi = y_top
    for lay in profile["layers"]:
        bot = lay.get("bottom")
        y_lo = interp(bot, x) if bot is not None else -1e9
        y_lo = max(y_lo, y_bot)
        if y_lo < y_hi:
            g_moist = lay["gamma"]
            g_sat = lay.get("gamma_sat") or g_moist
            if y_wt is None or y_wt >= y_hi:
                g = g_sat if y_wt is not None else g_moist
                w += g * (y_hi - y_lo)
            elif y_wt <= y_lo:
                w += g_moist * (y_hi - y_lo)
            else:
                w += g_moist * (y_hi - y_wt) + g_sat * (y_wt - y_lo)
            y_hi = y_lo
        if y_hi <= y_bot:
            break
    return w


def _phreatic_cos2(line, x):
    """cos^2 of the local piezometric-line slope (XSTABL/Slide 'Hu: auto'
    correction for steady seepage parallel to an inclined phreatic line)."""
    if not line or len(line) < 2:
        return 1.0
    for (x0, y0), (x1, y1) in zip(line, line[1:]):
        if x0 <= x <= x1 and x1 > x0:
            m = (y1 - y0) / (x1 - x0)
            return 1.0 / (1.0 + m * m)
    return 1.0


def _pore_u(profile, layer, x, y_base, w_over_b, gamma_w):
    """Pore pressure on the slice base at (x, y_base).

    The base layer's own "u_mode" wins (matching per-material pore-pressure
    options: none / ru / piezo); a global profile["water"] applies to layers
    that do not declare one.
    """
    water = profile.get("water") or {"type": "none"}
    mode = layer.get("u_mode")
    if mode is None:
        mode = water.get("type", "none")
    if mode == "none":
        return 0.0
    if mode == "ru":
        r = layer.get("ru") if layer.get("ru") is not None \
            else water.get("value", 0.0)
        return r * w_over_b
    if mode == "piezo":
        line = water.get("line")
        if not line:
            raise ValueError("a layer asks for piezometric pore pressure "
                             "but no piezometric line is given")
        head = interp(line, x) - y_base
        u = gamma_w * max(head, 0.0)
        if water.get("phreatic"):
            u *= _phreatic_cos2(line, x)
        return u
    raise ValueError(f"unknown pore-pressure mode {mode}")


# ---------------------------------------------------------------------------
# slicing
# ---------------------------------------------------------------------------

def _mirror_poly(poly):
    return [(-x, y) for x, y in reversed(poly)]


def mirror_profile(profile):
    """Reflect the model about x = 0 so a right-facing slope becomes the
    left-facing one the solvers expect. Fs is invariant under this."""
    out = {"ground": _mirror_poly(profile["ground"]),
           "layers": [dict(lay, bottom=(_mirror_poly(lay["bottom"])
                                        if lay.get("bottom") else None))
                      for lay in profile["layers"]]}
    w = profile.get("water") or {"type": "none"}
    if w.get("type") == "piezo":
        w = {"type": "piezo", "line": _mirror_poly(w["line"])}
    out["water"] = w
    return out


def is_right_facing(profile):
    """True when the ground is higher on the left (slide moves rightward)."""
    g = profile["ground"]
    return g[0][1] > g[-1][1]


def make_slices(profile, circle, width=None, n_slices=None, gamma_w=GAMMA_W):
    """Cut the sliding mass into vertical slices.

    Heights are the average of the two edge heights (trapezoid rule), the
    base angle comes from the circle at the slice midline, and the base
    strength/pore pressure are evaluated at the midline. Right-facing
    slopes (higher ground on the left) are mirrored internally so the
    driving direction is always consistent; Fs is unaffected. Returns a
    list of slice dicts and the (x_left, x_right) span in the ORIGINAL
    coordinates, or raises ValueError with a named reason.
    """
    if is_right_facing(profile):
        mirrored, span = make_slices(
            mirror_profile(profile),
            {"xc": -circle["xc"], "yc": circle["yc"], "R": circle["R"]},
            width=width, n_slices=n_slices, gamma_w=gamma_w)
        for s in mirrored:
            s["x0"], s["x1"] = -s["x1"], -s["x0"]
            s["xm"] = -s["xm"]
            s["mirrored"] = True
        mirrored.reverse()
        for k, s in enumerate(mirrored):
            s["i"] = k + 1
        return mirrored, (-span[1], -span[0])
    span = circle_ground_intersections(profile["ground"], circle)
    if span is None:
        raise ValueError("the trial circle does not cut the ground surface "
                         "in two points; check centre and radius")
    xl, xr = span
    if width is None and n_slices is None:
        n_slices = 40
    if width is not None:
        edges = []
        x = xl
        while x < xr - 1e-9:
            edges.append(x)
            x += width
        edges.append(xr)
    else:
        edges = [xl + (xr - xl) * i / n_slices for i in range(n_slices + 1)]

    R, xc = circle["R"], circle["xc"]
    slices = []
    for i in range(len(edges) - 1):
        x0, x1 = edges[i], edges[i + 1]
        b = x1 - x0
        if b <= 0:
            continue
        xm = 0.5 * (x0 + x1)
        y_base = arc_y(circle, xm)
        if y_base is None:
            continue
        a0 = arc_y(circle, x0)
        a1 = arc_y(circle, x1)
        a0 = y_base if a0 is None else a0
        a1 = y_base if a1 is None else a1
        h0 = interp(profile["ground"], x0) - a0
        h1 = interp(profile["ground"], x1) - a1
        y_top = interp(profile["ground"], xm)
        # weight: trapezoid of the edge column weights
        w0 = _column_weight(profile, x0, a0, interp(profile["ground"], x0))
        w1 = _column_weight(profile, x1, a1, interp(profile["ground"], x1))
        w_over_b = 0.5 * (w0 + w1)
        W = w_over_b * b
        sin_a = max(min((xm - xc) / R, 1.0), -1.0)
        alpha = math.asin(sin_a)
        dl = b / math.cos(alpha)
        li = _layer_at(profile, xm, y_base + 1e-6)
        lay = profile["layers"][li]
        u = _pore_u(profile, lay, xm, y_base, w_over_b, gamma_w)
        slices.append({
            "i": i + 1, "x0": x0, "x1": x1, "xm": xm, "b": b,
            "h": 0.5 * (h0 + h1), "y_base": y_base, "y_top": y_top,
            "y_lt": interp(profile["ground"], x0),
            "y_rt": interp(profile["ground"], x1),
            "y_lb": a0, "y_rb": a1,
            "alpha": alpha, "alpha_deg": math.degrees(alpha), "dl": dl,
            "W": W, "u": u, "c": lay["c"], "phi": lay["phi"], "layer": li,
        })
    if not slices:
        raise ValueError("no slices could be formed inside the circle span")
    return slices, (xl, xr)


# ---------------------------------------------------------------------------
# limit-equilibrium methods
# ---------------------------------------------------------------------------

def _auto_orient(slices):
    """If the total driving term is negative, the slide direction is the
    mirror of the assumed one: flip every base angle once. Fs is invariant
    under mirroring, so this only fixes the sign convention."""
    den = sum(s["W"] * math.sin(s["alpha"]) for s in slices)
    if den >= 0:
        return slices
    return [dict(s, alpha=-s["alpha"], alpha_deg=-s["alpha_deg"])
            for s in slices]


def oms_fs(slices):
    """Ordinary Method of Slices (Fellenius), xslope-compatible form."""
    slices = _auto_orient(slices)
    num = 0.0
    den = 0.0
    n_neg = 0
    rows = []
    for s in slices:
        tan_phi = math.tan(math.radians(s["phi"]))
        n_eff = s["W"] * math.cos(s["alpha"]) - s["u"] * s["dl"]
        if n_eff < 0:
            n_neg += 1
        res = s["c"] * s["dl"] + n_eff * tan_phi
        drv = s["W"] * math.sin(s["alpha"])
        num += res
        den += drv
        rows.append({**s, "n_eff": n_eff, "res": res, "drv": drv})
    if den <= 0:
        raise ValueError("driving moment is not positive; the trial circle "
                         "does not describe a slide in this direction")
    return {"method": "oms", "Fs": num / den, "sum_res": num, "sum_drv": den,
            "n_negative_base": n_neg, "rows": rows}


def bishop_fs(slices, tol=1e-6, max_iter=100, fs0=None):
    """Bishop's simplified method with the iteration history kept for
    narration. Starts from the OMS value unless fs0 is given."""
    slices = _auto_orient(slices)
    den = sum(s["W"] * math.sin(s["alpha"]) for s in slices)
    if den <= 0:
        raise ValueError("driving moment is not positive")
    fs = fs0 if fs0 is not None else oms_fs(slices)["Fs"]
    history = []
    converged = False
    for _ in range(max_iter):
        num = 0.0
        for s in slices:
            tan_phi = math.tan(math.radians(s["phi"]))
            m_a = math.cos(s["alpha"]) + math.sin(s["alpha"]) * tan_phi / fs
            if m_a <= 0.05:
                # steep-base pathology: m_alpha near zero blows the term up
                raise ValueError("Bishop's m_alpha fell below 0.05 on a "
                                 "steep slice base; result would be "
                                 "unreliable for this circle")
            num += (s["c"] * s["b"] + (s["W"] - s["u"] * s["b"]) * tan_phi) / m_a
        fs_new = num / den
        history.append(fs_new)
        if abs(fs_new - fs) < tol:
            converged = True
            fs = fs_new
            break
        fs = fs_new
    return {"method": "bishop", "Fs": fs, "sum_drv": den,
            "iterations": history, "converged": converged}


# ---------------------------------------------------------------------------
# convenience: simple slope profiles and toe circles (legacy contract)
# ---------------------------------------------------------------------------

def simple_slope_profile(H, beta_deg, c, phi, gamma, crest_run=None,
                         toe_run=None, water=None):
    """Toe at the origin, face rising at beta to height H, horizontal crest.
    Reproduces the original narrated geometry exactly."""
    tb = math.tan(math.radians(beta_deg))
    x_top = H / tb
    crest_run = crest_run if crest_run is not None else max(4 * H, 40.0)
    toe_run = toe_run if toe_run is not None else max(2 * H, 20.0)
    ground = [(-toe_run, 0.0), (0.0, 0.0), (x_top, H), (x_top + crest_run, H)]
    return {"ground": ground,
            "layers": [{"c": c, "phi": phi, "gamma": gamma, "bottom": None}],
            "water": water or {"type": "none"}}


def toe_circle(xc, yc):
    """Circle through the origin-toe: the legacy (xc, yc) contract."""
    return {"xc": xc, "yc": yc, "R": math.hypot(xc, yc)}


# ---------------------------------------------------------------------------
# critical-circle grid search (deterministic)
# ---------------------------------------------------------------------------

def grid_search(profile, method="bishop", nx=12, ny=10, n_depths=8,
                width=None, n_slices=40, refine=2):
    """Deterministic critical-circle search: rectangular centre grid above
    the slope, tangent-depth sweep per centre, then fixed-ratio refinement
    around the running minimum. Returns the best result and the FS field
    for visualisation. No randomness: same inputs, same answer."""
    g = profile["ground"]
    x_min, x_max = g[0][0], g[-1][0]
    y_min = min(y for _, y in g)
    y_max = max(y for _, y in g)
    H = max(y_max - y_min, 1.0)
    box = [x_min + 0.1 * (x_max - x_min), x_max - 0.1 * (x_max - x_min),
           y_max + 0.2 * H, y_max + 2.5 * H]
    solver = bishop_fs if method == "bishop" else oms_fs
    field = []
    best = None

    def eval_centre(xc, yc):
        nonlocal best
        local_best = None
        for k in range(n_depths):
            depth = y_min - (0.05 + 0.9 * k / max(n_depths - 1, 1)) * H
            R = yc - depth
            circle = {"xc": xc, "yc": yc, "R": R}
            try:
                slices, _ = make_slices(profile, circle, width=width,
                                        n_slices=n_slices)
                r = solver(slices)
            except ValueError:
                continue
            entry = {"xc": xc, "yc": yc, "R": R, "Fs": r["Fs"]}
            if local_best is None or r["Fs"] < local_best["Fs"]:
                local_best = entry
            if best is None or r["Fs"] < best["Fs"]:
                best = entry
        if local_best:
            field.append(local_best)

    for i in range(nx):
        for j in range(ny):
            xc = box[0] + (box[1] - box[0]) * i / max(nx - 1, 1)
            yc = box[2] + (box[3] - box[2]) * j / max(ny - 1, 1)
            eval_centre(xc, yc)
    for _ in range(refine):
        if best is None:
            break
        dx = (box[1] - box[0]) / max(nx - 1, 1)
        dy = (box[3] - box[2]) / max(ny - 1, 1)
        for i in (-1, -0.5, 0, 0.5, 1):
            for j in (-1, -0.5, 0, 0.5, 1):
                eval_centre(best["xc"] + i * dx * 0.5,
                            best["yc"] + j * dy * 0.5)
    if best is None:
        raise ValueError("no admissible trial circle found in the search box")
    return {"best": best, "field": field, "method": method}
