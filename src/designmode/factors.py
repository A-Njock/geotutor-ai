"""Deterministic factor lookups (protocol step F3).

Bearing-capacity factors, earth-pressure coefficients and shape/depth
factors are computed or interpolated here — never recalled by the model.
Every function takes phi in DEGREES and returns plain floats.

Sources:
- Terzaghi Nc/Nq: closed form from Terzaghi (1943); Ngamma: Kumbhojkar (1993)
  values as tabulated in Das, Principles of Foundation Engineering (Table 4.1),
  log-interpolated between anchors.
- Meyerhof / Hansen / Vesic: standard closed forms.
- Skempton (1951) undrained Nc.
- Rankine and Coulomb earth-pressure coefficients.
"""

import math

D2R = math.pi / 180.0


# ---------------------------------------------------------------------------
# Terzaghi (1943), general shear
# ---------------------------------------------------------------------------

def terzaghi_Nq(phi: float) -> float:
    if phi <= 0:
        return 1.0
    p = phi * D2R
    a = math.exp((0.75 * math.pi - p / 2.0) * math.tan(p))
    return a * a / (2.0 * math.cos(math.pi / 4.0 + p / 2.0) ** 2)


def terzaghi_Nc(phi: float) -> float:
    if phi <= 0:
        return 5.70
    return (terzaghi_Nq(phi) - 1.0) / math.tan(phi * D2R)


# Kumbhojkar (1993) Ngamma anchors (phi deg -> Ngamma), Das Table 4.1
_TERZAGHI_NG = [
    (0, 0.0), (5, 0.14), (10, 0.56), (15, 1.52), (20, 3.64), (25, 8.34),
    (30, 19.13), (32, 26.87), (34, 38.04), (35, 45.41), (36, 54.36),
    (38, 78.61), (40, 115.31), (42, 171.99), (44, 261.60), (45, 325.34),
    (46, 407.11), (48, 650.67), (50, 1072.80),
]


def terzaghi_Ngamma(phi: float) -> float:
    if phi <= 0:
        return 0.0
    if phi >= 50:
        return _TERZAGHI_NG[-1][1]
    for (p0, v0), (p1, v1) in zip(_TERZAGHI_NG, _TERZAGHI_NG[1:]):
        if p0 <= phi <= p1:
            if v0 <= 0:  # linear near zero, log-linear elsewhere
                return v0 + (v1 - v0) * (phi - p0) / (p1 - p0)
            f = (phi - p0) / (p1 - p0)
            return math.exp(math.log(v0) + f * (math.log(v1) - math.log(v0)))
    return _TERZAGHI_NG[-1][1]


# Terzaghi's own shape coefficients for the c and gamma terms
TERZAGHI_SHAPE = {
    "strip": {"s_c": 1.0, "s_gamma": 1.0},
    "square": {"s_c": 1.3, "s_gamma": 0.8},
    "rectangular": {"s_c": 1.3, "s_gamma": 0.8},  # conservative: treated as square
    "circular": {"s_c": 1.3, "s_gamma": 0.6},
}


# ---------------------------------------------------------------------------
# Meyerhof / Hansen / Vesic share Nq and Nc
# ---------------------------------------------------------------------------

def _Nq_exponential(phi: float) -> float:
    if phi <= 0:
        return 1.0
    p = phi * D2R
    return math.exp(math.pi * math.tan(p)) * math.tan(math.pi / 4.0 + p / 2.0) ** 2


def _Nc_from_Nq(phi: float) -> float:
    if phi <= 0:
        return 2.0 + math.pi  # 5.14
    return (_Nq_exponential(phi) - 1.0) / math.tan(phi * D2R)


def meyerhof_Nq(phi: float) -> float:
    return _Nq_exponential(phi)


def meyerhof_Nc(phi: float) -> float:
    return _Nc_from_Nq(phi)


def meyerhof_Ngamma(phi: float) -> float:
    if phi <= 0:
        return 0.0
    return (_Nq_exponential(phi) - 1.0) * math.tan(1.4 * phi * D2R)


def hansen_Nq(phi: float) -> float:
    return _Nq_exponential(phi)


def hansen_Nc(phi: float) -> float:
    return _Nc_from_Nq(phi)


def hansen_Ngamma(phi: float) -> float:
    if phi <= 0:
        return 0.0
    return 1.5 * (_Nq_exponential(phi) - 1.0) * math.tan(phi * D2R)


def vesic_Nq(phi: float) -> float:
    return _Nq_exponential(phi)


def vesic_Nc(phi: float) -> float:
    return _Nc_from_Nq(phi)


def vesic_Ngamma(phi: float) -> float:
    if phi <= 0:
        return 0.0
    return 2.0 * (_Nq_exponential(phi) + 1.0) * math.tan(phi * D2R)


# ---------------------------------------------------------------------------
# Shape and depth factors
# ---------------------------------------------------------------------------

def meyerhof_shape_depth(phi: float, B: float, L: float, Df: float) -> dict:
    """Meyerhof (1963). L is the long side; strip -> B/L = 0."""
    Kp = math.tan(math.pi / 4.0 + phi * D2R / 2.0) ** 2
    BL = (B / L) if L and L > 0 else 0.0
    DB = Df / B if B > 0 else 0.0
    s_c = 1.0 + 0.2 * Kp * BL
    d_c = 1.0 + 0.2 * math.sqrt(Kp) * DB
    if phi >= 10:
        s_q = s_g = 1.0 + 0.1 * Kp * BL
        d_q = d_g = 1.0 + 0.1 * math.sqrt(Kp) * DB
    else:
        s_q = s_g = 1.0
        d_q = d_g = 1.0
    return {"s_c": s_c, "s_q": s_q, "s_gamma": s_g,
            "d_c": d_c, "d_q": d_q, "d_gamma": d_g, "Kp": Kp}


def debeer_hansen_shape_depth(phi: float, B: float, L: float, Df: float,
                              Nq: float, Nc: float) -> dict:
    """De Beer (1970) shape + Hansen (1970) depth, used by Hansen and Vesic."""
    BL = (B / L) if L and L > 0 else 0.0
    p = phi * D2R
    s_c = 1.0 + BL * (Nq / Nc)
    s_q = 1.0 + BL * math.tan(p)
    s_g = max(1.0 - 0.4 * BL, 0.6)
    k = (Df / B) if (B > 0 and Df <= B) else (math.atan(Df / B) if B > 0 else 0.0)
    d_c = 1.0 + 0.4 * k
    d_q = 1.0 + 2.0 * math.tan(p) * (1.0 - math.sin(p)) ** 2 * k
    d_g = 1.0
    return {"s_c": s_c, "s_q": s_q, "s_gamma": s_g,
            "d_c": d_c, "d_q": d_q, "d_gamma": d_g}


# ---------------------------------------------------------------------------
# Skempton (1951), undrained clay (phi = 0)
# ---------------------------------------------------------------------------

def skempton_Nc(B: float, L: float, Df: float, shape: str) -> float:
    DB = min(Df / B, 2.5) if B > 0 else 0.0
    if shape == "strip":
        return min(5.0 * (1.0 + 0.2 * DB), 7.5)
    nc_sq = min(6.0 * (1.0 + 0.2 * DB), 9.0)
    if shape in ("square", "circular"):
        return nc_sq
    BL = (B / L) if L and L > 0 else 1.0
    return nc_sq * (0.84 + 0.16 * BL)


# ---------------------------------------------------------------------------
# Earth-pressure coefficients (retaining-wall domain)
# ---------------------------------------------------------------------------

def rankine_Ka(phi: float, beta: float = 0.0) -> float:
    p, b = phi * D2R, beta * D2R
    if beta == 0.0:
        return (1.0 - math.sin(p)) / (1.0 + math.sin(p))
    root = math.sqrt(math.cos(b) ** 2 - math.cos(p) ** 2)
    return math.cos(b) * (math.cos(b) - root) / (math.cos(b) + root)


def rankine_Kp(phi: float, beta: float = 0.0) -> float:
    p, b = phi * D2R, beta * D2R
    if beta == 0.0:
        return (1.0 + math.sin(p)) / (1.0 - math.sin(p))
    root = math.sqrt(math.cos(b) ** 2 - math.cos(p) ** 2)
    return math.cos(b) * (math.cos(b) + root) / (math.cos(b) - root)


def coulomb_Ka(phi: float, delta: float, beta: float = 0.0,
               alpha: float = 90.0) -> float:
    """alpha: wall face angle from horizontal (90 = vertical),
    delta: wall friction, beta: backfill slope. All degrees."""
    p, d, b, a = phi * D2R, delta * D2R, beta * D2R, alpha * D2R
    num = math.sin(a + p) ** 2
    den = (math.sin(a) ** 2 * math.sin(a - d) *
           (1.0 + math.sqrt(math.sin(p + d) * math.sin(p - b) /
                            (math.sin(a - d) * math.sin(a + b)))) ** 2)
    return num / den


# ---------------------------------------------------------------------------
# Registry of callable factors: formula YAML refers to these by name
# ---------------------------------------------------------------------------

FACTOR_FUNCTIONS = {
    "terzaghi_Nc": terzaghi_Nc,
    "terzaghi_Nq": terzaghi_Nq,
    "terzaghi_Ngamma": terzaghi_Ngamma,
    "meyerhof_Nc": meyerhof_Nc,
    "meyerhof_Nq": meyerhof_Nq,
    "meyerhof_Ngamma": meyerhof_Ngamma,
    "hansen_Nc": hansen_Nc,
    "hansen_Nq": hansen_Nq,
    "hansen_Ngamma": hansen_Ngamma,
    "vesic_Nc": vesic_Nc,
    "vesic_Nq": vesic_Nq,
    "vesic_Ngamma": vesic_Ngamma,
    "rankine_Ka": rankine_Ka,
    "rankine_Kp": rankine_Kp,
    "coulomb_Ka": coulomb_Ka,
}


if __name__ == "__main__":
    # spot checks against published tables
    assert abs(terzaghi_Nq(30) - 22.46) < 0.05, terzaghi_Nq(30)
    assert abs(terzaghi_Nc(30) - 37.16) < 0.05, terzaghi_Nc(30)
    assert abs(meyerhof_Nq(30) - 18.40) < 0.05, meyerhof_Nq(30)
    assert abs(meyerhof_Nc(30) - 30.14) < 0.05, meyerhof_Nc(30)
    assert abs(meyerhof_Ngamma(30) - 15.67) < 0.05, meyerhof_Ngamma(30)
    assert abs(hansen_Ngamma(30) - 15.07) < 0.05, hansen_Ngamma(30)
    assert abs(vesic_Ngamma(30) - 22.40) < 0.05, vesic_Ngamma(30)
    assert abs(rankine_Ka(30) - (1 / 3)) < 1e-6
    print("factors: all spot checks pass")
