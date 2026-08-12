"""Domain builders for the design solver.

Each module exposes build(frame, givens, add, problem_text) -> dict with
keys: results, conclusions, comparison (or None), figure, and optionally
error. The solver owns framing, clarifications, narration and audit; a
builder owns the deterministic step chain and the figure parameters of its
domain. Every number a builder emits is computed here in full precision,
never recalled from a model.
"""

from . import basics, braced, consolidation, permeability, pile, \
    retaining, slope

DOMAIN_BUILDERS = {
    "soil_basics": basics.build,
    "slope_stability": slope.build,
    "excavation": braced.build,
    "pile_foundation": pile.build,
    "retaining_wall": retaining.build,
    "consolidation": consolidation.build,
    "permeability": permeability.build,
}

# label shown in the "Applicable" chip before solving
DOMAIN_METHOD_LABEL = {
    "soil_basics": "Phase relations",
    "slope_stability": "Slope stability",
    "excavation": "Peck apparent-pressure envelope",
    "pile_foundation": "Pile capacity and settlement",
    "retaining_wall": "Retaining structures",
    "consolidation": "Consolidation",
    "permeability": "Permeability and seepage",
    "soil_classification": "Soil classification",
}

# classification lands from a parallel build; keep boot resilient until
# the module is present, then it wires itself in
try:
    from . import classify
    DOMAIN_BUILDERS["soil_classification"] = classify.build
except ImportError:
    pass
