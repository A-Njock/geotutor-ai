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
    "consolidation_coeff": "m^2/year",
    "mass": "kg",
    "density": "Mg/m^3",
    "time": "s",
    "flow": "m^3/s",
    "velocity": "m/s",
    "compressibility": "m^2/kN",
    "moment": "kN*m",
    "grain_size": "mm",
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
    # phase relations without weights; consolidation time-rate
    "e_void": "dimensionless", "S_r": "dimensionless",
    "Nc": "dimensionless", "U": "dimensionless",
    "cv": "consolidation_coeff",
    # lab measurements
    "m_tin": "mass", "m_wet_tot": "mass", "m_dry_tot": "mass",
    "m_wet": "mass", "m_dry": "mass", "m_wax": "mass",
    "D_s": "length", "L_s": "length",
    "rho_bulk": "density", "rho_dry": "density", "rho_wax": "density",
    "e_max": "dimensionless", "e_min": "dimensionless",
    # permeability and seepage
    "d_pipe": "length", "h1": "length", "h2": "length",
    "h_const": "length", "H_head": "length",
    "t_el": "time", "Q_vol": "volume", "q_flow": "flow",
    "r1": "length", "r2": "length", "hw1": "length", "hw2": "length",
    "Nf": "dimensionless", "Nd": "dimensionless", "k_perm": "velocity",
    # consolidation magnitude and scaling
    "Cc": "dimensionless", "Cr": "dimensionless", "OCR": "dimensionless",
    "sigma_v0": "stress", "d_sigma": "stress", "mv": "compressibility",
    "t_lab": "time", "H_lab": "length",
    # classification
    "P200": "dimensionless", "P4": "dimensionless",
    "D10": "grain_size", "D30": "grain_size", "D60": "grain_size",
    "Cu": "dimensionless", "Cz": "dimensionless",
    "LL": "dimensionless", "PL": "dimensionless", "PI": "dimensionless",
    # capacity fidelity
    "su2": "stress", "cw": "stress", "M_mom": "moment",
    "Ir": "dimensionless", "Nq": "dimensionless",
    "Ngamma": "dimensionless", "K": "dimensionless",
    "n_slices": "dimensionless", "S_limit": "length",
    "theta_wall": "angle",
    # stress states
    "sigma_1": "stress", "sigma_3": "stress", "sigma_d": "stress",
    "u_pore": "stress", "sigma_n": "stress", "tau_f": "stress",
}

# unit spellings that pint does not accept out of the box
_UNIT_ALIASES = {
    "kn/m3": "kN/m^3", "kn/m^3": "kN/m^3", "kn/m³": "kN/m^3",
    "kn/m2": "kPa", "kn/m^2": "kPa", "kn/m²": "kPa", "kpa": "kPa",
    "mpa": "MPa", "t/m3": "tonne_force/m^3", "deg": "degree",
    "degrees": "degree", "°": "degree", "kn": "kN", "n": "N",
    "m2/year": "m^2/year", "m2/yr": "m^2/year", "m^2/yr": "m^2/year",
    "m2/s": "m^2/s", "m2/sec": "m^2/s", "cm2/s": "cm^2/s",
    "cm2/sec": "cm^2/s", "mm2/s": "mm^2/s", "m2/day": "m^2/day",
    "cm2/year": "cm^2/year", "cm2/yr": "cm^2/year",
    # densities (case is lost upstream: "mg/m3" always means megagram here)
    "mg/m3": "Mg/m^3", "mg/m^3": "Mg/m^3", "mg/m³": "Mg/m^3",
    "g/cm3": "g/cm^3", "g/cm^3": "g/cm^3", "g/cc": "g/cm^3",
    "kg/m3": "kg/m^3", "kg/m^3": "kg/m^3",
    "g": "gram", "gm": "gram", "grams": "gram", "kg": "kilogram",
    # time and flow
    "min": "minute", "mins": "minute", "minutes": "minute",
    "hr": "hour", "hrs": "hour", "h": "hour", "hours": "hour",
    "day": "day", "days": "day", "week": "week", "weeks": "week",
    "l": "liter", "litre": "liter", "litres": "liter", "ml": "milliliter",
    "l/s": "liter/second", "l/min": "liter/minute",
    "m3/s": "m^3/s", "m3/day": "m^3/day", "m3/min": "m^3/minute",
    "m/s": "m/s", "m/sec": "m/s", "cm/s": "cm/s", "cm/sec": "cm/s",
    "mm/s": "mm/s", "m/day": "m/day", "m/min": "m/minute",
    # compressibility and moment
    "m2/kn": "m^2/kN", "m^2/kn": "m^2/kN", "1/kpa": "1/kPa",
    "kn*m": "kN*m", "kn-m": "kN*m", "knm": "kN*m", "kn m": "kN*m",
    "kn.m": "kN*m", "kn-m/m": "kN*m",
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
    # a bare number for an angle symbol is taken as printed (degrees or a
    # dimensionless factor like the pile adhesion alpha); pint would
    # otherwise assume radians and silently multiply by 57.3
    if SYMBOL_FAMILY.get(sym) == "angle" and u == "dimensionless":
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
    "e_void": (0.05, 5.0, ""),
    "S_r": (0.0, 1.000001, ""),
    "U": (0.0, 1.000001, ""),
    "Nc": (1.0, 100.0, ""),
    "cv": (1e-4, 1e4, "m^2/year"),
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
