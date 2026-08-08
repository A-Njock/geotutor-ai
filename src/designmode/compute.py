"""Numerical executor (protocol steps N1-N5, U1).

The model never computes: every numerical step is an expression string from
the registry or the solver, evaluated here with pint unit-carrying
quantities at full precision. Rounding happens only at display. Each final
result is independently re-evaluated straight from the registry equation and
the two paths must agree within 0.5 %.
"""

import math

from .units import Q_, canonical_unit, bounds_violation

# the only names an expression may use besides bound symbols
_SAFE_FUNCS = {
    "sqrt": math.sqrt, "tan": math.tan, "sin": math.sin, "cos": math.cos,
    "atan": math.atan, "radians": math.radians, "log": math.log,
    "log10": math.log10, "exp": math.exp, "pi": math.pi,
    "min": min, "max": max, "abs": abs,
}


class ComputeError(Exception):
    pass


def evaluate(expression: str, bindings: dict, result_sym: str) -> float:
    """Evaluate one expression with unit-carrying arithmetic (N1, U1).

    `bindings` maps symbol -> float magnitude in its canonical unit; each is
    wrapped in its pint unit so dimensional slips raise here instead of
    surfacing as wrong numbers. Returns the float magnitude of the result in
    the result symbol's canonical unit.
    """
    ns = dict(_SAFE_FUNCS)
    for sym, val in bindings.items():
        cu = canonical_unit(sym)
        # angles enter trig via radians(); keep them as plain degrees here
        ns[sym] = Q_(float(val), cu) if cu and cu != "degree" else float(val)
    try:
        out = eval(expression, {"__builtins__": {}}, ns)  # noqa: S307
    except Exception as e:
        raise ComputeError(f"expression '{expression}' failed: {e}") from e

    target = canonical_unit(result_sym)
    if hasattr(out, "to"):
        try:
            out = out.to(target).magnitude if target else out.magnitude
        except Exception as e:
            raise ComputeError(
                f"'{expression}' produced wrong dimensions for {result_sym}: {e}"
            ) from e
    result = float(out)

    msg = bounds_violation(result_sym, result)  # N5
    if msg:
        raise ComputeError(f"implausible result: {msg}")
    return result


def recompute_check(expression: str, bindings: dict, result_sym: str,
                    first_pass_value: float, tolerance: float = 0.005) -> dict:
    """Protocol N4: independent second evaluation, plain floats, no pint.
    Deviation beyond `tolerance` (relative) marks the step as failed."""
    ns = dict(_SAFE_FUNCS)
    ns.update({k: float(v) for k, v in bindings.items()})
    try:
        second = float(eval(expression, {"__builtins__": {}}, ns))  # noqa: S307
    except Exception as e:
        return {"ok": False, "reason": f"recomputation failed: {e}"}
    ref = max(abs(first_pass_value), 1e-12)
    dev = abs(second - first_pass_value) / ref
    return {"ok": dev <= tolerance, "deviation": dev, "recomputed": second}


def display_round(value: float, sig: int = 4) -> float:
    """Round only at final display (N2)."""
    if value == 0:
        return 0.0
    from math import floor, log10
    return round(value, -int(floor(log10(abs(value)))) + (sig - 1))
