# Linked-Scene Specification (council synthesis, 2026-08-13)

GEOTUTOR LINKED-SCENE SPECIFICATION (SYNTHESIS OF DESIGNERS 1, 2, 3)

Repo: e:\YORK.A\Python codes2\BIN\Antigrav
Server files: src\designmode\domains\generic.py
Client files: geotutor\client\src\components\designmode\{SceneFigure.tsx, figShared.ts, StepPlayer.tsx, types.ts}, new geotutor\client\src\lib\figureLint.ts
Test files: tests\visual\* (new), tests\test_visual_lint.py (new)

CONFLICT RESOLUTIONS (applied throughout, per priority order: step-element link correctness > no visual defects > latency > effort)

- C1. Highlight namespace. Designer 1's separate viz ops win over Designer 2's "accept ids inside highlight". The symbol namespace ("highlight") and the element-id namespace stay disjoint. To preserve Designer 2's three-state rendering, the link is emitted as TWO ops, not one: "focus" for elements carrying the step's output, "support" for elements carrying the step's input symbols and the model's advisory extras. The client never parses formulas; there is no "uses" field. Python, which already knows the formula symbols, does the split. This keeps the load-bearing link fully deterministic and server-side.
- C2. Chips. Designer 2's in-SVG chips win for scene figures (a CSS-pixel HTML overlay over a scaled SVG cannot be made collision-safe, so defect class 1 and 2 are unfixable in HTML). Designer 1's "StepPlayer untouched" is relaxed to: StepPlayer's FigureOverlay stops rendering note chips when the figure template is "scene" with schema >= 2; dedicated figures keep the HTML overlay exactly as today (no regression), and Designer 3's lint rule R4 polices them.
- C3. Call budget. Designer 1's merged plan+scene call wins: 2 calls happy path (open givens, then plan+scene), 3 worst case on a plan retry, same worst case as today.
- C4. Defect detection is two independent layers. Designer 2's layout engine PREVENTS overlaps and asserts its own report; Designer 3's lint VERIFIES from outside in screen space, covering dedicated figures and the HTML/SVG boundary the layout engine cannot see. Neither replaces the other.
- C5. Zero-lint gate with waivers. New violations always fail; day-one benign overlaps in dedicated figures go into waivers.json with a burn-down list, so the gate ships immediately without blocking on hand-tuned figures.

====================================================================
1. FINAL JSON CONTRACT
====================================================================

1.1 LLM calls. Call 1 (OPEN_SYSTEM, open givens) is unchanged. Call 2 uses a new PLAN_SCENE_SYSTEM that merges today's PLAN_SYSTEM and SCENE_SYSTEM into one strict-JSON response. SCENE_SYSTEM as a separate call is deleted. The merge is what makes linking possible: step highlights can only reference element ids if both halves live in one JSON.

1.2 Merged response shape:

```
{
  "feasible": true,
  "missing": [],                        // plain language, only when feasible=false
  "method": "Terzaghi bearing capacity",
  "steps": [ PlanStep, ... ],           // max 15
  "answers": [ {"target": "q_all", "quantity": "q_all", "unit": "kPa"} ],
  "scene": {
    "elements": [ SceneElement, ... ],  // 3..30
    "missing": []                       // plain-language GEOMETRY facts absent from
                                        // the problem; non-empty is NOT an error
  }
}
```

1.3 PlanStep = today's step plus one optional field:

```
{
  "target": "q_net",                    // ^[A-Za-z_][A-Za-z_0-9]*$, unique, not a given
  "formula": "Q / (B * L)",             // <=300 chars, closed vocabulary, unchanged
  "unit": "kPa",
  "title": "Net bearing pressure",
  "why": "one teaching sentence",
  "highlights": ["el_footing"]          // NEW, optional, <=6 element ids: elements the
                                        // reader should look at during this step
}
```

1.4 SceneElement = today's element plus one required field:

```
{
  "id": "el_footing",                   // NEW: ^el_[a-z0-9_]{1,30}$, unique in scene
  "type": "footing",                    // unchanged closed set of 10 types
  ... numeric fields per type ...,      // unchanged
  "label": "B",                         // unchanged
  "label_from": "B"                     // unchanged: symbol; renderer fills the value
}
```

Prompt rule: "Give every element an id of the form el_<what_it_is>, unique, lowercase. In each step's highlights, list ids of elements a reader should look at while following that step. In scene.missing list, in plain language, geometry the drawing would need that the problem does not state. Draw what is known anyway."

1.5 Persisted link: emitted into each step's viz, the same mechanism the dedicated builders use. Two new viz ops reuse the existing VizOp shape (op + target):

```
{"op": "focus",   "target": "el_footing"}   // element carries this step's OUTPUT
{"op": "support", "target": "el_q_arrow"}   // element carries an INPUT symbol, or advisory
```

A compute step's viz becomes, for example:
```
[{"op":"highlight","target":"q_net"},        // unchanged, symbol namespace
 {"op":"focus","target":"el_footing"},
 {"op":"support","target":"el_q_arrow"}]
```
Old clients ignore unknown ops silently. Dedicated builders never emit focus or support, so nothing changes for them.

1.6 Figure params (template "scene"), versioned:

```
{
  "template": "scene",
  "schema": 2,                          // ids + focus/support ops present;
                                        // absent or 1 = legacy label_from-only
  "elements": [...],                    // now carry "id"
  "method": "...", "values": {...}, "answer": {...},   // unchanged
  "orphans": ["el_dashed_spread"],      // ids never focused/supported by any step
  "layout": { "placed": n, "moved": n, "leadered": n,
              "truncated": n, "dropped": n }   // written client-side, see section 3
}
```

1.7 types.ts additions, all optional and additive: `El.id?: string`; `FigureParams.schema?: number; orphans?: string[]`. VizOp is unchanged in shape ("focus" and "support" are just op values).

1.8 Deterministic linking algorithm (Python, in build(), after validation, no LLM):

```
by_symbol = {}                                    # symbol -> [element ids]
for e in elements:
    if e.get("label_from"):
        by_symbol.setdefault(e["label_from"], []).append(e["id"])

scope = set(givens)
for step in steps:
    primary  = list(by_symbol.get(step["target"], ()))          # output elements
    inputs   = symbols_in(step["formula"]) & scope              # reuse _SYM_RE
    supp     = [eid for s in inputs for eid in by_symbol.get(s, ())]
    supp    += [h for h in step.get("highlights", [])
                if h in id_set and h not in primary and h not in supp]
    step_focus[step["target"]]   = primary[:4]
    step_support[step["target"]] = [e for e in supp if e not in primary][:6]
    scope.add(step["target"])
```

Conclude step: focus = by_symbol[answer_target] plus step_focus of the answer target; support = its step_support. Per-step cap: 4 focus + 6 support (model advisory extras are dropped first). Guarantee: any element whose label_from is the step's target or one of its formula symbols lights on that step, with or without model cooperation. That is requirement (a), and it is exactly the property that makes the dedicated builders work.

====================================================================
2. VALIDATION RULES AND FALLBACK LADDER
====================================================================

The two halves validate SEPARATELY and fail SEPARATELY. A broken scene never kills a valid plan; a broken plan kills everything (numbers first). Only plan violations trigger the single retry, and the retry regenerates the whole merged object.

Plan half (extends existing _validate; existing rules kept):
- P1 steps <= 15 .......................................... reject plan (retry)
- P2 target matches _SYM_RE, unique, shadows no given ...... reject plan (retry)
- P3 formula symbols all in givens, earlier targets, _SAFE_FUNCS ... reject plan (retry)
- P4 formula length <= 300 ................................ reject plan (retry)
- P5 every answers[].target is a step target ............... reject plan (retry)
- P6 highlights is a list of <=6 strings ................... repair: coerce/truncate, never reject

Scene half (repair-first; the scene must be hard to lose):
- S1 element type in the closed set of 10 .................. drop element
- S2 numeric fields finite, |v| <= 500 ..................... drop element
- S3 id matches ^el_[a-z0-9_]{1,30}$ and unique ............ repair: assign el_<type>_<n>
- S4 label_from matches _SYM_RE AND names a given or step target ... repair: drop label_from, keep element
- S5 >=3 elements survive and at least one of soil/footing/pile/wall ... scene invalid, fall to calc_chain
- S6 scene.missing entries are strings, <=6, <=80 chars .... repair: truncate

Link rules (cross-half; all repairs, never rejections):
- L1 every highlights id exists in the element id set ...... drop unknown id, log
- L2 coverage floor: each compute step focuses at least the elements whose label_from is its target ... guaranteed by construction (1.8)
- L3 orphan elements (no step lights them, no label_from) ... keep drawing, record in figure.orphans
- L4 orphan symbols (label_from in no formula, no answer) ... keep, log warning (context labels are fine)
- L5 caps 4 focus / 6 support per step ..................... truncate, advisory extras first

Fallback ladder (top = best; every rung honest, no silent degrade):
- R0 merged call ok, plan valid, scene valid ......... linked scene, full step sync
- R1 plan valid, scene degraded (S-repairs applied) .. linked scene minus dropped parts
- R2 plan valid, scene invalid (S5) or absent ........ calc_chain figure; when scene.missing is non-empty, the assume step narration gains: "The drawing omits what the problem did not state: <items>. Add these facts in the chat for a complete cross-section."
- R3 plan invalid .................................... one merged retry with violations named
- R4 retry invalid ................................... existing honest refusal text
- R5 feasible=false .................................. existing "More information is needed" clarify flow, from plan.missing
- R6 step eval error or non-finite result ............ existing per-step honest error
- R7 LLMUnavailable .................................. existing maintenance message

Invariants: no rung ever shows a number Python did not compute; no rung shows a drawing whose labels could contradict a step (labels fill from the values map only).

Clarify loop, two tiers: plan.missing (feasible=false) is a hard stop through the existing chat re-ask; scene.missing is soft, the computation runs and the notice travels in the assume step plus the R2 sentence. When the user supplies geometry in a follow-up, the normal re-run regenerates the merged artifact with a full scene. ClarifyCard untouched, no new UI.

====================================================================
3. RENDERER LAYOUT ENGINE AND RESERVED REGIONS
====================================================================

3.1 Chips move in-SVG for scene figures. FigureOverlay stops rendering note chips when template is "scene" and schema >= 2; comparison bars move below the figure card, outside the canvas. Dedicated figures keep the HTML overlay untouched this round. In-SVG chip geometry: rect rx=14, height 26, right-aligned stack pinned at x1=712, fill #ffffff opacity 0.95, stroke rgba(37,99,235,0.4) w1.2 (blue family per house style), text fontSize 13 monospace fill INK, 12px side padding, cap 4 chips.

3.2 Reserved regions (720x460 viewBox units):

```
R_CHIPS   = (418, 8, 712, 8 + 30*n + 6*(n-1))   n = occupied chip rows this step; max y1 = 146
R_BADGE   = (720 - bw - 24, 406, 712, 452)      bw = measured badge width, cap 300
R_DIMLANE = (14, GY - 6, leftEdge - 2, 452)     leftEdge = sx(xMin), about 110
R_SOILCOL = (leftEdge + 4, GY, leftEdge + 4 + maxSoilNameWidth, sy(deepest))
R_SKY     = (leftEdge, 8, rightEdge, GY - 4)    load arrows and their labels only
R_MARGIN  = 8px inset on all four sides; no glyph box may cross it
```

Rules: R_CHIPS is recomputed per step and returns territory when empty. Scene labels never intersect R_CHIPS or R_BADGE (fixes the chip-over-"q = 120 kPa" defect). dim_v labels live only inside R_DIMLANE; dim_h labels in the strip below their tick line; neither enters R_BADGE. Badge and chips are placed last and win ties by evicting scene labels to alternate candidates, never the reverse.

3.3 Layout pass (pure function inside SceneFigure before emitting JSX; no getBBox, no DOM measurement):

Text width estimator: `w(text, fs) = fs * (0.62*wide + 0.56*normal + 0.30*narrow) + 10`, box height = fs + 6. wide = W M m w and subscript/superscript glyphs; narrow = i l j t f r I . , ' space. The +10 covers halo bleed. Always round up; whitespace is free, overlap is a defect. Unicode subscripts (gamma_sat, sigma prime) count as wide; never break inside a symbol token.

Algorithm:
1. Collect label items: every element's resolved label, each chip, the badge, as {id, text, fs, anchor, candidates, priority}.
2. Seed occupancy with the static regions plus coarse geometry boxes text must not cover: footing/pile rects inflated 4px, strut circles, water-table symbol block, 8x8 squares at every dim tick endpoint (fixes the "D = 8 m" on-tick defect), extension-line endpoints.
3. Sort by priority: badge 0, chips 1, PRIMARY element label 2, load labels 3, dim labels 4, dashed/aux 5, soil names 6.
4. Try candidates in order; first non-intersecting box wins and joins the occupancy list. Ladders: load_arrow right of shaft, left of shaft, above tail, leader. dim_v left of lane, step down 16px up to 4 times testing full boxes, rotate -90 on the lane, leader into R_DIMLANE free space. dim_h below line, above line, leader. dashed higher endpoint, other endpoint, midpoint above, leader. soil name layer top+22, layer center, leader if layer under 20px tall.
5. Leader fallback (always succeeds): free 18px rows in the nearest margin band, leader stroke FIG.DIM w1 dasharray 2 3, 2.5px dot at the anchor, leader must not cross a placed box. Cap 2 leaders per figure; beyond that the label's text joins the chip stack instead.
6. Clamp and shrink: shift inside R_MARGIN; fs 14 to 12.5; then truncate. Chips: max 34 chars, split at first "=", NEVER truncate the value+unit side, middle-ellipse the name side (first 14 + U+2026 + last 6). Scene labels: max 22 chars, first 9 + U+2026 + last 4. If the sanitizer strips U+2026, fall back to two dots. Answer badge: measure with the estimator, not length*8.2, check BEFORE building the rect; over 24 chars switch to "answer: value unit"; still over 300px, drop to fs 13.
7. Emit the layout report {placed, moved, leadered, truncated, dropped} onto figure params and a data-layout attribute on the svg root. The engine asserts zero residual intersections; the lint verifies that claim from outside.

Determinism: stable sort, no randomness; identical elements always produce identical placement, so snapshots are testable.

====================================================================
4. HIGHLIGHT RENDERING STATES
====================================================================

4.1 State resolution per element per step (pure, no formula parsing on the client):
- PRIMARY: e.id is in activeEls(steps, current) for op "focus", OR legacy path: e.label_from is in activeTargets or equals the current step's result symbol.
- SUPPORTING: e.id is in the set for op "support".
- RECEDED: everything else, only when focus is on (some element is primary or supporting this step).
- REST: all elements, when no step lights anything.

figShared.ts gains:
```
export function activeEls(steps, current): Set<string>      // ops with op === "focus"
export function supportEls(steps, current): Set<string>     // ops with op === "support"
```

4.2 Attribute table (matches the dedicated figures' feel):

| element type | rest | SUPPORTING | PRIMARY |
|---|---|---|---|
| footing/pile/wall body | fill #c9ced6, stroke INK w2 | stroke HL(#f59e0b) w2.4 | fill #fde68a, stroke HL w3, glow underlay |
| strut/load_arrow/dashed | stroke INK/SLIP w3/1.8 | stroke HL w3.5 | stroke HL w4.5, glow, arrowhead swaps to amber marker #arrSceneAmber (add to defs) |
| dim_v/dim_h | stroke DIM w1.2, text DIM | stroke HL w1.8, text #b45309 | stroke HL w2.4, text #b45309 weight 600 |
| water_table | WATER dashed | + w2.2 | + w2.6, glow |
| soil layer | tinted fill | never glow a whole layer; promote its margin name to amber | same |
| labels | INK/DIM, halo | amber | amber, weight 600, fontSize +1 |

RECEDED: annotation text and dims opacity 0.45; structural bodies and soil opacity floor 0.75, never lower (the scene must stay readable).

4.3 Glow underlay: a duplicate shape drawn BEFORE the element, geometry inflated 6px, fill FIG.HL opacity 0.30 for bodies; for lines a duplicate line stroke FIG.HL width base+8 opacity 0.25 linecap round. No SVG filters (feGaussianBlur is slow on scrub and inconsistent across browsers).

4.4 Transition: style={{transition: "opacity 180ms ease, stroke 180ms ease, fill 180ms ease"}}; set strokeWidth via style too. No delay, so arrow-key scrubbing feels instant.

4.5 Honest fallback: a step resolving zero primary and zero supporting elements fades NOTHING (focus=false). A fully lit static figure is honest; a faded figure with nothing lit reads as broken.

====================================================================
5. FIGURE LINT (RUNTIME + PLAYWRIGHT BATTERY + DEPLOY GATE)
====================================================================

5.1 Module: geotutor\client\src\lib\figureLint.ts, framework-free, about 200 lines, exposed as window.__figLint = {run, last} unconditionally (a few bytes) so Playwright can use production preview builds.

Instrumentation (one-line changes, zero behavior change): StepPlayer figure container gets data-fig-root and data-fig-step={current} and data-step-count; FigureOverlay wrapper gets data-fig-overlay, each chip and compare row gets data-lint-chip; SceneFigure tags dim groups data-part="dim" (dedicated figures adopt incrementally, nothing breaks if they do not); SceneFigure's in-SVG chips also carry data-lint-chip.

Node collection inside [data-fig-root]: whole SVG text elements (getBBox per element, never per tspan), discarding empty, hidden, effective opacity < 0.05, zero-size; HTML [data-lint-chip] boxes (the chip box is the occluder, chips are opaque); line-like graphics (line, polyline, stroked fill:none paths). hasHalo = paint-order includes stroke AND stroke luminance > 0.85 AND stroke-width >= 2.

Coordinate space: screen space via getBoundingClientRect for all pairwise tests (the defect class that bit us is HTML over SVG, which getBBox cannot see); getBBox only for R1. Ink insets before pairwise tests: text rects shrink insetY = min(0.18h, 4px) and insetX = 1.5px; chip rects are not inset.

Rules (each violation = {rule, step, nodes, rects, ratio, msg}):
- R1 OUT-OF-VIEWBOX: every SVG text getBBox inside (0,0,720,460) expanded 2 units.
- R2 CLIPPED-BY-ANCESTOR: effective clip rect = intersection of client rects of every non-visible-overflow ancestor and the viewport; violation if a text node or chip loses more than 1px on any side. This is the long-answer-chip defect.
- R3 TEXT-ON-TEXT: pairwise inset text rects (SVG-SVG, SVG-HTML, HTML-HTML); ratio = interArea / min(areaA, areaB) > 0.10 is a violation. Halo never excuses text over text. Exceptions: data-lint="allow-overlap" on either node, or shared data-lint-group.
- R4 CHIP-OVER-LABEL: any opaque chip rect intersecting any inset SVG text rect after 2px pad. This is the chip-over-"q = 120 kPa" defect; also covers the compare panel.
- R5 LINE-THROUGH-TEXT: line via Liang-Barsky, path/polyline via getPointAtLength sampling every 6px. Inside data-part="dim": ANY crossing of ANY text is a violation, halo or not (an interrupted tick reads as broken). Elsewhere: violation only when the text has no halo (halo text sits on leaders and hatch by design). A segment terminating within 3px of the rect edge is exempt (leaders pointing at their label).
- R6 LAYOUT-REPORT-MISMATCH (new, ties Designer 2 to Designer 3): if the svg root carries data-layout claiming zero drops and the lint finds R3/R4/R5 violations among elements the layout engine placed, report both the violation and the mismatch, so estimator drift is caught, not silently absorbed.

Runtime wiring in StepPlayer (dev or ?figlint=1): double requestAnimationFrame plus await document.fonts.ready, run lint, store window.__figLint.last, console.warn violations, paint red-outline divs over offending rects. Full pass under 5ms on 20-60 nodes.

5.2 Playwright battery. Deterministic, no LLM calls, no API keys: fixtures are captured solution payloads (steps + figure JSON, the exact shape StepPlayer consumes). Dev-only loader in useDesign.ts reads ?figfixture=<name> and fetches /fixtures/<name>.json.

```
tests\visual\
  playwright.config.ts     # webServer pnpm --dir geotutor dev (reuseExistingServer),
                           # chromium only, screenshots only-on-failure -> artifacts\
                           # PREVIEW=1 targets the built preview server
  figure-lint.spec.ts      # one spec, parameterized over fixtures
  waivers.json             # {fixture, step, rule, textPrefix} tuples
  fixtures\
    footing.json slope.json braced_cut.json pile.json wall.json
    phases.json classification.json permeability.json consolidation.json
    generic_load_arrow.json    # reproducer: chip near "q = 120 kPa"
    generic_long_answer.json   # reproducer: long answer chip at pane edge
    generic_deep_dims.json     # reproducer: "D = 8 m" tick collision
    generic_water_table.json
  artifacts\               # gitignored
```

Spec loop: for each fixture, load, walk every step via the step-next control, waitForFunction on data-fig-step, await fonts.ready, page.evaluate window.__figLint.run(), filter waivers, screenshot on violation, expect.soft so one run reports every bad step of every fixture. Failure message carries rule, step index and title, first 40 chars of offending text, rounded rects, ratio, actionable from the console alone.

Waivers: dedicated figures were tuned by eye; day-one benign overlaps go in waivers.json, counted in the run summary as a burn-down list. New violations always fail. Preferred permanent fix is data-lint="allow-overlap" in the component, then delete the waiver.

5.3 Integration and gate.

pytest bridge tests\test_visual_lint.py, marker "visual" registered in pyproject.toml, skipped unless GEOTUTOR_VISUAL=1 and pnpm present; runs the Playwright battery via subprocess and asserts returncode 0. The five-point programme in ASSURANCE_PLAN.md gains its visual point through the same pytest front door; envelope/property/adversarial suites stay fast via -m "not visual".

Root package.json:
```
"figlint":   "pnpm --dir geotutor exec playwright test -c ../tests/visual/playwright.config.ts",
"predeploy": "pnpm --dir geotutor build && PREVIEW=1 pnpm --dir geotutor exec playwright test -c ../tests/visual/playwright.config.ts"
```
DEPLOY.md gains one line before railway up: "Figure lint green on localhost: pnpm run predeploy (zero non-waived violations, waivers reviewed)." One-time setup: pnpm --dir geotutor add -D @playwright/test; pnpm --dir geotutor exec playwright install chromium.

====================================================================
6. MIGRATION NOTE (SAVED SESSIONS AND DEDICATED FIGURES)
====================================================================

- Old scene figures (no schema field, elements without id, steps without focus/support ops): the new isActive degrades to exactly the current label_from behavior; activeEls and supportEls return empty sets. Renders identically to today. No data migration.
- Old calc_chain and "none" figures: untouched code paths.
- New solutions on an old client build: unknown viz ops "focus"/"support" and unknown fields id/schema/orphans/layout are ignored by the existing shapes (VizOp is op plus optional target; El fields are optional). Safe in both directions.
- Dedicated figures: zero changes to their builders, viz emission, or SVG components this round. They never emit focus/support, FigureOverlay keeps serving them, and they are nine of the thirteen lint fixtures, so any accidental regression fails the battery. figShared additions (activeEls, supportEls, estimateTextWidth, Rect, intersects, resolveState) are additive; dedicated figures may adopt resolveState later.
- schema: 2 exists so the auditor and future tooling branch on it instead of sniffing.

====================================================================
7. ORDERED IMPLEMENTATION CHECKLIST
====================================================================

Canonical retest problem, used after EVERY step below: the surcharge footing problem from the user's screenshot (load arrow "q = 120 kPa", embedment "D = 8 m", long-name answer), saved immediately in step 0 as fixtures generic_load_arrow.json, generic_long_answer.json, generic_deep_dims.json. The user's rule: after every fix, re-run the same problem and look.

Step 0. Capture fixtures FIRST (before any code changes), so today's defects are pinned as failing baselines.
- Run the app, submit the canonical problems, save the solution payloads into tests\visual\fixtures\ (all 13 files listed in 5.2).
- Test: fixtures load via a temporary JSON sanity script; visually confirm the three defects still reproduce.

Step 1. Lint module and instrumentation (detector before fixes, so every later step is measured).
- New geotutor\client\src\lib\figureLint.ts (rules R1-R6, screen space, insets, halo policy).
- StepPlayer.tsx: data-fig-root, data-fig-step, data-step-count, dev-mode useEffect wiring, red-outline debug overlay. FigureOverlay: data-fig-overlay, data-lint-chip.
- Test: run the canonical problem with ?figlint=1; the console MUST report R4 (chip over q label), R2 (clipped answer chip), R5 (D = 8 m ticks). If the lint stays silent on known defects, fix the lint before proceeding.

Step 2. Playwright battery and gate plumbing.
- tests\visual\playwright.config.ts, figure-lint.spec.ts, waivers.json (empty), useDesign.ts ?figfixture loader, tests\test_visual_lint.py, pyproject marker, package.json scripts, DEPLOY.md line, .gitignore artifacts.
- Test: pnpm run figlint goes RED on the three generic reproducers and (apart from waived items) green on the nine dedicated fixtures. Triage dedicated-figure hits into waivers.json with a burn-down comment.

Step 3. Server contract: merged call, ids, deterministic link (src\designmode\domains\generic.py).
- PLAN_SCENE_SYSTEM replacing PLAN_SYSTEM + SCENE_SYSTEM; _scene becomes _clean_scene (pure validation, S1-S6); new _link_steps (section 1.8); _validate gains P6; build() restructured per the ladder (R0-R7), emitting focus/support ops, schema 2, orphans, and the scene.missing sentence.
- Test: pytest tests -m "not visual" (existing suites green); run the canonical problem end to end; inspect the payload: every compute step carries focus ops for its target's elements; numbers unchanged from before the refactor; re-run one problem per dedicated domain to confirm dedicated payloads are byte-identical.

Step 4. Client types and shared helpers (types.ts, figShared.ts).
- El.id, FigureParams.schema/orphans; activeEls, supportEls, estimateTextWidth, Rect, intersects, resolveState.
- Test: build passes; canonical problem renders exactly as before (helpers not yet consumed); dedicated figures unchanged.

Step 5. Highlight states in SceneFigure.tsx (link first, per priority order).
- Three-state resolution (4.1), attribute table, glow underlays, amber marker, transitions, honest no-fade fallback, legacy label_from path preserved.
- Test: step through the canonical problem; every compute step lights its output element(s) amber and its input elements dimmer; a schema-1 saved session still renders as today; pnpm run figlint (layout defects still expected RED, highlight work must not add new violations).

Step 6. Layout engine and in-SVG chips (SceneFigure.tsx, StepPlayer.tsx).
- Reserved regions, occupancy pass, candidate ladders, leader fallback, truncation rules, badge measurement fix, layout report on data-layout and figure params; FigureOverlay stops rendering note chips for scene schema >= 2; comparison bars move below the card.
- Test: canonical problem again, all three original defects must be gone by eye AND pnpm run figlint fully green on the three generic reproducers; nine dedicated fixtures unchanged (no new violations, waiver count not increased).

Step 7. Full battery, burn-down, gate rehearsal.
- GEOTUTOR_VISUAL=1 pytest tests -m visual green; pnpm run predeploy green against the built preview bundle; review waivers.json and delete any now-fixed entries.
- Test: run five fresh out-of-bag problems (not fixtures) with ?figlint=1, zero console violations, highlights track every step; re-run the canonical problem one final time.

Step 8. Fixture refresh and commit.
- Re-capture the three generic fixtures from the fixed pipeline (they now double as regression pins for schema 2), keep the old ones as *_legacy.json to pin backward compatibility.
- Test: full battery green; pytest all suites green; then commit. Deploy only after the DEPLOY.md line is satisfied.

Files touched, in order: tests\visual\fixtures\* (0), geotutor\client\src\lib\figureLint.ts + StepPlayer.tsx (1), tests\visual\* + tests\test_visual_lint.py + package.json + DEPLOY.md (2), src\designmode\domains\generic.py (3), types.ts + figShared.ts (4), SceneFigure.tsx highlights (5), SceneFigure.tsx layout + StepPlayer.tsx overlay (6), waivers.json (7), fixtures refresh (8).

House rules honored throughout: LLM plans, Python computes, numbers never come from the model; strict JSON with deterministic validation for everything the model drafts; honest fallbacks at every rung; no em-dashes in any user-facing string (U+2026 ellipsis only, with the two-dot fallback if the sanitizer strips it); the banned word appears nowhere in labels, chips, aria text, or lint messages; two-call happy path preserved; dedicated figures regress nowhere and are guarded by nine always-on fixtures.