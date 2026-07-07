"""Hand-curated spell tags: which spells are in the park, which are CDTR originals.

Loaded from `spells/data/spell_tags.yml` — authored by hand, kept apart from the
PDF-extracted `spell_info.yml` so a lore re-run cannot clobber it. Keyed by
`SpellType` value, same key templates and lore use.

`PRIMER` is derived, never listed: every spell not tagged `cdtr` came from the
Primer PDF. `park` and `cdtr` are explicit lists.

Product-only, like lore: tags are UX/curation (the settings-panel spell filter)
and never gate a cast — the recognizer still matches every template. A missing
file warns once and degrades to all-PRIMER; a key with no matching `SpellType`
is logged at debug (a typo). Contrast the SVG template loader, which fails loud —
a broken template breaks recognition; a missing tag does not.
"""

from __future__ import annotations

from pathlib import Path

from gamevolt.io.utils.yaml import load_yaml_if_exists
from gamevolt.logging import Logger
from spells.spell_tag import SpellTag
from spells.spell_type import SpellType


def spell_tags_path() -> Path:
    # spells/spell_tags.py -> spells/data/spell_tags.yml
    return Path(__file__).resolve().parent / "data" / "spell_tags.yml"


def load_spell_tags(logger: Logger, path: Path | None = None) -> dict[SpellType, frozenset[SpellTag]]:
    """Build the tag registry: one non-empty `frozenset[SpellTag]` per `SpellType`
    (except NONE).

    A missing file warns once and yields all-PRIMER. Keys with no matching
    `SpellType` are logged at debug (a typo) since tags are product-only and
    never gate a cast.
    """
    path = path or spell_tags_path()
    data = load_yaml_if_exists(path)
    if data is None:
        logger.warning(f"spell tags file not found: {path} (all spells tagged {SpellTag.PRIMER})")
        data = {}

    known = {s.value: s for s in SpellType if s is not SpellType.NONE}

    def read(tag: SpellTag) -> set[SpellType]:
        spells: set[SpellType] = set()
        unknown: list[str] = []
        for key in data.get(tag.value) or []:
            spell = known.get(key)
            if spell is None:
                unknown.append(key)
            else:
                spells.add(spell)
        if unknown:
            logger.debug(f"spell tags: {len(unknown)} '{tag}' entries with no matching SpellType (ignored): {', '.join(sorted(unknown))}")
        return spells

    park = read(SpellTag.PARK)
    cdtr = read(SpellTag.CDTR)

    registry: dict[SpellType, frozenset[SpellTag]] = {}
    for spell in known.values():
        tags = {SpellTag.CDTR} if spell in cdtr else {SpellTag.PRIMER}
        if spell in park:
            tags.add(SpellTag.PARK)
        registry[spell] = frozenset(tags)
    return registry
