"""Formula registry loader and constraint matcher (protocol steps F1-F2, F4).

The matcher is pure Python: given the validated problem frame and the bound
givens, it returns every formula whose applicability block is satisfied.
Selection is by constraint match, never by generation, so an inapplicable
formula cannot be chosen at all.
"""

from pathlib import Path

import yaml

REGISTRY_DIR = Path(__file__).parent / "registry"

_cache = None


def load_registry() -> dict:
    """{formula_id: formula_dict}, merged across all domain files."""
    global _cache
    if _cache is None:
        _cache = {}
        for f in sorted(REGISTRY_DIR.glob("*.yaml")):
            doc = yaml.safe_load(f.read_text(encoding="utf-8"))
            for formula in doc.get("formulas", []):
                formula["domain"] = doc["domain"]
                _cache[formula["id"]] = formula
    return _cache


def match_formulas(frame: dict, givens: dict) -> tuple[list[dict], list[str]]:
    """Return (applicable_formulas, rejection_log).

    `frame` is the validated C1 frame; `givens` maps canonical symbols to
    float values. The rejection log records why each candidate was excluded,
    which is surfaced in the audit trail.
    """
    reg = load_registry()
    applicable, rejections = [], []
    domain = frame.get("domain")
    shape = frame.get("footing_shape") or "strip"
    drainage = frame.get("drainage_condition")
    mechanism = frame.get("failure_mechanism") or "general_shear"
    phi = givens.get("phi", givens.get("phi_prime"))

    for fid, f in reg.items():
        if f["domain"] != domain:
            continue
        app = f.get("applicability", {})
        why = None

        if frame.get("unsupported_quantity"):
            why = ("the problem asks for a quantity the registry does not "
                   "cover yet (only bearing capacities for now)")
        elif frame.get("eccentric_load"):
            why = ("the load is eccentric; that needs Meyerhof's effective "
                   "area method, which is not yet in the registry")
        elif mechanism not in app.get("failure_mechanism", [mechanism]):
            why = f"failure mechanism '{mechanism}' not covered"
        elif drainage and drainage != "unknown" and \
                drainage not in app.get("drainage", [drainage]):
            why = f"drainage condition '{drainage}' not covered"
        elif shape not in app.get("footing_shape", [shape]):
            why = f"footing shape '{shape}' not covered"
        elif app.get("requires_phi_zero") and phi is not None and phi > 0.5:
            why = f"needs phi = 0 (undrained clay) but phi = {phi:g} deg"
        elif "max_Df_over_B" in app and "Df" in givens and "B" in givens \
                and givens["B"] > 0 \
                and givens["Df"] / givens["B"] > app["max_Df_over_B"] + 1e-9:
            why = (f"Df/B = {givens['Df'] / givens['B']:.2f} exceeds the "
                   f"method's shallow-footing limit of {app['max_Df_over_B']:g}")

        if why:
            rejections.append(f"{f['label']}: {why}")
        else:
            applicable.append(f)

    return applicable, rejections


def missing_inputs(formula: dict, givens: dict) -> list[str]:
    """Protocol F4: every symbol in `requires` must be bound before the
    formula may run. gamma_eff and q_surcharge are produced by the solver's
    water-table stage, so they count as derivable when gamma is known."""
    derivable = {"gamma_eff", "q_surcharge"}
    missing = []
    for sym in formula.get("requires", []):
        if sym in givens:
            continue
        if sym in derivable and ("gamma" in givens or "gamma_sat" in givens):
            continue
        if sym == "c" and ("c_prime" in givens or "su" in givens or
                           "cu" in givens or givens.get("phi", 0) > 0):
            continue  # c = 0 is a standard labelled assumption for sand
        if sym == "phi" and ("phi_prime" in givens or "su" in givens or
                             "cu" in givens):
            continue  # phi = 0 is a labelled assumption when only su is given
        if sym == "su" and ("cu" in givens or "c" in givens):
            continue
        if sym == "Df":
            continue  # defaults to 0 (surface footing) with a labelled assumption
        missing.append(sym)
    return missing
