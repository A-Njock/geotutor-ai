"""Independent verification backend for slope chains (Phase 2).

Runs Spencer's method (complete equilibrium) from the pinned xslope engine
(Apache-2.0, vendored license retained) on the SAME slices our kernel built.
These results are presented as independent checks with attribution — never
narrated as hand calculations, because a two-unknown Newton iteration is not
a teachable spreadsheet step.

Trust rule: before reporting Spencer, the engine's own OMS is run on the
same table and must agree with our kernel's OMS to 0.1 % — proving the
table hand-off is faithful. If it does not, no verification is reported.
"""

import math

try:
    import numpy as np
    import pandas as pd

    from xslope import solve as _XS
    AVAILABLE = True
except Exception:                                    # pragma: no cover
    AVAILABLE = False

XSLOPE_VERSION = "0.2.1"


def _slices_to_df(slices, circle):
    n = len(slices)
    rows = {
        "alpha": [s["alpha_deg"] for s in slices],
        "phi": [s["phi"] for s in slices],
        "c": [s["c"] for s in slices],
        "w": [s["W"] for s in slices],
        "u": [s["u"] for s in slices],
        "dl": [s["dl"] for s in slices],
        "dx": [s["b"] for s in slices],
        "x_c": [s.get("xm", 0.0) for s in slices],
        "y_cb": [s.get("y_base", 0.0) for s in slices],
        "y_cg": [s.get("y_base", 0.0) + 0.5 * s.get("h", 0.0)
                 for s in slices],
        "y_lb": [s.get("y_lb", s.get("y_base", 0.0)) for s in slices],
        "y_rb": [s.get("y_rb", s.get("y_base", 0.0)) for s in slices],
        "y_lt": [s.get("y_lt", 0.0) for s in slices],
        "y_rt": [s.get("y_rt", 0.0) for s in slices],
        "x_l": [s.get("x0", 0.0) for s in slices],
        "x_r": [s.get("x1", 0.0) for s in slices],
        "dload": [0.0] * n, "d_x": [0.0] * n, "d_y": [0.0] * n,
        "beta": [0.0] * n, "kw": [0.0] * n, "t": [0.0] * n,
        "y_t": [0.0] * n, "p": [0.0] * n,
        "h_pile": [0.0] * n, "theta_p": [0.0] * n,
        "r": [circle["R"]] * n, "xo": [circle["xc"]] * n,
        "yo": [circle["yc"]] * n,
    }
    # better base-edge elevations when the kernel provides them
    df = pd.DataFrame(rows)
    return df


def spencer_check(slices, circle, our_oms_fs):
    """Returns {"FS": float, "engine": str} or {"declined": reason}."""
    if not AVAILABLE:
        return {"declined": "verification engine not installed"}
    try:
        df = _slices_to_df(slices, circle)
        ok0, r0 = _XS.oms(df)
        if not ok0:
            return {"declined": f"engine OMS failed: {r0}"}
        if abs(r0["FS"] - our_oms_fs) > 0.001 * max(abs(our_oms_fs), 1e-9):
            return {"declined": "hand-off check failed: engine OMS "
                                f"{r0['FS']:.4f} vs ours {our_oms_fs:.4f}"}
        ok, r = _XS.spencer(df)
        if not ok:
            return {"declined": f"Spencer did not converge: {r}"}
        out = {"FS": float(r["FS"]),
               "engine": f"xslope {XSLOPE_VERSION} (Apache-2.0)"}
        # second independent check: Morgenstern-Price on the same table
        # (best-effort; Spencer alone already stands if it declines)
        try:
            ok2, r2 = _XS.mprice(df)
            if ok2:
                out["FS_mp"] = float(r2["FS"])
        except Exception:
            pass
        return out
    except Exception as e:                            # pragma: no cover
        return {"declined": f"verification error: {str(e)[:80]}"}


def normal_cdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))
