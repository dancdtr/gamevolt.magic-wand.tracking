"""Hand-curated product selection: which spells ship in the theme-park experience.

Loaded from `spells/data/spell_selection.yml` — authored by hand, kept apart from
the PDF-extracted `spell_info.yml` so a lore re-run cannot clobber it. Keyed by
`SpellType`, same key templates and lore use.

Product-only, like lore: inclusion is UX/curation and never gates a cast (the
recognizer still matches every template). Absent key => not included; a missing
file warns once and yields the empty set. Contrast the SVG template loader, which
fails loud — a broken template breaks recognition; a missing selection does not.
"""

from __future__ import annotations

from pathlib import Path

from gamevolt.io.utils.yaml import load_yaml_if_exists
from gamevolt.logging import Logger
from spells.spell_type import SpellType


def spell_selection_path() -> Path:
    # spells/spell_selection.py -> spells/data/spell_selection.yml
    return Path(__file__).resolve().parent / "data" / "spell_selection.yml"


def load_included_spells(logger: Logger, path: Path | None = None) -> frozenset[SpellType]:
    """Build the set of spells included in the theme-park experience.

    A missing file warns once and yields the empty set. Keys with no matching
    `SpellType` are logged at debug (a typo) since selection is product-only and
    never gates a cast.
    """
    path = path or spell_selection_path()
    data = load_yaml_if_exists(path)
    if data is None:
        logger.warning(f"spell selection file not found: {path} (no spells marked included)")
        return frozenset()

    keys = data.get("included") or []
    known = {s.value: s for s in SpellType if s is not SpellType.NONE}

    included: set[SpellType] = set()
    unknown: list[str] = []
    for key in keys:
        spell = known.get(key)
        if spell is None:
            unknown.append(key)
        else:
            included.add(spell)

    if unknown:
        logger.debug(f"spell selection: {len(unknown)} entries with no matching SpellType (ignored): {', '.join(sorted(unknown))}")

    return frozenset(included)
