"""Static per-spell lore (name, nickname, description, classification, …).

Loaded from `spells/data/spell_info.yml` — reference copy shown in the visualiser,
kept out of appsettings (bulky, never changes, no runtime behaviour). Keyed by
`SpellType`, same key the SVG templates use.

Lore is UX-only: missing spells or fields degrade gracefully (blank / title-cased
fallback), they never gate a cast. Contrast the SVG template loader, which fails
loud — a broken template breaks recognition; missing lore does not.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from gamevolt.io.types import YamlObject
from gamevolt.io.utils.yaml import load_yaml_if_exists
from gamevolt.logging import Logger
from spells.spell_type import SpellType


@dataclass(frozen=True)
class SpellInfo:
    """Reference lore for one spell. Every field has a benign default."""

    display_name: str = ""
    nickname: str = ""
    description: str = ""
    classification: str = ""
    difficulty: str = ""
    pronunciation: str = ""
    notable_uses: str = ""
    source: str = ""


def spell_info_path() -> Path:
    # spells/spell_info.py -> spells/data/spell_info.yml
    return Path(__file__).resolve().parent / "data" / "spell_info.yml"


def _default_display_name(spell: SpellType) -> str:
    # PIERTOTUM_LOCOMOTOR -> "Piertotum Locomotor"
    return spell.name.replace("_", " ").title()


def _from_entry(spell: SpellType, entry: YamlObject) -> SpellInfo:
    return SpellInfo(
        display_name=entry.get("display_name") or _default_display_name(spell),
        nickname=entry.get("nickname", ""),
        description=entry.get("description", ""),
        classification=entry.get("classification", ""),
        difficulty=entry.get("difficulty", ""),
        pronunciation=entry.get("pronunciation", ""),
        notable_uses=entry.get("notable_uses", ""),
        source=entry.get("source", ""),
    )


def load_spell_info(logger: Logger, path: Path | None = None) -> dict[SpellType, SpellInfo]:
    """Build the lore registry: one `SpellInfo` per `SpellType` (except NONE).

    Spells absent from the YAML get a fallback `SpellInfo` (title-cased display name,
    blank fields). A missing file warns once and yields all-fallback entries — the
    visualiser still runs.

    The YAML is auto-extracted from the Spells Primer and is keyed 1:1 with the
    gesture templates, so it normally covers every `SpellType`. A key with no matching
    enum member would be a typo; those are logged at debug (not a warning) since lore
    is UX-only and never gates a cast.
    """
    path = path or spell_info_path()
    data = load_yaml_if_exists(path)
    if data is None:
        logger.warning(f"spell lore file not found: {path} (using fallback names)")
        data = {}

    known = {s.value: s for s in SpellType if s is not SpellType.NONE}
    unknown = [k for k in data if k not in known]
    if unknown:
        logger.debug(f"spell lore: {len(unknown)} entries with no matching SpellType (lore-only): {', '.join(sorted(unknown))}")

    registry: dict[SpellType, SpellInfo] = {}
    for value, spell in known.items():
        entry = data.get(value)
        if entry is None:
            registry[spell] = SpellInfo(display_name=_default_display_name(spell))
        else:
            registry[spell] = _from_entry(spell, entry)
    return registry
