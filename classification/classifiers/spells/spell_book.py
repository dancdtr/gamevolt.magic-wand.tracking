from classification.classifiers.spells.spell import Spell
from classification.gesture_type import GestureType
from spell_type import SpellType

_SPELLS = [
    Spell(
        type=SpellType.NONE,
        definition=[],
    ),
    Spell(
        type=SpellType.REVELIO,  # 1
        definition=[GestureType.CROOK_N_CW, GestureType.LINE_SE],
    ),
    Spell(
        type=SpellType.LOCOMOTOR,  # 2
        definition=[
            GestureType.LINE_N,
            GestureType.LINE_SW,
            GestureType.LINE_E,
        ],
    ),
    Spell(
        type=SpellType.ARRESTO_MOMENTUM,  # 3
        definition=[
            GestureType.LINE_NNE,
            GestureType.LINE_SSE,
            GestureType.LINE_NNE,
            GestureType.LINE_SSE,
        ],
    ),
    Spell(
        type=SpellType.WINGARDIUM_LEVIOSA,  # 4
        definition=[
            GestureType.ARC_180_CCW_START_W,
            GestureType.LINE_S,
        ],
    ),
]


class SpellBook:
    def __init__(self) -> None:
        self._spells: dict[SpellType, Spell] = {spell.type: spell for spell in _SPELLS}

    def get(self, type: SpellType) -> Spell:
        spell = self._spells.get(type)
        if spell is None:
            raise KeyError(f"No spell defined for type: {type}!")

        return spell
