"""Domain builders for the design solver.

Each module exposes build(frame, givens, add, problem_text) -> dict with
keys: results, conclusions, comparison (or None), figure, and optionally
error. The solver owns framing, clarifications, narration and audit; a
builder owns the deterministic step chain and the figure parameters of its
domain. Every number a builder emits is computed here in full precision,
never recalled from a model.
"""

from . import basics, braced, consolidation, pile, retaining, slope

DOMAIN_BUILDERS = {
    "soil_basics": basics.build,
    "slope_stability": slope.build,
    "excavation": braced.build,
    "pile_foundation": pile.build,
    "retaining_wall": retaining.build,
    "consolidation": consolidation.build,
}

# label shown in the "Applicable" chip before solving
DOMAIN_METHOD_LABEL = {
    "soil_basics": "Phase relations",
    "slope_stability": "Slope stability",
    "excavation": "Peck apparent-pressure envelope",
    "pile_foundation": "Pile capacity and settlement",
    "retaining_wall": "Retaining structures",
    "consolidation": "Terzaghi time-rate of consolidation",
}
