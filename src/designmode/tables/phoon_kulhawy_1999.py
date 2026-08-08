"""Typical ranges of soil properties, digitised from Phoon & Kulhawy (1999).

Source (verified against the paper's text layer, 2026-08-08):
    Phoon, K.-K. and Kulhawy, F.H. (1999). "Characterization of geotechnical
    variability." Canadian Geotechnical Journal, 36(4), 612-624.
    - Table 1 (p. 615): inherent variability of strength properties
    - Table 2 (p. 616): inherent variability of index parameters
    - Table 7 (p. 621): approximate guidelines for inherent soil variability

These are ADVISORY ranges: values outside them are flagged to the reader
with the citation, then used exactly as given. They are ranges of mean
values compiled from the paper's database, not physical limits; the hard
impossibility bounds live in units.py.
"""

CITATION = ("Phoon and Kulhawy (1999), Canadian Geotechnical Journal "
            "36(4), 612-624")

# sym -> (lo, hi, unit label, which table + page, detail)
TYPICAL = {
    "phi": (20.0, 40.0, "degrees", "Table 7, p. 621",
            "range of mean effective friction angles for clay and sand"),
    "su": (10.0, 700.0, "kPa", "Table 7, p. 621",
           "union of the su ranges for UC (10-400), UU (10-350) and CIUC "
           "(150-700) tests on clay"),
    "gamma": (14.0, 20.0, "kN/m^3", "Table 2, p. 616",
              "range of mean total unit weights of the compiled "
              "fine-grained deposits"),
    "gamma_dry": (13.0, 18.0, "kN/m^3", "Table 2, p. 616",
                  "range of mean dry unit weights of the compiled deposits"),
    "w": (0.13, 1.05, "(as a fraction)", "Table 2, p. 616",
          "range of mean natural water contents, 13-105 %"),
}

# aliases share their base symbol's range
_ALIASES = {"phi_prime": "phi", "phi2": "phi", "cu": "su",
            "gamma2": "gamma", "gamma_sat": "gamma"}


def atypical_warnings(givens: dict) -> list[dict]:
    """Flag given values outside the Phoon & Kulhawy typical ranges."""
    out = []
    seen = set()
    for sym, val in givens.items():
        base = _ALIASES.get(sym, sym)
        if base not in TYPICAL or base in seen or not isinstance(val, (int, float)):
            continue
        lo, hi, unit, where, detail = TYPICAL[base]
        if val < lo or val > hi:
            seen.add(base)
            out.append({
                "sym": sym, "value": val, "lo": lo, "hi": hi, "unit": unit,
                "where": where, "detail": detail,
            })
    return out
