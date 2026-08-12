# GeoTutor Design: Capability Assurance and Testing Plan

Recorded 2026-08-12. This is the standing plan for answering, with
evidence instead of claims, the question: *can the system deal with any
geotechnical design problem, any geometry, complex geology?*

## The three-tier capability model (the honest frame for "any problem")

- **Tier 1 - Dedicated, verified procedures.** Deterministic builders
  with benchmark-verified arithmetic. Geometry is *parametrized*, not
  arbitrary: slopes accept polyline surfaces, layered profiles, per-layer
  water (dry / r_u / piezometric), non-toe circles, Culmann planes,
  infinite slopes, with Spencer cross-verification; footings accept
  strip/square/rectangular/circular with eccentric and moment loading and
  any water table; walls, piles, cuts, phases, permeability,
  consolidation, classification cover their standard configurations.
- **Tier 2 - General reasoning mode.** Any problem reducible to a chain
  of closed-form calculations over scalar givens: the model PLANS the
  method as strict JSON over the closed symbol set, Python executes every
  number, the answer carries the "general mode, verify independently"
  label, and infeasible plans surface the missing information for the
  chat loop. This covers most hand-solvable problems outside Tier 1.
- **Tier 3 - Out of honest reach without a numerical engine.** Arbitrary
  2-D/3-D geometry with irregular stratigraphy (zoned dams, tunnels,
  coupled seepage-deformation) is finite-element territory. The
  guarantee here is refusal instead of fabrication. Roadmap: the vendored
  xslope package contains a strength-reduction FE module, deliberately
  not activated; activating it under the same verification discipline as
  the slope kernel is the path to Tier 3 for slopes first.

## The five-point assurance programme

1. **Capability envelope, written down and machine-readable.** One map
   per domain: geometry parameters and their ranges, layer counts, water
   conditions, loading types. Everything inside the envelope is
   guaranteed by tests; everything outside must PROVABLY refuse or route
   to Tier 2 with the warning label. Untested capability claims are
   worthless. (Implementation: an `envelope.yaml` per domain next to the
   registry, consumed by the test generator below and by the honest
   refusal messages.)

2. **Property-based stress testing.** Generate thousands of random valid
   parameter combinations per domain and assert PHYSICS INVARIANTS that
   must hold without knowing the answer:
   - factor of safety falls as a slope steepens, rises with c and phi;
   - bearing capacity rises with phi, B, and depth; falls as the water
     table rises;
   - a symmetric problem gives a symmetric answer;
   - every result degenerates to the textbook closed form at parameter
     limits (e.g. rectangular -> strip as L grows; layered -> homogeneous
     as properties equalize; Coulomb -> Rankine as delta and batter -> 0,
     verified already at Ka = 0.3333).
   This tests "any geometry within the envelope" rather than "the five
   geometries someone thought of".

3. **Adversarial geometry sweeps.** Deliberately weird-but-valid inputs:
   razor-thin layers, near-vertical slopes, the water table exactly at a
   layer interface, B = L exactly, values at regime boundaries
   (gamma*H/c = 4 exactly). This is the bug class that exposed the
   missing Peck 0.3*gamma*H floor; hunt it systematically, in the live
   pipeline, not just unit tests.

4. **Cross-verification everywhere a second engine exists.** Spencer
   already checks Bishop with a 0.1 % hand-off guard; add a
   Morgenstern-Price chip and the strength-reduction FE check for triple
   redundancy on slopes; method-vs-method comparison already plays this
   role for footings (Terzaghi/Meyerhof/Hansen/Vesic) and piles
   (Meyerhof/Coyle-Castello/Vesic). Disagreement is displayed, never
   averaged away.

5. **Tier-2 audit loop (the growth engine).** Every general-mode
   solution a user flags with thumbs-down arrives in the feedback email
   batches; each flagged problem becomes a candidate for promotion to a
   dedicated, verified Tier-1 builder with hand-checked cases. The
   guaranteed envelope grows exactly where real users push it.

## Status ledger

- 2026-08-12: three-tier model in production (generic mode live and
  verified on a 1-D elastic compression case, 14.9 mm exact). Points 1-4
  are NOT yet implemented; this document is the commitment. Point 5 is
  live end-to-end (feedback -> email -> review).
- Benchmark evidence so far: 539-problem external set, round 1 vs
  round 2 comparison in D:\GEOTUTOR_BENCH (run1/, run2/,
  REVISION_REPORT.md).
