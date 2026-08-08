"""Unit handling (protocol steps U1-U2) and physical bounds (N5).

All quantities are normalised to a canonical SI set at the boundary
(m, kN, kPa, kN/m3, degrees, dimensionless fractions) and converted to the
requested unit only at final display. Arithmetic in the executor carries
pint quantities, so a dimensional slip raises at compute time instead of
producing a wrong number.
"""

from pint import UnitRegistry

ureg = UnitRegistry()
Q_ = ureg.Quantity

# canonical unit per symbol family (what the executor works in)
CANONICAL = {
    "length": "m",
    "stress": "kPa",
    "unit_weight": "kN/m^3",
    "force": "kN",
    "angle": "degree",
    "volume": "m^3",
    "dimensionless": "",
}

# symbol -> family. Symbols not listed are treated as dimensionless.
SYMBOL_FAMILY = {
    "B": "length", "L": "length", "Df": "length", "Dw": "length",
    "H": "length", "z": "length", "D": "length",
    "c": "stress", "c_prime": "stress", "su": "stress", "cu": "stress",
    "q_surcharge": "stress", "sigma_v": "stress", "q_ult": "stress",
    "q_all": "stress", "q_net": "stress", "q_applied": "stress",
    "gamma": "unit_weight", "gamma_sat": "unit_weight",
    "gamma_dry": "unit_weight", "gamma_w": "unit_weight",
    "gamma_eff": "unit_weight", "gamma_prime": "unit_weight",
    "phi": "angle", "phi_prime": "angle", "delta": "angle",
    "beta": "angle", "alpha": "angle",
    "Q_ult": "force", "Q_all": "force", "P": "force", "W": "force",
    "e_load": "length",           # load eccentricity
    "V": "volume",
    "s": "length",                # strut spacing along the cut
    "dA": "length", "dB": "length", "dC": "length",
    "sigma_all": "stress",
    "FS": "dimensionless", "Gs": "dimensionless", "w": "dimensionless",
    # piles
    "Ep": "stress", "Es": "stress", "mu_s": "dimensionless",
    "Qwp": "force", "Qws": "force",
    # sheet pile walls
    "L1": "length", "L2": "length",
    # cantilever retaining wall geometry (Das notation)
    "x1": "length", "x2": "length", "x3": "length", "x4": "length",
    "x5": "length", "alpha": "angle", "gamma_c": "unit_weight",
    "gamma2": "unit_weight", "phi2": "angle", "c2": "stress",
    # circular slip surface
    "xc": "length", "yc": "length", "R": "length",
    "ru": "dimensionless",
    # reliability inputs (standard deviations of soil parameters)
    "sigma_c": "stress", "sigma_phi": "angle", "sigma_gamma": "unit_weight",
}

# unit spellings that pint does not accept out of the box
_UNIT_ALIASES = {
    "kn/m3": "kN/m^3", "kn/m^3": "kN/m^3", "kn/m³": "kN/m^3",
    "kn/m2": "kPa", "kn/m^2": "kPa", "kn/m²": "kPa", "kpa": "kPa",
    "mpa": "MPa", "t/m3": "tonne_force/m^3", "deg": "degree",
    "degrees": "degree", "°": "degree", "kn": "kN", "n": "N",
    "": "dimensionless", None: "dimensionless",
}


def clean_unit(u):
    if u is None:
        return "dimensionless"
    key = str(u).strip().lower()
    return _UNIT_ALIASES.get(key, str(u).strip())


def canonical_unit(sym: str) -> str:
    return CANONICAL[SYMBOL_FAMILY.get(sym, "dimensionless")]


def normalise(sym: str, value: float, unit) -> float:
    """Convert an input to the symbol's canonical unit; returns a float
    magnitude. Raises pint.DimensionalityError on inconsistent input."""
    target = canonical_unit(sym)
    u = clean_unit(unit)
    if not target:  # dimensionless; percentages become fractions
        if str(unit).strip() in ("%", "percent", "pct"):
            return float(value) / 100.0
        return float(value)
    q = Q_(float(value), u)
    # density given for a unit weight: make the x g explicit (U1)
    if SYMBOL_FAMILY.get(sym) == "unit_weight" and q.check("[mass] / [volume]"):
        q = (q * ureg.standard_gravity).to(target)
    return q.to(target).magnitude


def to_display(value: float, from_unit: str, to_unit: str) -> float:
    if not from_unit or not to_unit or from_unit == to_unit:
        return value
    return Q_(value, from_unit).to(clean_unit(to_unit)).magnitude


# ---------------------------------------------------------------------------
# Physical bounds (N5): values outside these never reach the user.
# (min, max, canonical unit)
# ---------------------------------------------------------------------------

BOUNDS = {
    "phi": (0.0, 55.0, "degree"),
    "phi_prime": (0.0, 55.0, "degree"),
    "gamma": (9.0, 26.0, "kN/m^3"),
    "gamma_sat": (12.0, 26.0, "kN/m^3"),
    "gamma_eff": (2.0, 26.0, "kN/m^3"),
    "c": (0.0, 1500.0, "kPa"),
    "c_prime": (0.0, 500.0, "kPa"),
    "su": (0.0, 1500.0, "kPa"),
    "B": (0.05, 50.0, "m"),
    "L": (0.05, 100.0, "m"),
    "Df": (0.0, 80.0, "m"),
    "Dw": (0.0, 200.0, "m"),
    "FS": (1.0, 10.0, ""),
    "q_ult": (1.0, 300000.0, "kPa"),
    "q_all": (0.5, 100000.0, "kPa"),
    "Q_ult": (0.1, 1e7, "kN"),
    "Q_all": (0.1, 1e7, "kN"),
}


def bounds_violation(sym: str, value: float):
    """Return a message when a canonical-unit value is physically
    implausible, else None."""
    if sym not in BOUNDS:
        return None
    lo, hi, unit = BOUNDS[sym]
    if value < lo or value > hi:
        u = f" {unit}" if unit else ""
        return (f"{sym} = {value:g}{u} is outside the plausible range "
                f"[{lo:g}, {hi:g}]{u}")
    return None
