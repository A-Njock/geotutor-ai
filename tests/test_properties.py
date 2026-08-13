"""Physics invariants over random valid inputs (assurance plan, point 2).

Pure Python against the deterministic layer: builders and the slope
kernel are imported directly, no LLM is ever called. Every random draw is
seeded, so a failure reproduces exactly. Parameter windows mirror
src/designmode/envelope.yaml.
"""

import math
import random
import re
import sys
from pathlib import Path

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
from src.designmode.domains.slope import _culmann             # noqa: E402

SEED = 20260812
N = 300


def noop(*args, **kwargs):
    """Stub for the narration callback: swallow every step."""


class Capture:
    """Narration stub that keeps the full-precision result values."""

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


# ---------------------------------------------------------------------------
# a) slope kernel: OMS and Bishop on the toe-circle contract
# ---------------------------------------------------------------------------

def _circle(H, beta):
    """The envelope's deterministic trial circle for a slope (H, beta)."""
    xc = 0.5 * H / math.tan(math.radians(beta))
    return K.toe_circle(xc, 1.5 * H)


def _fs_pair(H, beta, c, phi, gamma, water=None, n_slices=30):
    prof = K.simple_slope_profile(H, beta, c=c, phi=phi, gamma=gamma,
                                  water=water)
    slices, _ = K.make_slices(prof, _circle(H, beta), n_slices=n_slices)
    return K.oms_fs(slices)["Fs"], K.bishop_fs(slices)["Fs"]


def test_slope_fs_decreases_as_beta_increases():
    random.seed(SEED)
    skips = 0
    for _ in range(N):
        H = random.uniform(3, 40)
        b1 = random.uniform(15, 60)
        b2 = b1 + random.uniform(3, 10)
        c = random.uniform(5, 40)
        phi = random.uniform(5, 35)
        gam = random.uniform(16, 22)
        try:
            o1, bi1 = _fs_pair(H, b1, c, phi, gam)
            o2, bi2 = _fs_pair(H, b2, c, phi, gam)
        except ValueError:
            skips += 1
            continue
        assert o2 <= o1 + 1e-9, (
            f"OMS rose with beta: H={H:.2f} b1={b1:.2f} b2={b2:.2f} "
            f"c={c:.1f} phi={phi:.1f}: {o1:.4f} -> {o2:.4f}")
        assert bi2 <= bi1 + 1e-9, (
            f"Bishop rose with beta: H={H:.2f} b1={b1:.2f} b2={b2:.2f} "
            f"c={c:.1f} phi={phi:.1f}: {bi1:.4f} -> {bi2:.4f}")
    assert skips < 0.3 * N, f"too many inadmissible circles: {skips}/{N}"


def test_slope_fs_increases_with_c_and_phi():
    random.seed(SEED)
    skips = 0
    for _ in range(N):
        H = random.uniform(3, 40)
        b = random.uniform(15, 70)
        c = random.uniform(2, 40)
        phi = random.uniform(5, 35)
        gam = random.uniform(16, 22)
        dc = random.uniform(2, 20)
        dphi = random.uniform(2, 10)
        try:
            o0, b0 = _fs_pair(H, b, c, phi, gam)
            oc, bc = _fs_pair(H, b, c + dc, phi, gam)
            op, bp = _fs_pair(H, b, c, phi + dphi, gam)
        except ValueError:
            skips += 1
            continue
        assert oc > o0 and bc > b0, "Fs did not rise with c"
        assert op > o0 and bp > b0, "Fs did not rise with phi"
    assert skips < 0.3 * N, f"too many inadmissible circles: {skips}/{N}"


def test_slope_fs_decreases_as_ru_increases():
    random.seed(SEED)
    skips = 0
    for _ in range(N):
        H = random.uniform(3, 40)
        b = random.uniform(15, 60)
        c = random.uniform(5, 40)
        phi = random.uniform(5, 35)
        gam = random.uniform(16, 22)
        r1 = random.uniform(0.0, 0.3)
        r2 = r1 + random.uniform(0.05, 0.2)
        try:
            o1, b1 = _fs_pair(H, b, c, phi, gam,
                              water={"type": "ru", "value": r1})
            o2, b2 = _fs_pair(H, b, c, phi, gam,
                              water={"type": "ru", "value": r2})
        except ValueError:
            skips += 1
            continue
        assert o2 <= o1 + 1e-9, f"OMS rose with ru: {o1:.4f} -> {o2:.4f}"
        assert b2 <= b1 + 1e-9, f"Bishop rose with ru: {b1:.4f} -> {b2:.4f}"
    assert skips < 0.3 * N, f"too many inadmissible circles: {skips}/{N}"


def test_slope_bishop_at_least_090_of_oms():
    random.seed(SEED)
    skips = 0
    for _ in range(N):
        H = random.uniform(3, 40)
        b = random.uniform(15, 70)
        c = random.uniform(2, 40)
        phi = random.uniform(5, 35)
        gam = random.uniform(16, 22)
        ru = random.uniform(0.0, 0.4)
        water = {"type": "ru", "value": ru} if ru > 0.02 else None
        try:
            oms, bis = _fs_pair(H, b, c, phi, gam, water=water)
        except ValueError:
            skips += 1
            continue
        assert bis >= 0.9 * oms, (
            f"Bishop fell under 0.9 OMS: OMS={oms:.4f} Bishop={bis:.4f} "
            f"H={H:.2f} beta={b:.2f} c={c:.1f} phi={phi:.1f} ru={ru:.2f}")
    assert skips < 0.3 * N, f"too many inadmissible circles: {skips}/{N}"


# ---------------------------------------------------------------------------
# b) bearing factors and earth-pressure coefficients
# ---------------------------------------------------------------------------

_MONOTONE_FACTORS = [
    F.vesic_Nq, F.vesic_Nc, F.vesic_Ngamma,
    F.terzaghi_Nc, F.terzaghi_Nq, F.terzaghi_Ngamma,
    F.hansen_Ngamma, F.meyerhof_Ngamma,
]


def test_factors_strictly_increase_with_phi():
    random.seed(SEED)
    for _ in range(N):
        p1 = random.uniform(1.0, 48.0)
        p2 = p1 + random.uniform(0.2, 49.0 - p1)
        for fn in _MONOTONE_FACTORS:
            v1, v2 = fn(p1), fn(p2)
            assert v2 > v1, (
                f"{fn.__name__} not increasing: "
                f"{fn.__name__}({p1:.3f})={v1:.4f} >= "
                f"{fn.__name__}({p2:.3f})={v2:.4f}")


def test_factor_anchors_at_phi_zero():
    for fn in (F.terzaghi_Nq, F.meyerhof_Nq, F.hansen_Nq, F.vesic_Nq):
        assert fn(0.0) == 1.0, f"{fn.__name__}(0) != 1"
    for fn in (F.meyerhof_Nc, F.hansen_Nc, F.vesic_Nc):
        assert abs(fn(0.0) - (2.0 + math.pi)) < 1e-9, (
            f"{fn.__name__}(0) is not the Prandtl 5.14")
    for fn in (F.terzaghi_Ngamma, F.meyerhof_Ngamma, F.hansen_Ngamma,
               F.vesic_Ngamma):
        assert fn(0.0) == 0.0, f"{fn.__name__}(0) != 0"


def test_coulomb_degenerates_to_rankine():
    random.seed(SEED)
    for _ in range(N):
        phi = random.uniform(1.0, 45.0)
        p = math.radians(phi)
        rankine = (1.0 - math.sin(p)) / (1.0 + math.sin(p))
        coulomb = F.coulomb_Ka(phi, 0.0, 0.0, 90.0)
        assert abs(coulomb - rankine) < 1e-6, (
            f"Coulomb(delta=0, level, vertical) != Rankine at "
            f"phi={phi:.3f}: {coulomb} vs {rankine}")


def test_rankine_ka_kp_reciprocal_level_ground():
    random.seed(SEED)
    for _ in range(N):
        phi = random.uniform(1.0, 45.0)
        prod = F.rankine_Ka(phi) * F.rankine_Kp(phi)
        assert abs(prod - 1.0) < 1e-9, f"Ka*Kp != 1 at phi={phi:.3f}: {prod}"


# ---------------------------------------------------------------------------
# c) lateral thrust on a wall (Rankine chains in retaining.py)
# ---------------------------------------------------------------------------

def _thrust(givens, text):
    cap = Capture()
    out = _lateral_thrust({}, givens, cap, text)
    assert isinstance(out, dict)
    assert "error" not in out, out.get("error")
    for sym in ("P_a", "P_p", "P"):
        if sym in cap.vals:
            return cap.vals[sym], cap, out
    raise AssertionError("no thrust value captured")


def test_active_thrust_monotone_in_H_gamma_phi():
    random.seed(SEED)
    for _ in range(N):
        H = random.uniform(1.0, 12.0)
        gam = random.uniform(15.0, 22.0)
        phi = random.uniform(20.0, 42.0)
        base, _, _ = _thrust({"H": H, "gamma": gam, "phi": phi},
                             "active thrust on the wall")
        assert base > 0 and math.isfinite(base)
        up_h, _, _ = _thrust({"H": H + random.uniform(0.5, 4.0),
                              "gamma": gam, "phi": phi},
                             "active thrust on the wall")
        assert up_h > base, "P did not rise with H"
        up_g, _, _ = _thrust({"H": H, "gamma": gam + random.uniform(1, 4),
                              "phi": phi},
                             "active thrust on the wall")
        assert up_g > base, "P did not rise with gamma"
        up_p, _, _ = _thrust({"H": H, "gamma": gam,
                              "phi": phi + random.uniform(1, 5)},
                             "active thrust on the wall")
        assert up_p < base, "P did not fall with phi"


def test_passive_exceeds_active_same_soil():
    random.seed(SEED)
    for _ in range(N):
        g = {"H": random.uniform(1.0, 12.0),
             "gamma": random.uniform(15.0, 22.0),
             "phi": random.uniform(15.0, 42.0)}
        pa, _, _ = _thrust(dict(g), "active thrust on the wall")
        pp, _, _ = _thrust(dict(g), "passive thrust on the wall")
        assert pp > pa, f"passive {pp:.2f} not above active {pa:.2f} for {g}"


def test_active_thrust_decreases_with_cohesion():
    random.seed(SEED)
    for _ in range(N):
        H = random.uniform(2.0, 10.0)
        gam = random.uniform(15.0, 22.0)
        phi = random.uniform(0.0, 35.0)
        c1 = random.uniform(1.0, 40.0)
        c2 = c1 + random.uniform(2.0, 40.0)
        p1, _, _ = _thrust({"H": H, "gamma": gam, "phi": phi, "c": c1},
                           "active thrust on the wall")
        p2, _, _ = _thrust({"H": H, "gamma": gam, "phi": phi, "c": c2},
                           "active thrust on the wall")
        assert p2 <= p1 + 1e-9, (
            f"P rose with c: c {c1:.1f}->{c2:.1f}, P {p1:.3f}->{p2:.3f}")
        assert p1 >= 0.0 and p2 >= 0.0, "negative thrust"


def test_sloping_backfill_components():
    random.seed(SEED)
    for _ in range(N):
        phi = random.uniform(25.0, 42.0)
        alpha = random.uniform(1.0, phi - 1.0)
        g = {"H": random.uniform(2.0, 10.0),
             "gamma": random.uniform(15.0, 22.0),
             "phi": phi, "alpha": alpha}
        p, cap, out = _thrust(g, "active thrust on the wall")
        a = math.radians(alpha)
        ph = cap.vals.get("P_h")
        assert ph is not None, "no horizontal component captured"
        assert abs(ph - p * math.cos(a)) <= 1e-6 * max(p, 1.0), (
            f"Pah != P cos(alpha): {ph} vs {p * math.cos(a)}")
        pav = conclusion(out, "P_av")
        assert pav is not None
        # the conclusion value is display-rounded to 4 significant figures
        assert abs(pav - p * math.sin(a)) <= 1e-3 * max(p, 1.0), (
            f"Pav != P sin(alpha) beyond display rounding: "
            f"{pav} vs {p * math.sin(a)}")


# ---------------------------------------------------------------------------
# d) phase relations (soil_basics)
# ---------------------------------------------------------------------------

def test_phase_unit_weight_ordering():
    random.seed(SEED)
    for _ in range(N):
        e = random.uniform(0.3, 1.5)
        gs = random.uniform(2.5, 2.8)
        s = random.uniform(0.05, 1.0)
        cap = Capture()
        out = basics.build({}, {"e_void": e, "Gs": gs, "S_r": s}, cap,
                           "Find the unit weights of the soil.")
        assert "error" not in out, out.get("error")
        gd = cap.vals["gamma_d"]
        g = cap.vals["gamma"]
        gsat = cap.vals["gamma_sat"]
        assert 0 < gd <= g + 1e-9 <= gsat + 2e-9, (
            f"ordering broken: gamma_d={gd} gamma={g} gamma_sat={gsat} "
            f"(e={e:.3f}, Gs={gs:.3f}, S={s:.3f})")
        for v in (gd, g, gsat):
            assert math.isfinite(v) and v > 0


def test_phase_saturated_soil_hits_gamma_sat():
    random.seed(SEED)
    for _ in range(N):
        e = random.uniform(0.3, 1.5)
        gs = random.uniform(2.5, 2.8)
        cap = Capture()
        out = basics.build({}, {"e_void": e, "Gs": gs, "S_r": 1.0}, cap,
                           "Find the unit weights of the soil.")
        assert "error" not in out
        assert abs(cap.vals["gamma"] - cap.vals["gamma_sat"]) < 1e-9, (
            f"S=1 but gamma != gamma_sat at e={e:.3f}, Gs={gs:.3f}")


def test_phase_gamma_equals_W_over_V():
    random.seed(SEED)
    for _ in range(N):
        V = random.uniform(0.001, 0.1)
        gamma_true = random.uniform(14.0, 20.0)
        W = gamma_true * V
        w = random.uniform(0.05, 0.4)
        gs = random.uniform(2.5, 2.8)
        cap = Capture()
        out = basics.build({}, {"V": V, "W": W, "w": w, "Gs": gs}, cap,
                           "Phase relations of the sample.")
        assert "error" not in out, out.get("error")
        assert abs(cap.vals["gamma"] - W / V) < 1e-9 * gamma_true, (
            f"gamma != W/V: {cap.vals['gamma']} vs {W / V}")


# ---------------------------------------------------------------------------
# e) consolidation
# ---------------------------------------------------------------------------

def test_consolidation_time_quarters_under_double_drainage():
    random.seed(SEED)
    for _ in range(N):
        cv = random.uniform(0.5, 20.0)
        H = random.uniform(1.0, 15.0)
        U = random.uniform(0.2, 0.95)
        cap_d, cap_s = Capture(), Capture()
        od = consolidation.build(
            {}, {"cv": cv, "H": H, "U": U}, cap_d,
            "Time to reach the target degree; sand above and below the "
            "clay layer.")
        os_ = consolidation.build(
            {}, {"cv": cv, "H": H, "U": U}, cap_s,
            "Time to reach the target degree; the clay rests on an "
            "impermeable base.")
        assert "error" not in od and "error" not in os_
        td, ts = cap_d.vals["t"], cap_s.vals["t"]
        assert td > 0 and ts > 0
        assert abs(ts / td - 4.0) < 1e-9, (
            f"single/double time ratio is {ts / td}, not 4")


def test_consolidation_time_decreases_with_cv():
    random.seed(SEED)
    for _ in range(N):
        cv1 = random.uniform(0.5, 10.0)
        cv2 = cv1 + random.uniform(0.5, 10.0)
        H = random.uniform(1.0, 15.0)
        U = random.uniform(0.2, 0.95)
        c1, c2 = Capture(), Capture()
        consolidation.build({}, {"cv": cv1, "H": H, "U": U}, c1,
                            "Time needed; the clay drains from both faces.")
        consolidation.build({}, {"cv": cv2, "H": H, "U": U}, c2,
                            "Time needed; the clay drains from both faces.")
        assert c2.vals["t"] < c1.vals["t"], "t did not fall as cv rose"


def test_consolidation_tv_at_90_percent_is_0848():
    cap = Capture()
    out = consolidation.build(
        {}, {"cv": 2.0, "H": 6.0, "U": 0.9}, cap,
        "Time to 90 percent consolidation; sand above and below the clay.")
    assert "error" not in out
    assert conclusion(out, "T_v") == 0.848


def test_settlement_increases_with_load_and_Cc():
    random.seed(SEED)
    text = "Find the primary consolidation settlement of the clay layer."
    for _ in range(N):
        H = random.uniform(1.0, 10.0)
        e0 = random.uniform(0.5, 1.5)
        s0 = random.uniform(30.0, 200.0)
        ds1 = random.uniform(10.0, 150.0)
        ds2 = ds1 + random.uniform(10.0, 100.0)
        cc1 = random.uniform(0.1, 0.6)
        cc2 = cc1 + random.uniform(0.05, 0.4)
        base_g = {"H": H, "e_void": e0, "sigma_v0": s0, "d_sigma": ds1,
                  "Cc": cc1}
        c0, cd, cc = Capture(), Capture(), Capture()
        o0 = consolidation.build({}, dict(base_g), c0, text)
        od = consolidation.build({}, dict(base_g, d_sigma=ds2), cd, text)
        oc = consolidation.build({}, dict(base_g, Cc=cc2), cc, text)
        assert "error" not in o0 and "error" not in od and "error" not in oc
        s_base = c0.vals["S_c"]
        assert s_base > 0
        assert cd.vals["S_c"] > s_base, "S_c did not rise with d_sigma"
        assert cc.vals["S_c"] > s_base, "S_c did not rise with Cc"


# ---------------------------------------------------------------------------
# f) permeability
# ---------------------------------------------------------------------------

def test_falling_head_k_increases_with_log_head_ratio():
    random.seed(SEED)
    for _ in range(N):
        g = {"D_s": random.uniform(0.05, 0.15),
             "L_s": random.uniform(0.1, 0.3),
             "d_pipe": random.uniform(0.005, 0.02),
             "h2": random.uniform(0.2, 0.5),
             "t_el": random.uniform(30.0, 600.0)}
        g1 = dict(g, h1=g["h2"] + random.uniform(0.1, 0.5))
        g2 = dict(g, h1=g1["h1"] + random.uniform(0.1, 0.5))
        c1, c2 = Capture(), Capture()
        o1 = permeability.build({}, g1, c1, "Falling head test on the soil.")
        o2 = permeability.build({}, g2, c2, "Falling head test on the soil.")
        assert "error" not in o1 and "error" not in o2
        k1, k2 = c1.vals["k"], c2.vals["k"]
        assert k1 > 0 and k2 > 0 and math.isfinite(k1) and math.isfinite(k2)
        assert k2 > k1, "k did not rise with ln(h1/h2)"


def test_constant_head_k_linear_in_collected_volume():
    random.seed(SEED)
    for _ in range(N):
        g = {"D_s": random.uniform(0.05, 0.15),
             "L_s": random.uniform(0.1, 0.3),
             "h_const": random.uniform(0.2, 0.8),
             "Q_vol": random.uniform(5e-4, 5e-3),
             "t_el": random.uniform(30.0, 600.0)}
        c1, c2 = Capture(), Capture()
        o1 = permeability.build({}, dict(g), c1, "Constant head test.")
        o2 = permeability.build({}, dict(g, Q_vol=2.0 * g["Q_vol"]), c2,
                                "Constant head test.")
        assert "error" not in o1 and "error" not in o2
        k1, k2 = c1.vals["k"], c2.vals["k"]
        assert k1 > 0 and math.isfinite(k1)
        assert abs(k2 / k1 - 2.0) < 1e-9, "k not linear in Q_vol"


# ---------------------------------------------------------------------------
# g) classification totality: 1000 random draws, never a raise
# ---------------------------------------------------------------------------

_USCS_SYMBOL = re.compile(r"^[A-Z]{2}(-[A-Z]{2})?$")


def test_classification_totality_1000_draws():
    random.seed(SEED)
    for i in range(1000):
        g = {"P200": random.uniform(0.0, 100.0)}
        g["P4"] = random.uniform(g["P200"], 100.0)
        g["LL"] = random.uniform(0.0, 120.0)
        g["PL"] = random.uniform(0.0, g["LL"])
        if random.random() < 0.5:
            g["Cu"] = random.uniform(0.5, 30.0)
            g["Cz"] = random.uniform(0.1, 5.0)
        try:
            out = classify.build({}, g, noop, "Classify the soil (USCS).")
        except Exception as exc:  # noqa: BLE001 - the point of the test
            raise AssertionError(
                f"classify.build raised {type(exc).__name__} on draw "
                f"{i}: {g}") from exc
        assert isinstance(out, dict)
        if "error" in out:
            assert isinstance(out["error"], str) and out["error"]
            continue
        sym = conclusion(out, "group_symbol")
        assert sym, f"no group symbol and no error for {g}"
        assert _USCS_SYMBOL.match(sym), (
            f"symbol {sym!r} breaks the USCS grammar for {g}")


# ---------------------------------------------------------------------------
# h) Culmann plane wedge
# ---------------------------------------------------------------------------

def _culmann_fs(H, beta, c, phi, gamma):
    cap = Capture()
    out = _culmann({}, {"H": H, "beta": beta, "c": c, "phi": phi,
                        "gamma": gamma}, cap,
                   "Culmann plane failure through the toe.")
    assert "error" not in out, out.get("error")
    return cap.vals["Fs"]


def test_culmann_fs_monotone_in_H_beta_c():
    random.seed(SEED)
    for _ in range(N):
        phi = random.uniform(0.0, 30.0)
        beta = random.uniform(phi + 10.0, 80.0)
        H = random.uniform(2.0, 15.0)
        c = random.uniform(10.0, 60.0)
        gam = random.uniform(16.0, 22.0)
        fs = _culmann_fs(H, beta, c, phi, gam)
        assert fs > 0 and math.isfinite(fs)
        assert _culmann_fs(H + random.uniform(1.0, 8.0), beta, c, phi,
                           gam) < fs, "FS did not fall with H"
        assert _culmann_fs(H, min(beta + random.uniform(2.0, 8.0), 89.0),
                           c, phi, gam) < fs, "FS did not fall with beta"
        assert _culmann_fs(H, beta, c + random.uniform(5.0, 40.0), phi,
                           gam) > fs, "FS did not rise with c"


def test_culmann_safe_depth_inverts_fs():
    random.seed(SEED)
    for _ in range(N):
        phi = random.uniform(0.0, 30.0)
        beta = random.uniform(phi + 10.0, 80.0)
        H = random.uniform(2.0, 20.0)
        c = random.uniform(10.0, 60.0)
        gam = random.uniform(16.0, 22.0)
        fs = _culmann_fs(H, beta, c, phi, gam)
        cap = Capture()
        out = _culmann({}, {"beta": beta, "c": c, "phi": phi,
                            "gamma": gam, "FS": fs}, cap,
                       "Culmann plane failure: maximum depth of the cut.")
        assert "error" not in out
        h_back = cap.vals["Hcr"]
        assert abs(h_back - H) / H < 0.005, (
            f"round trip broke: H={H:.4f} FS={fs:.5f} back={h_back:.4f}")
