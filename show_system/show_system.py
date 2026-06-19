from spells.spell_cast_quality import SpellCastQuality
from spells.spell_type import SpellType
from wizards.hogwarts_house import HogwartsHouse


class ShowSystem:
    """Notifies external show-control hardware of recognised spell casts.

    Implemented by ShowSystemController (UDP fan-out) and NoOpShowSystem (disabled)."""

    def play_spell(self, wand_id: str, spell_type: SpellType, quality: SpellCastQuality, house: HogwartsHouse) -> None: ...
