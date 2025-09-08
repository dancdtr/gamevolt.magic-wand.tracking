from classification.classifiers.spells.spell import Spell
from classification.gesture_type import GestureType
from spell_type import SpellType

_SPELLS = [
    Spell(
        type=SpellType.NONE,  # 0
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
    Spell(
        type=SpellType.METEOLOJINX,  # 5
        definition=[
            GestureType.ARC_180_CCW_START_E,
            GestureType.ARC_180_CW_START_W,
        ],
    ),
    Spell(type=SpellType.COLOVARIA, definition=[]),
    Spell(type=SpellType.SLUGULUS_ERECTO, definition=[]),
    Spell(type=SpellType.VENTUS, definition=[]),
    Spell(type=SpellType.RICTUSEMPRA, definition=[]),
    Spell(type=SpellType.REPARO, definition=[]),
    Spell(type=SpellType.PIERTOTUM_LOCOMOTOR, definition=[]),
    Spell(type=SpellType.ALOHOMORA, definition=[]),
    Spell(type=SpellType.COLLOPORTUS, definition=[]),
    Spell(type=SpellType.SILENCIO, definition=[]),
    Spell(type=SpellType.INCENDIO, definition=[]),
    Spell(type=SpellType.INFLATUS, definition=[]),
    Spell(type=SpellType.IMMOBULUS, definition=[]),
    Spell(type=SpellType.APARECIUM, definition=[]),
    Spell(type=SpellType.ENGORGIO, definition=[]),
    Spell(type=SpellType.SQITCHING, definition=[]),
    Spell(type=SpellType.CANTIS, definition=[]),
    Spell(type=SpellType.PEPPER_BREATH, definition=[]),
    Spell(type=SpellType.VERA_VERTO, definition=[]),
    Spell(type=SpellType.DENSAUGEO, definition=[]),
    Spell(type=SpellType.HORN_TONGUE, definition=[]),
    Spell(type=SpellType.FLIPENDO, definition=[]),
    Spell(type=SpellType.EXPECTO_PATRONUM, definition=[]),
    Spell(type=SpellType.LUMOS_MAXIMA, definition=[]),
    Spell(type=SpellType.HERBIVICIUS, definition=[]),
    Spell(type=SpellType.NEBULUS, definition=[]),
]


class SpellFactory:
    def __init__(self) -> None:
        self._spells: dict[SpellType, Spell] = {spell.type: spell for spell in _SPELLS}

    def create(self, type: SpellType) -> Spell:
        spell = self._spells.get(type)
        if spell is None:
            raise KeyError(f"No spell defined for type: {type}!")

        return spell
