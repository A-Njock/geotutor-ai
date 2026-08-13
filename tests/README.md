# GeoTutor deterministic-layer test suites

Assurance plan points 1-3: the machine-readable capability envelope plus
the two suites that back it with evidence. Everything here is pure
Python against the deterministic layer (builders, the slope kernel, the
factor functions). No LLM is ever called, no network is touched, and all
randomness is seeded (20260812), so every run is reproducible.

## Run

From the repo root:

```powershell
& "e:\YORK.A\Python codes2\BIN\Antigrav\.venv\Scripts\python.exe" -m pytest tests -q
```

Full run takes about 6 seconds.

## The envelope's role

`src/designmode/envelope.yaml` is the capability envelope (assurance
plan point 1): per domain, the geometry parameter ranges, the layer
counts and water conditions the builders genuinely support (read from
the builder code, not guessed), the loading types, and what happens
outside the ranges (an honest error dict, which the pipeline can then
retry in the general reasoning mode with its warning label).

The property suite draws its random parameters INSIDE those ranges, so
the envelope is exactly the region where the physics invariants are
guaranteed by test. The adversarial suite probes the edges and the
just-outside region. If a builder's support ever widens or narrows, the
envelope file and the draw windows in the suites must move together.

## test_properties.py - physics invariants over random valid inputs

24 tests, most looping 300 seeded random draws (1000 for the
classification totality sweep). The invariants hold without knowing any
answer in advance:

- **Slope kernel** (OMS and Bishop on the toe-circle contract): Fs falls
  as beta rises, rises with c and with phi, falls as ru rises;
  Bishop >= 0.9 x OMS. Trial circle per draw: xc = 0.5 H / tan(beta),
  yc = 1.5 H; inadmissible circles are counted and must stay under 30 %.
- **Bearing factors**: all eight N-factor functions strictly increase
  with phi on [1, 49]; Nq(0) = 1; the Prandtl-form Nc(0) = 2 + pi;
  Coulomb Ka(delta=0, level, vertical) equals Rankine (1-sin)/(1+sin)
  within 1e-6; Rankine Ka x Kp = 1 within 1e-9 on level ground.
- **Lateral thrust** (Rankine chains): active P rises with H and gamma,
  falls with phi; passive > active for the same soil; P falls as c rises
  and never goes negative; with a sloping backfill Pah = P cos(alpha)
  within 1e-6 and Pav = P sin(alpha) within display rounding.
- **Phase relations**: gamma_d <= gamma <= gamma_sat, all positive;
  S = 1 makes gamma equal gamma_sat exactly; from (V, W, w, Gs) the bulk
  unit weight is exactly W/V.
- **Consolidation**: single-drainage time is exactly 4 x the
  double-drainage time for the same layer; t falls as cv rises;
  Tv(U=90 %) = 0.848; settlement rises with d_sigma and with Cc.
- **Permeability**: k > 0 always; falling-head k rises with ln(h1/h2);
  constant-head k is exactly linear in the collected volume.
- **Classification totality**: 1000 random valid gradation/plasticity
  draws; build() never raises, always returns a group symbol or an
  honest error dict; USCS symbols match `^[A-Z]{2}(-[A-Z]{2})?$`.
- **Culmann**: FS falls with H and beta, rises with c; the safe-depth
  formula inverts the FS computation (round trip within 0.5 %).

## test_adversarial.py - weird-but-valid edge probes

39 tests (36 pass, 3 xfail). Deterministic nasty cases; each must end in
a finite number or an honest error dict - never an unhandled exception,
never NaN/inf, never a negative capacity. Covered: slope faces at 89.5
and 0.5 degrees, H = 0.1 m and 200 m, one and 500 slices, a circle
barely clipping the ground; factor functions at phi = 0, 0.001, 49.999;
walls with Dw = 0, Dw = H, huge cohesion (tension crack past the base),
backfill slope exactly at phi; phases at S = 1, w = 0, and both
percent/fraction conventions; consolidation at U = 0.999 (allowed) and
U = 1.0 (refuses), lab thickness equal to field; classification at the
exact P200 = 50/12/5, PI = 4/7, LL = 50 boundaries, zero fines, and
single-value inputs; permeameters with h1 = h2, r1 = r2, hw1 = hw2 (all
refuse instead of dividing).

## Current counts (2026-08-13)

| Suite                | Pass | xfail | Fail |
|----------------------|------|-------|------|
| test_properties.py   | 24   | 0     | 0    |
| test_adversarial.py  | 36   | 3     | 0    |
| total                | 60   | 3     | 0    |

## Recorded findings (the 3 xfails)

These are real defects found by the probes, deliberately recorded
instead of fixed here (strict xfails: they will flag when fixed):

1. `test_slope_single_slice_plausibly_bounded` - n_slices = 1 on a toe
   circle returns Fs of order 1e27 instead of refusing: the single
   midline slice sits near the circle apex, the driving sum nearly
   cancels, and the kernel only refuses when that sum is <= 0, not when
   it is degenerately small.
2. `test_slope_barely_clipping_plausibly_bounded` - a trial circle that
   barely clips the ground returns Fs of order 1e20 for the same
   reason; it should be reported as an inadmissible circle.
3. `test_thrust_huge_cohesion_lever_arm_non_negative` - when the
   tension crack depth exceeds the wall height the thrust is correctly
   floored at 0, but the reported lever arm z_bar = (H - z_c)/3 goes
   negative (-25.4 m "above the base" for H = 3 m, c = 500 kPa); it
   should be clamped at 0 or omitted once no compressive zone remains.
