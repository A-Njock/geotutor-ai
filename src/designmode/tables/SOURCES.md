# Design chart & table source map

Verified sweep of `archive/old_pdf_library/PDF_database/` (2026-08-07, three parallel
readers over 22 chapter PDFs). Every entry below was CONFIRMED present at the stated
page — page numbers are PDF page positions inside each chapter file (1-based), not
printed book pages.

Purpose: when a factor/coefficient the solver needs is not yet in
`src/designmode/factors.py` or a domain builder, digitise it FROM THESE SOURCES into a
structured JSON file in this folder (schema at the bottom), register it in
`FACTOR_FUNCTIONS`, and reference it from the formula registry. Never let the LLM
recall chart values.

Short file keys (all under `archive/old_pdf_library/PDF_database/`):
- OU2/OU3/OU4/OU6/OU7a/OU7b/OU8 = Chang-Yu Ou & Kuo-Hsin Yang 2024, *Fundamentals of
  Foundation Engineering* chapter files (7a = "7...up to 350", 7b = "7...351-355";
  NOTE: the files named "5..." are Earth Retaining Structures, ch. 7 is piles)
- BABAN-BC / BABAN-S = Baban 2016 *Shallow Foundations* — Bearing Capacity / Settlement
- FEH3/6/8/10/11 = *The Foundation Engineering Handbook* chapters
- SMITH9/10/11/12/13 = Smith's Elements of Soil Mechanics chapters
- CRAIG4/11/12 = Craig's Soil Mechanics chapters
- SMF14/15 = Soil Mechanics Fundamentals and Applications chapters
- HB = *Handbook of Geotechnical Investigation and Design Tables* (407 pp)

## A. Already digitised / closed-form in the solver (no action)

| Item | Where in code | Cross-check source |
|---|---|---|
| Terzaghi Nc/Nq closed form + Kumbhojkar Ngamma anchors | factors.py `_TERZAGHI_NG` | OU3 p9 Table 3.1 (numeric, per-degree); BABAN-BC p11 Table 4.3 |
| Meyerhof/Hansen/Vesic factors (closed form) | factors.py | HB p338 Table 21.6 (numeric per 1 deg); BABAN-BC p11 Table 4.4 |
| Skempton undrained Nc | factors.py | HB p339 Table 21.7 (numeric: z/B 0-5, strip + square) |
| Rankine/Coulomb Ka, Kp | factors.py | Craig11 pp9-13 (general delta+batter+slope form) |
| Meyerhof pile Nq* — FULL per-degree table 20-45 deg | domains/pile.py `_MEYERHOF_NQ` | Das PFE per-degree table (user-supplied excerpt 2026-08-07); charts: SMF15 p4 Fig 15.5; FEH6 p8 Fig 6.4 (+ p9 critical-depth chart). Note: an earlier lone anchor 45->1174 was WRONG; the table value is 930 |
| Vesic pile N-sigma* closed form + Irr | domains/pile.py | FEH6 pp10-11 Tables 6.1a/6.1b (numeric grid to verify against) |
| Peck braced-cut envelopes | domains/braced.py | OU6 pp25-27 (Figs 6.14, 6.15 + eqs); FEH10 p37; Craig11 p51 |
| Vesic pile settlement Iwp≈0.85, Iws=2+0.35*sqrt(L/D) | domains/pile.py | OU7a p53 Eqs 7.43-7.46 |
| Water-table 3-case correction | solver.py `_water_table_stage` | OU3 p15 Fig 3.10 |
| Effective-area eccentric method | solver.py `_effective_area_chain` | BABAN-BC p18 Fig 4.5; OU3 p20 Fig 3.12 |

## B. In the library — digitise from here when the domain needs it

Shallow foundations / settlement:
- Steinbrenner I1/I2 elastic settlement table: BABAN-S p8 Table 3.8 (full M x N grid);
  F1/F2/A0-A2 closed forms OU3 pp24-25 Eqs 3.24-3.29
- Fox embedment depth factor If: BABAN-S p7 Table 3.7 + Fig 3.2; OU3 p24 Table 3.4
- Schmertmann Iz (CPT settlement): BABAN-S pp19-21 (construction rule is codeable:
  square Iz=0.1 at z=0, peak at 0.5B, 0 at 2B; strip 0.2/B/4B) + C1/C2/C3 eqs
- Consolidation Tv-U: HB p134 Table 8.19 (numeric, 3 drainage cases); closed form
  Craig4 p19 Eq 4.23 (Tv = pi/4 U^2 for U<0.6, else 1.781-0.933 log(100-U%))
- cv lab constructions: Craig4 p21 Fig 4.16 (log-time), p23 Fig 4.17 (root-time)
- Preconsolidation: Craig4 p6 Fig 4.4 (Casagrande); HB pp116-119 CPT/Vs correlations
- SPT corrections: HB p76 Tables 4.8 (CN, Skempton) & 4.9 (energy -> N60);
  phi from SPT: HB pp85-87 Tables 5.3-5.6; Dr: HB p337 Table 21.4, p95 Table 5.20
- Meyerhof allowable pressure from SPT: HB p340 Table 21.8 (B x N grid, numeric)
- Boussinesq rectangular corner: exact closed form (no table needed); coarse check
  table HB p386 Table 24.6; 2:1 method FEH3 p25; Newmark chart FEH3 pp27-28
- Eccentric+inclined reduction charts: BABAN-BC pp22-24 Figs 4.9-4.11 + p20 Table 4.9
- Layered-soil punching (Meyerhof-Hanna Ks): BABAN-BC pp35-36 Figs 4.20-4.22
- Footings near slopes (Meyerhof Ncq/Ngamma-q): BABAN-BC pp28-33
- Tolerable settlement / angular distortion: OU3 p32 Tables 3.5/3.6; BABAN-S pp3-5;
  HB pp371-375
- Es and Poisson ranges: BABAN-S pp13-16 Tables 3.9-3.12; HB pp176-177

Piles:
- alpha-method: OU7a p23 Table 7.2 (su/Pa -> alpha, 14 rows, Terzaghi/Peck/Mesri);
  FEH6 p12 Table 6.2 (Peck); Sladen closed form FEH6 p14 Eq 6.15b
- lambda-method: OU7a p24 Table 7.3 (L -> lambda, 13 rows, already numeric)
- beta-method: OU7a p24-26 (Burland eq, Ks/K0 Table 7.5, delta/phi Table 7.4);
  De Nicola & Randolph beta = 0.18 + 0.65 Dr
- Broms lateral capacity: FEH8 p5 Fig 8.4 (cohesive short/long), p12 Fig 8.9
  (cohesionless) + closed-form eqs pp6, 13; OU7a pp40, 43 duplicate charts
- Group efficiency: FEH6 p37 Converse-Labarre eq; OU7b p2 Kishida-Meyerhof chart
- Group settlement: SMF15 p25 equivalent raft at 2L/3 + 2:1; FEH6 p43
- Poulos & Davis elastic single pile: FEH6 pp29-33 Figs 6.14-6.18 (I0, Rk, Rh, Rv, Rb)
- SPT pile capacity: OU7a p27 Eqs 7.24/7.25 (Meyerhof 40N family); FEH6 p15
- CPT pile methods: FEH6 pp15-17 Tables 6.3-6.5; SMF15 p17 Table 15.7 (Eslami-Fellenius)
- Negative skin friction: OU7a pp53-55 (neutral plane); FEH6 p43 Table 6.9 (criteria)
- p-y curves: OU7a p46 Fig 7.30 Matlock + Table 7.6 (eps50); FEH8 pp16-18 Table 8.1
  (linear influence factors K_AH etc. vs beta*L — numeric)
- EC7 pile factors: SMITH10 pp20-29 Tables 10.2-10.4 (xi correlation + R1-R4 sets)

Retaining / excavation / slopes:
- Caquot-Kerisel passive: OU4 p27 Fig 4.12, p28 Fig 4.13 (charts) + p29 Table 4.1
  (NUMERIC reduction factor R, delta/phi 0-0.7 x phi 10-45; Kp(delta) = R * Kp(delta=phi))
- Taylor stability charts: Smith13 pp29-30 (best); FEH11 pp19-20; OU8 p15;
  Craig12 p10 (incl. Gibson-Morgenstern cu increasing with depth)
- Bishop-Morgenstern m/n plates: SMITH13 pp53-59 (image plates; theory pp33-37)
- Hoek-Bray circular-failure charts: OU8 p18 Fig 8.12 (5 groundwater cases)
- Michalowski seismic slope charts: OU8 p20 Fig 8.14
- Bjerrum-Eide bottom heave Nc: OU6 p10 Fig 6.8 + p11 Fig 6.9 (stiff-base + fd) +
  rectangular correction Eq 6.10
- Terzaghi basal heave, upheaval, piping: OU6 pp6-12, 20-23 (Eqs 6.1-6.19)
- Mononobe-Okabe seismic: OU4 pp33-36 (Kae Eq 4.37, Kpe Eq 4.41); FEH10 p41
- Compaction-induced pressure (Ingold): Craig11 pp32-34 + Fig 11.25
- Line/strip surcharge on walls: OU4 pp31-33 Figs 4.16/4.17; Craig11 p33
- Free-earth-support anchored sheet pile: Craig11 pp36-39 + Examples 11.7/11.8;
  FEH10 pp34-35
- Peck settlement-behind-excavation envelope: OU6 p38 Fig 6.23; Clough & O'Rourke
  p39 Fig 6.24; Craig11 p53 Fig 11.39
- Slurry-trench stability charts: Craig12 pp5-6 Figs 12.3-12.5
- Wall mobilisation movement Table: FEH10 p7 Table 10.1 (dx/H active/passive, numeric)
- MSE walls: FEH10 pp24-30 (procedure); Craig11 pp56-58
- Required FS tables (FHWA/AASHTO): FEH11 p3 Tables 11.1/11.2

## B2. Acquired 2026-08-07 (user downloads, copied into the library)

All five verified by rendering key pages; scan quality is good enough to
digitise when the consuming chain gets built. PDF page numbers are 1-based.

- `EM_1110-2-2504_Design_of_Sheet_Pile_Walls_USACE_1994.pdf` (75 pp, PUBLIC
  DOMAIN):
  - p52 Fig 6-4 — ROWE'S MOMENT-REDUCTION COEFFICIENTS (after Bowles 1982):
    sand panels R_M vs log rho (rho = H^4/EI, -4.0..-1.5) for loose and dense,
    curves alpha = 0.6/0.7/0.8; clay panels R_M vs stability number
    Sn = 1.25 C/Pv for rho = -3.1/-2.6/-2.0. Crisp; digitise at gridlines.
  - pp40-42 Figs 5-5..5-7 — cantilever + free-earth anchored design pressure
    distributions; p48 Figs 6-1/6-2 structural design pressures
  - Numeric tables extracted below (text layer, doubt-free)
- `Cousins_1978_Stability_Charts_for_Simple_Earth_Slopes_ASCE_GT2.pdf` (13 pp,
  the ORIGINAL Cousins paper): p6 Fig 4 toe-circle N_F charts (ru = 0/0.25/0.5,
  lambda-c-phi families, log scale); p7 Fig 5 depth-factor D = 1/1.25/1.5
  charts; pp8-9 Figs 6-7 critical-circle coordinate charts. Dense log-scale
  curve families — digitise carefully, per-curve, when a Cousins chain exists.
- `Morgenstern_1963_Stability_Charts_Rapid_Drawdown_Geotechnique.pdf` (11 pp,
  the ORIGINAL paper): charts are Figs 4/5/6 (c'/gammaH = 0.0125/0.025/0.05),
  each with slopes 2:1, 3:1, 4:1, 5:1 and phi' = 20/30/40 deg, FS vs drawdown
  ratio L/H in 0..1. Assumptions: homogeneous slope on rigid base, B-bar = 1,
  no dissipation, bulk density = 2 gamma_w, circles tangent to base.
  phi_w = (gamma'/gamma) phi_m conversion for Taylor comparison (Eq 8, p5).
- `Hunter_Schuster_Chart_Solutions_for_Analysis_of_Earth_Slopes_HRR345.pdf`
  (13 pp): compilation — Taylor (Figs 3-4), Bishop-Morgenstern (Figs 5-8 area),
  Morgenstern drawdown (Figs 9-10), Hunter / Hunter-Schuster charts
  (Figs 11-14, incl. depth-factor and M = cu-gradient cases). Whether Spencer's
  own charts are reproduced is UNVERIFIED — check before relying on it.
- `ENCE4610_Sheet_Piling_Walls_Lecture_Slides.pdf` (55 pp): teaching slides on
  cantilever/anchored walls + braced cuts; worked examples; no unique tables.

### EM 1110-2-2504 numeric tables (extracted 2026-08-07, text layer — exact)

Table 3-1 (after Teng 1962), granular soils — compactness: Dr %, SPT N, phi deg,
moist pcf, submerged pcf:
- Very loose: 0-15, 0-4, <28, <100, <60
- Loose: 16-35, 5-10, 28-30, 95-125, 55-65
- Medium: 36-65, 11-30, 31-36, 110-130, 60-70
- Dense: 66-85, 31-50, 37-41, 110-140, 65-85
- Very dense: 86-100, >51, >41, >130, >75
(imperial pcf; 1 pcf = 0.157 kN/m^3)

Table 3-2 (Allen, Duncan & Snacio 1988), delta/phi ratio by wall material:
- Sand: steel 0.54, wood 0.76, concrete 0.76
- Silt & clay: steel 0.54, wood 0.55, concrete 0.50

Table 3-3 (US Navy 1982), wall-interface friction delta (deg):
- Steel sheet piles: clean gravel/gravel-sand/well-graded rockfill 22;
  clean sand/silty sand-gravel/uniform hard rockfill 17; silty sand, gravel or
  sand mixed with silt or clay 14; fine sandy silt, nonplastic silt 11
- Concrete sheet piles: same four classes 22-26, 17-22, 17, 14

Table 3-4, clay consistency (qu = 2c, psf; SPT blows/ft; sat. unit weight pcf):
- Very soft 0-500, 0-2, <100-110; Soft 500-1000, 3-4, 100-120;
- Medium 1000-2000, 5-8, 110-125; Stiff 2000-4000, 9-16, 115-130;
- Very stiff 4000-8000, 16-32, 120-140; Hard >8000, >32, >130

## B3. Acquired 2026-08-07 (second batch) — the wants list is CLOSED

- `Das_Principles_of_Foundation_Engineering_SI_7th_Edition.pdf` (815 pp, the
  TDG course text). Coyle & Castello charts DIGITIZED EXACTLY from the PDF's
  vector paths (not eye-read): Fig 11.15 Nq* (PDF p584) and Fig 11.17 K
  (PDF p591) -> anchor tables now live in `src/designmode/domains/pile.py`
  (`_CC_NQ`, `_CC_K`). Calibration residual < 3 % of a log decade; validated
  vs the book's own Example 11.1c reading (Nq* ~ 48 at phi' 35, L/D 33.3 ->
  digitized 45.9) and deck parity (t09 C&C point now 2659 vs deck 2661.5).
  Note: phi' = 42 is beyond Fig 11.15 (curves end at 40 deg); the deck's
  Nq* = 100 reading was an extrapolation — kept as a disclosed anchored
  extension of the 40-degree curve. Also in the book: Table 11.8 Nc* vs Irr
  (phi = 0, numeric, PDF p583), O'Neill & Reese Ir correlation
  (Ir = 347 cu/pa - 33 <= 300), Mansur & Hunter field K values (H-piles 1.65,
  pipe 1.26, precast 1.5, PDF p590), Meyerhof SPT skin friction
  fav = 0.02 pa N60 (high-displacement) / 0.01 pa N60 (low-displacement),
  Briaud fav = 0.224 pa N60^0.29 (PDF pp590-591).
- `Duncan_Wright_Brandon_Soil_Strength_and_Slope_Stability_2ed_2014.pdf`
  (333 pp) — closes the Spencer gap (Spencer content pp98-126; chart
  appendix near the end, pp321-333 region; digitise when a Spencer chain
  is built).
- `Geotechnical_Design_Manual_Ch17_Embankments_2022.pdf` (69 pp, agency
  design manual) — LRFD slope stability practice, embankment failure
  mechanisms, settlement; reference material for a future embankment domain.

## POLICY — poorly digitized sources (user decision 2026-08-07)

NAVFAC DM-7.01/7.02 (Osterberg chart etc.) will NOT be digitised: the scans
are too poor to extract honestly. Instead, when a solve needs a value from
such a chart, the app asks the READER to look the value up (naming the
document, figure and entry arguments) and answer via the clarification flow;
the value is then used with provenance "reader-supplied chart reading".
This becomes a clarification type when such a chain is first built.

## B4. Phoon & Kulhawy (1999) — DIGITIZED (2026-08-08)

`Phoon_Kulhawy_1999_Characterization_of_Geotechnical_Variability_CGJ.pdf`
(CGJ 36(4) 612-624; verified from the text layer). Digitized into
`tables/phoon_kulhawy_1999.py` and wired as the ADVISORY TIER in
solver.`_phoon_advisory` (warn + proceed; hard bounds in units.py refuse):
- Table 1 (p. 615): strength-property variability incl. phi-bar sand
  35-41 deg (COV 5-11), clay/silt 9-33 deg (COV 10-50)
- Table 2 (p. 616): index parameters incl. gamma 14-20 kN/m3 (COV 3-20),
  gamma_d 13-18, wn 13-105 %
- Table 7 (p. 621): guidelines used for the advisory ranges (phi 20-40 deg
  COV 5-15; su UC 10-400 / UU 10-350 / CIUC 150-700 kPa)

## C. Remaining wants — none blocking

- (minor) A Cc correlation source — or accept the standard published equations
  (Terzaghi-Peck Cc = 0.009(LL-10), Skempton) with citation.
- Verify whether Spencer's own charts are reproduced in the Hunter & Schuster
  compilation (else use Duncan & Wright above).

## User-supplied excerpts (2026-08-07) — taken vs deliberately left

TAKEN (verified consistent with existing regression-tested anchors):
- Meyerhof pile Nq* per-degree table, phi 20-45 (matched all 6 prior anchors
  exactly; corrected 45 from 1174 to 930) -> now in domains/pile.py
- Confirmations (already implemented, no change needed): Meyerhof limiting
  ql = 0.5 pa Nq* tan(phi); Vesic sand sigma-bar = (1+2K0)/3 * q', K0 = 1-sin(phi),
  N-sigma = 3 Nq/(1+2K0)

RECORDED FOR FUTURE (standard published closed forms, not yet built as chains):
- Vesic pile point in CLAY (undrained): Qp = Ap cu Nc*, with
  Nc* = 4/3 (ln Irr + 1) + pi/2 + 1, Ir = Es/(3 cu), Irr = Ir undrained
- Meyerhof clay point: Qp = 9 cu Ap
- SPT pile point (granular): qp = 0.4 pa N60 (L/D) <= 4 pa N60 (Meyerhof);
  Briaud et al. 1985: qp = 19.7 pa (N60)^0.36
- CPT pile point: qp = Ccpt * qc-bar (avg qc within ~1.5D of the tip)

LEFT OUT ON PURPOSE (doubt rule — verify against the original before use):
- Poulos (1989) Cb table and the Ccpt constants table (Jardine 2005 /
  Lee & Salgado 1999): plausible but unverified against the originals; do not
  bake into the solver until checked.
- (RESOLVED 2026-08-07 later) Coyle & Castello: the Das PDF arrived and both
  charts were digitized exactly — see B3 below.

## Structured extraction format (for future table JSON files in this folder)

```json
{
  "id": "coyle_castello_nq",
  "source": {"book": "...", "figure": "...", "pdf_file": "...", "pdf_page": 0},
  "quantity": "Nq_star", "inputs": ["phi_deg", "L_over_D"],
  "units": {"phi_deg": "degree", "L_over_D": "1", "Nq_star": "1"},
  "valid_range": {"phi_deg": [30, 45], "L_over_D": [5, 100]},
  "anchors": [[30, 10, 25.0], ...],
  "interpolation": "log-linear in Nq_star over phi, linear over L_over_D",
  "tolerance": "chart-reading, ±8 %",
  "extrapolation": "forbid"
}
```

Loader contract: each JSON registers one callable in `FACTOR_FUNCTIONS` under its
`id`; the YAML formula registry references it by name; provenance cards are
auto-generated from `source` + `tolerance`; out-of-range input -> honest rejection
naming the range, never silent extrapolation.
