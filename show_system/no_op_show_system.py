from spells.spell_cast_quality import SpellCastQuality
from spells.spell_type import SpellType
from wizards.hogwarts_house import HogwartsHouse


class NoOpShowSystem:
    """Show system disabled: spell casts are dropped, no UDP is sent. See ShowSystem."""

    def play_spell(self, wand_id: str, spell_type: SpellType, quality: SpellCastQuality, house: HogwartsHouse) -> None:
        return None
