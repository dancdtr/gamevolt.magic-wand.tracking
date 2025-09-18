from classification.gesture_type import GestureType as G
from spells.spell import Spell
from spells.spell_type import SpellType

_SPELLS = [
    Spell(is_implemented=True, id="SP00", type=SpellType.NONE, definition=[G.NONE]),
    Spell(is_implemented=True, id="SP01", type=SpellType.REVELIO, definition=[G.CROOK_N_CW, G.LINE_SE]),
    Spell(is_implemented=True, id="SP02", type=SpellType.LOCOMOTOR, definition=[G.LINE_N, G.LINE_SW, G.LINE_E]),
    Spell(is_implemented=True, id="SP03", type=SpellType.ARRESTO_MOMENTUM, definition=[G.LINE_NNE, G.LINE_SSE, G.LINE_NNE, G.LINE_SSE]),
    Spell(is_implemented=True, id="SP04", type=SpellType.WINGARDIUM_LEVIOSA, definition=[G.ARC_180_CCW_START_W, G.LINE_S]),
    Spell(is_implemented=True, id="SP05", type=SpellType.METEOLOJINX, definition=[G.ARC_180_CCW_START_E, G.ARC_180_CW_START_W]),
    Spell(is_implemented=False, id="SP06", type=SpellType.COLOVARIA, definition=[G.NONE]),
    Spell(is_implemented=True, id="SP07", type=SpellType.SLUGULUS_ERECTO, definition=[G.LINE_S, G.LINE_WSW, G.LINE_N, G.LINE_ENE]),
    Spell(is_implemented=True, id="SP08", type=SpellType.VENTUS, definition=[G.LINE_SSE, G.LINE_NNE]),
    Spell(is_implemented=False, id="SP09", type=SpellType.RICTUMSEMPRA, definition=[G.NONE]),
    Spell(is_implemented=True, id="SP10", type=SpellType.REPARO, definition=[G.ARC_450_CW_START_W]),
    Spell(is_implemented=True, id="SP11", type=SpellType.PIERTOTUM_LOCOMOTOR, definition=[G.LINE_SW, G.LINE_E, G.LINE_N]),
    Spell(is_implemented=True, id="SP12", type=SpellType.ALOHOMORA, definition=[G.ARC_360_CW_START_N, G.LINE_S]),
    Spell(is_implemented=True, id="SP13", type=SpellType.COLLOPORTUS, definition=[G.LINE_E, G.LINE_S, G.LINE_W, G.LINE_S]),
    Spell(is_implemented=True, id="SP14", type=SpellType.SILENCIO, definition=[G.ARC_180_CW_START_E, G.LINE_S]),
    Spell(is_implemented=True, id="SP15", type=SpellType.INCENDIO, definition=[G.LINE_NNE, G.LINE_SSE, G.LINE_W]),
    Spell(is_implemented=True, id="SP16", type=SpellType.INFLATUS, definition=[G.ARC_180_CW_START_W]),
    Spell(is_implemented=True, id="SP17", type=SpellType.IMMOBULUS, definition=[G.LINE_NW, G.LINE_E, G.LINE_SW]),
    Spell(is_implemented=False, id="SP18", type=SpellType.APARECIUM, definition=[G.LINE_W, G.WAVE_SINE_720_E]),
    Spell(is_implemented=True, id="SP19", type=SpellType.ENGORGIO, definition=[G.LINE_ESE, G.LINE_WSW]),
    Spell(is_implemented=True, id="SP20", type=SpellType.SWITCHING, definition=[G.LINE_SSE, G.LINE_E]),
    Spell(is_implemented=False, id="SP21", type=SpellType.CANTIS, definition=[G.NONE]),
    Spell(is_implemented=True, id="SP22", type=SpellType.PEPPER_BREATH, definition=[G.FLICK_CCW_NE, G.FLICK_CCW_SE]),
    Spell(is_implemented=False, id="SP23", type=SpellType.VERA_VERTO, definition=[G.NONE]),
    Spell(is_implemented=True, id="SP24", type=SpellType.DENSAUGEO, definition=[G.LINE_S, G.LINE_SW, G.LINE_S]),
    Spell(is_implemented=True, id="SP25", type=SpellType.HORN_TONGUE, definition=[G.FLICK_CW_SE, G.LINE_NE, G.LINE_SSW]),
    Spell(is_implemented=True, id="SP26", type=SpellType.FLIPENDO, definition=[G.LINE_SE, G.WAVE_SINE_360_E]),
    Spell(is_implemented=True, id="SP27", type=SpellType.EXPECTO_PATRONUM, definition=[G.ARC_450_CW_START_E]),
    Spell(is_implemented=True, id="SP28", type=SpellType.LUMOS_MAXIMA, definition=[G.LINE_NNE, G.LINE_SSE]),
    Spell(is_implemented=True, id="SP29", type=SpellType.HERBIVICIUS, definition=[G.LINE_S, G.ARC_180_CW_START_W]),
    Spell(is_implemented=False, id="SP30", type=SpellType.NEBULUS, definition=[G.NONE]),
]


class SpellFactory:
    def __init__(self) -> None:
        self._spells: dict[SpellType, Spell] = {spell.type: spell for spell in _SPELLS}

    def create(self, spell_type: SpellType) -> Spell:
        spell = self._spells.get(spell_type)
        if spell is None:
            raise KeyError(f"No spell defined for type: {spell_type}!")

        return spell
