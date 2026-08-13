"""Weird-but-valid edge probes (assurance plan, point 3).

Deterministic nasty cases against the deterministic layer only: no LLM,
no network. Every case must end in a sane outcome: a finite number or an
honest error dict. Never an unhandled exception, never NaN or inf, never
a negative capacity.

Where a probe exposes a real defect, the assertion is recorded as an
xfail with the finding in its reason string; fixing the builder is out of
scope for this suite.
"""

import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.designmode import factors as F                       # noqa: E402
from src.designmode import slope_kernel as K                  # noqa: E402
from src.designmode.domains import basics                     # noqa: E402
from src.designmode.domains import classify                   # noqa: E402
from src.designmode.domains import consolidation              # noqa: E402
from src.designmode.domains import permeability               # noqa: E402
from src.designmode.domains.retaining import _lateral_thrust  # noqa: E402

YEAR_S = 3.156e7


def noop(*args, **kwargs):
    """Narration stub."""


class Capture:
    def __init__(self):
        self.vals = {}

    def __call__(self, *args, **kwargs):
        r = kwargs.get("result")
        if r and "sym" in r:
            self.vals[r["sym"]] = r["value"]


def conclusion(out, quantity):
    for c in out.get("conclusions", []):
        if c["quantity"] == quantity:
            return c["value"]
    return None


def sane(x):
    return x is not None and math.isfinite(x)


# ---------------------------------------------------------------------------
# slope kernel extremes
# ---------------------------------------------------------------------------

def _slope_fs(H, beta, n_slices=30, circle=None):
    """Run the kernel; a named ValueError counts as an honest refusal and
    is returned as the string 'refused'."""
    if circle is None:
        xc = 0.5 * H / math.tan(math.radians(beta))
        circle = K.toe_circle(xc, 1.5 * H)
    prof = K.simple_slope_profile(H, beta, c=15.0, phi=25.0, gamma=19.0)
    try:
        slices, _ = K.make_slices(prof, circle, n_slices=n_slices)
        return K.oms_fs(slices)["Fs"], K.bishop_fs(slices)["Fs"]
    except ValueError:
        return "refused", "refused"


@pytest.mark.parametrize("H,beta", [
    (10.0, 89.5),   # near-vertical face
    (10.0, 0.5),    # near-flat face
    (0.1, 30.0),    # razor-thin slope
    (200.0, 30.0),  # far outside the envelope: may refuse, must not crash
])
def test_slope_extreme_geometry_no_crash(H, beta):
    oms, bis = _slope_fs(H, beta)
    if oms == "refused":
        return  # an honest named refusal is a pass
    assert sane(oms) and sane(bis), f"non-finite Fs at H={H}, beta={beta}"
    assert oms > 0 and bis > 0, f"negative Fs at H={H}, beta={beta}"


def test_slope_500_slices_matches_norm():
    oms, bis = _slope_fs(10.0, 45.0, n_slices=500)
    assert sane(oms) and sane(bis)
    assert 0.1 < oms < 100 and 0.1 < bis < 100


def test_slope_single_slice_no_crash():
    oms, bis = _slope_fs(10.0, 45.0, n_slices=1)
    if oms == "refused":
        return
    assert sane(oms) and sane(bis)
    assert oms > 0 and bis > 0


# finding FIXED: the builder now refuses circles whose driving mass is
# degenerately small (Fs quotient above 1000 or non-finite)
def test_slope_single_slice_plausibly_bounded():
    oms, _ = _slope_fs(10.0, 45.0, n_slices=1)
    assert oms == "refused" or oms < 1e3


def test_slope_circle_barely_clipping_toe_no_crash():
    circle = {"xc": 12.0, "yc": 25.0, "R": 15.02}  # dips ~0.02 m under crest
    oms, bis = _slope_fs(10.0, 45.0, circle=circle)
    if oms == "refused":
        return
    assert sane(oms) and sane(bis)
    assert oms > 0


# finding FIXED: same inadmissible-circle guard covers the sliver case
def test_slope_barely_clipping_plausibly_bounded():
    circle = {"xc": 12.0, "yc": 25.0, "R": 15.02}
    oms, _ = _slope_fs(10.0, 45.0, circle=circle)
    assert oms == "refused" or oms < 1e3


# ---------------------------------------------------------------------------
# bearing factors at regime edges
# ---------------------------------------------------------------------------

def test_factors_at_phi_zero():
    assert F.vesic_Nq(0.0) == 1.0
    assert abs(F.vesic_Nc(0.0) - (2.0 + math.pi)) < 1e-12
    assert F.vesic_Ngamma(0.0) == 0.0
    assert F.terzaghi_Nc(0.0) == 5.70  # Terzaghi's own phi = 0 anchor


def test_factors_just_above_phi_zero():
    for fn in (F.vesic_Nq, F.vesic_Nc, F.vesic_Ngamma, F.terzaghi_Nq,
               F.terzaghi_Nc, F.terzaghi_Ngamma, F.meyerhof_Ngamma,
               F.hansen_Ngamma):
        v = fn(0.001)
        assert sane(v) and v >= 0.0, f"{fn.__name__}(0.001) = {v}"


def test_factors_just_below_fifty():
    for fn in (F.vesic_Nq, F.vesic_Nc, F.vesic_Ngamma, F.terzaghi_Nq,
               F.terzaghi_Nc, F.terzaghi_Ngamma, F.meyerhof_Ngamma,
               F.hansen_Ngamma):
        v = fn(49.999)
        assert sane(v) and v > 0.0, f"{fn.__name__}(49.999) = {v}"
        assert v < 1e5, f"{fn.__name__}(49.999) = {v} looks unphysical"


# ---------------------------------------------------------------------------
# lateral thrust edges
# ---------------------------------------------------------------------------

def _thrust(givens, text="active thrust on the wall"):
    cap = Capture()
    out = _lateral_thrust({}, givens, cap, text)
    p = None
    for sym in ("P_a", "P_p", "P"):
        if sym in cap.vals:
            p = cap.vals[sym]
            break
    return out, p, cap


def test_thrust_tiny_wall():
    out, p, _ = _thrust({"H": 0.001, "gamma": 18.0, "phi": 30.0})
    assert "error" not in out
    assert sane(p) and p >= 0.0


def test_thrust_water_at_surface():
    out, p, _ = _thrust({"H": 4.0, "gamma": 18.0, "phi": 30.0, "Dw": 0.0,
                         "gamma_sat": 20.0})
    assert "error" not in out
    assert sane(p) and p > 0.0
    # water over the full height must push harder than the dry wall
    _, p_dry, _ = _thrust({"H": 4.0, "gamma": 18.0, "phi": 30.0})
    assert p > p_dry


def test_thrust_water_at_surface_without_gamma_sat_refuses():
    out, _, _ = _thrust({"H": 4.0, "gamma": 18.0, "phi": 30.0, "Dw": 0.0})
    assert "error" in out and isinstance(out["error"], str)


def test_thrust_water_exactly_at_base():
    # Dw = H means no water inside the wall height: the dry chain applies
    out, p, _ = _thrust({"H": 4.0, "gamma": 18.0, "phi": 30.0, "Dw": 4.0,
                         "gamma_sat": 20.0})
    assert "error" not in out
    assert sane(p) and p > 0.0
    _, p_dry, _ = _thrust({"H": 4.0, "gamma": 18.0, "phi": 30.0})
    assert abs(p - p_dry) < 1e-9


def test_thrust_huge_cohesion_never_negative():
    out, p, _ = _thrust({"H": 3.0, "gamma": 18.0, "phi": 20.0, "c": 500.0})
    assert "error" not in out
    assert p == 0.0, "crack past the wall base must leave zero thrust"
    zc = conclusion(out, "z_c")
    assert zc is not None and zc >= 0.0


# finding FIXED: z_c is capped at H and z_bar clamped at 0 once no
# compressive zone remains
def test_thrust_huge_cohesion_lever_arm_non_negative():
    out, _, _ = _thrust({"H": 3.0, "gamma": 18.0, "phi": 20.0, "c": 500.0})
    zbar = conclusion(out, "z_bar")
    assert zbar is not None and zbar >= 0.0


def test_thrust_backfill_slope_at_phi():
    # alpha -> phi drives the Rankine square root to zero: Ka -> cos(beta)
    for alpha in (30.0, 30.0 - 1e-9):
        out, p, _ = _thrust({"H": 4.0, "gamma": 18.0, "phi": 30.0,
                             "alpha": alpha})
        assert "error" not in out
        assert sane(p) and p > 0.0
    # and the limit value is the dry Ka = cos(alpha) triangle
    out, p, _ = _thrust({"H": 4.0, "gamma": 18.0, "phi": 30.0,
                         "alpha": 30.0})
    expected = 0.5 * 18.0 * 16.0 * math.cos(math.radians(30.0))
    assert abs(p - expected) < 1e-6


# ---------------------------------------------------------------------------
# phase relations edges
# ---------------------------------------------------------------------------

def test_phases_fully_saturated_exact():
    cap = Capture()
    out = basics.build({}, {"e_void": 0.6, "Gs": 2.7, "S_r": 1.0}, cap,
                       "Unit weights of the saturated soil.")
    assert "error" not in out
    assert abs(cap.vals["gamma"] - cap.vals["gamma_sat"]) < 1e-12


def test_phases_void_ratio_just_inside_envelope():
    cap = Capture()
    out = basics.build({}, {"e_void": 0.3001, "Gs": 2.65, "S_r": 0.5}, cap,
                       "Unit weights.")
    assert "error" not in out
    for sym in ("gamma", "gamma_d", "gamma_sat"):
        assert sane(cap.vals[sym]) and cap.vals[sym] > 0


def test_phases_zero_moisture():
    cap = Capture()
    out = basics.build({}, {"V": 0.01, "W": 0.18, "w": 0.0, "Gs": 2.7},
                       cap, "Phase relations of the oven-dry sample.")
    assert "error" not in out
    assert abs(cap.vals["gamma"] - 18.0) < 1e-9
    assert abs(cap.vals["gamma_d"] - cap.vals["gamma"]) < 1e-9
    assert cap.vals["S"] == 0.0       # reported in percent
    assert cap.vals["Vw"] == 0.0


def test_phases_percent_and_fraction_agree():
    c_pct, c_frac = Capture(), Capture()
    o1 = basics.build({}, {"V": 0.01, "W": 0.18, "w": 25.0, "Gs": 2.7},
                      c_pct, "Phase relations.")
    o2 = basics.build({}, {"V": 0.01, "W": 0.18, "w": 0.25, "Gs": 2.7},
                      c_frac, "Phase relations.")
    assert "error" not in o1 and "error" not in o2
    for sym in ("gamma", "gamma_d", "e", "S"):
        assert abs(c_pct.vals[sym] - c_frac.vals[sym]) < 1e-9, sym
    c_pct, c_frac = Capture(), Capture()
    basics.build({}, {"e_void": 0.7, "Gs": 2.7, "S_r": 80.0}, c_pct, "p")
    basics.build({}, {"e_void": 0.7, "Gs": 2.7, "S_r": 0.8}, c_frac, "p")
    for sym in ("gamma", "gamma_d", "gamma_sat"):
        assert abs(c_pct.vals[sym] - c_frac.vals[sym]) < 1e-9, sym


# ---------------------------------------------------------------------------
# consolidation edges
# ---------------------------------------------------------------------------

def test_consolidation_u_0999_allowed():
    cap = Capture()
    out = consolidation.build(
        {}, {"cv": 2.0, "H": 6.0, "U": 0.999}, cap,
        "Time needed; the clay drains from both faces.")
    assert "error" not in out
    assert sane(cap.vals["t"]) and cap.vals["t"] > 0


def test_consolidation_u_exactly_one_refuses():
    out = consolidation.build(
        {}, {"cv": 2.0, "H": 6.0, "U": 1.0}, noop,
        "Time to full consolidation; the clay drains from both faces.")
    assert "error" in out and "100" in out["error"]


def test_consolidation_lab_equals_field_thickness():
    # H_lab = H with matching double drainage: the field IS the specimen
    cap = Capture()
    out = consolidation.build(
        {}, {"t_lab": 300.0, "H_lab": 6.0, "H": 6.0}, cap,
        "Scale the oedometer time to the layer; sand above and below.")
    assert "error" not in out
    t_years = cap.vals["t"]
    assert abs(t_years * YEAR_S - 300.0) < 1e-6


# ---------------------------------------------------------------------------
# classification exact boundaries
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("givens,expected", [
    # fine/coarse split: exactly 50 % fines is fine-grained per D2487
    ({"P200": 50.0, "LL": 40.0, "PL": 20.0}, "CL"),
    # dual-symbol window edges: 5 % and 12 % both take the dual symbol
    ({"P200": 5.0, "P4": 60.0, "LL": 30.0, "PL": 20.0,
      "Cu": 8.0, "Cz": 2.0}, "SW-SC"),
    ({"P200": 12.0, "P4": 60.0, "LL": 30.0, "PL": 20.0,
      "Cu": 8.0, "Cz": 2.0}, "SW-SC"),
    # CL-ML hatched band edges: PI = 4 enters the band
    ({"P200": 80.0, "LL": 25.0, "PL": 21.0}, "CL-ML"),
    # PI = 7 at LL = 30 sits BELOW the A-line (PI_A = 7.3): silt
    ({"P200": 80.0, "LL": 30.0, "PL": 23.0}, "ML"),
    # LL exactly 50 is high plasticity
    ({"P200": 80.0, "LL": 50.0, "PL": 20.0}, "CH"),
    # zero fines with gradation numbers
    ({"P200": 0.0, "P4": 40.0, "Cu": 8.0, "Cz": 2.0}, "GW"),
    # everything zero except the fines content
    ({"P200": 100.0, "LL": 0.0, "PL": 0.0}, "ML"),
])
def test_classification_boundaries(givens, expected):
    out = classify.build({}, dict(givens), noop, "Classify the soil (USCS).")
    assert "error" not in out, out.get("error")
    assert conclusion(out, "group_symbol") == expected


def test_classification_p200_alone_refuses_honestly():
    out = classify.build({}, {"P200": 0.0}, noop, "Classify the soil (USCS).")
    assert "error" in out and isinstance(out["error"], str)


def test_classification_out_of_range_refuses():
    out = classify.build({}, {"P200": 104.0}, noop,
                         "Classify the soil (USCS).")
    assert "error" in out


# ---------------------------------------------------------------------------
# permeability degenerate inputs
# ---------------------------------------------------------------------------

def test_falling_head_equal_heads_refuses():
    out = permeability.build(
        {}, {"D_s": 0.1, "L_s": 0.15, "d_pipe": 0.01, "h1": 0.5,
             "h2": 0.5, "t_el": 60.0}, noop, "Falling head test.")
    assert "error" in out, "h1 == h2 must refuse, not divide"


def test_pumping_equal_radii_refuses():
    out = permeability.build(
        {}, {"q_flow": 0.01, "r1": 10.0, "r2": 10.0, "hw1": 4.0,
             "hw2": 5.0}, noop, "Pumping test in the aquifer.")
    assert "error" in out, "r1 == r2 must refuse, not take log(1)/0"


def test_pumping_equal_heads_refuses():
    out = permeability.build(
        {}, {"q_flow": 0.01, "r1": 10.0, "r2": 30.0, "hw1": 4.0,
             "hw2": 4.0}, noop, "Pumping test in the aquifer.")
    assert "error" in out, "hw1 == hw2 must refuse, not divide by zero"
