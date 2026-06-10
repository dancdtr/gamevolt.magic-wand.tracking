from messaging.show_system_spell_cast_message import ShowSystemSpellCastMessage
from spells.spell_cast_quality import SpellCastQuality
from spells.spell_type import SpellType
from wizards.hogwarts_house import HogwartsHouse

spell_type = SpellType.ALOHOMORA
quality: SpellCastQuality = SpellCastQuality.SKILLED
house: HogwartsHouse = HogwartsHouse.GRYFFINDOR

message = ShowSystemSpellCastMessage(spell_type, quality, house)

x = message.to_dict()

print(x)
