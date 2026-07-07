from enum import StrEnum, auto


class SpellTag(StrEnum):
    """Provenance / curation tags. Every spell carries one or more:

    - PRIMER: extracted from the Spells Primer PDF (derived: everything not CDTR).
    - PARK: ships in the theme-park experience (hand-curated Primer subset).
    - CDTR: a CDTR original, not in the Primer.

    Assignments live in spells/data/spell_tags.yml (see spells/spell_tags.py).
    """

    PRIMER = auto()
    PARK = auto()
    CDTR = auto()
