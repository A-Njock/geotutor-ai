"""Geotechnical symbol/synonym dictionary for query expansion.

Maps the short forms engineers actually type (su, phi', Cc, qc ...) to the
full terms that appear in books and papers, so both the vector search and the
keyword search can find passages that never spell out the symbol.

Keys are matched case-insensitively against whole words in the query.
"""

GLOSSARY: dict[str, list[str]] = {
    # strength
    "su": ["undrained shear strength"],
    "cu": ["undrained shear strength", "undrained cohesion"],
    "phi": ["friction angle", "angle of shearing resistance"],
    "phi'": ["effective friction angle", "angle of shearing resistance"],
    "c'": ["effective cohesion"],
    "ucs": ["unconfined compressive strength"],
    "qu": ["ultimate bearing capacity", "unconfined compressive strength"],
    # consolidation / compressibility
    "cc": ["compression index"],
    "cs": ["swelling index", "recompression index"],
    "cr": ["recompression index"],
    "cv": ["coefficient of consolidation"],
    "mv": ["coefficient of volume compressibility"],
    "e0": ["initial void ratio"],
    "ocr": ["overconsolidation ratio"],
    "pc": ["preconsolidation pressure"],
    # in-situ tests
    "cpt": ["cone penetration test"],
    "cptu": ["piezocone test", "cone penetration test"],
    "qc": ["cone tip resistance", "cone resistance"],
    "fs": ["sleeve friction", "factor of safety"],
    "spt": ["standard penetration test"],
    "n60": ["SPT blow count corrected", "standard penetration test"],
    "vane": ["field vane shear test"],
    "dmt": ["flat dilatometer test"],
    "pmt": ["pressuremeter test"],
    # bearing capacity / foundations
    "nc": ["bearing capacity factor"],
    "nq": ["bearing capacity factor"],
    "ngamma": ["bearing capacity factor"],
    "df": ["founding depth", "depth of embedment"],
    "fos": ["factor of safety"],
    "fs=": ["factor of safety"],
    # index properties
    "ll": ["liquid limit"],
    "pl": ["plastic limit"],
    "pi": ["plasticity index"],
    "gs": ["specific gravity of solids"],
    "w%": ["water content", "moisture content"],
    "dr": ["relative density"],
    "emax": ["maximum void ratio"],
    "emin": ["minimum void ratio"],
    # stress / stiffness
    "k0": ["coefficient of earth pressure at rest"],
    "ka": ["active earth pressure coefficient"],
    "kp": ["passive earth pressure coefficient"],
    "sigma'": ["effective stress"],
    "u": ["pore water pressure"],
    "g0": ["small-strain shear modulus"],
    "gmax": ["small-strain shear modulus"],
    "vs": ["shear wave velocity"],
    "es": ["soil modulus", "modulus of elasticity of soil"],
    # seepage
    "k": ["hydraulic conductivity", "coefficient of permeability"],
    "i": ["hydraulic gradient"],
    "ic": ["critical hydraulic gradient", "soil behaviour type index"],
    # earthquake
    "crr": ["cyclic resistance ratio"],
    "csr": ["cyclic stress ratio"],
    "msf": ["magnitude scaling factor"],
    "pga": ["peak ground acceleration"],
    "amax": ["peak ground acceleration"],
    # rock
    "rqd": ["rock quality designation"],
    "gsi": ["geological strength index"],
    "rmr": ["rock mass rating"],
    "jrc": ["joint roughness coefficient"],
    # common named methods (help BM25 find the right chapters)
    "terzaghi": ["Terzaghi bearing capacity"],
    "meyerhof": ["Meyerhof bearing capacity"],
    "vesic": ["Vesic bearing capacity"],
    "skempton": ["Skempton bearing capacity factor"],
    "camclay": ["Cam-Clay critical state model"],
    "cam-clay": ["Cam-Clay critical state model"],
    "mohr": ["Mohr-Coulomb failure criterion"],
    "hoek": ["Hoek-Brown failure criterion"],
    "casagrande": ["Casagrande method"],
    "bishop": ["Bishop method of slices slope stability"],
    "janbu": ["Janbu method slope stability"],
    "morgenstern": ["Morgenstern-Price method slope stability"],
}


def expand_query(query: str) -> list[str]:
    """Return extra search phrases implied by symbols in the query."""
    import re
    tokens = set(t.lower() for t in re.findall(r"[A-Za-z][A-Za-z0-9'\-=%]*", query))
    extras: list[str] = []
    for tok in tokens:
        for phrase in GLOSSARY.get(tok, []):
            if phrase.lower() not in query.lower() and phrase not in extras:
                extras.append(phrase)
    return extras
