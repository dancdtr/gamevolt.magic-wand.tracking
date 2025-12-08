from logging import Logger

from spells.spell import Spell
from spells.spell_type import SpellType

_DEFAULT_SPELL = Spell(id=0, code="SP00", type=SpellType.NONE)

_SPELLS = [
    _DEFAULT_SPELL,
    Spell(id=1, code="SP01", type=SpellType.REVELIO),
    Spell(id=2, code="SP02", type=SpellType.LOCOMOTOR),
    Spell(id=3, code="SP03", type=SpellType.ARRESTO_MOMENTUM),
    Spell(id=4, code="SP04", type=SpellType.WINGARDIUM_LEVIOSA),
    Spell(id=5, code="SP05", type=SpellType.METEOLOJINX),
    Spell(id=6, code="SP06", type=SpellType.COLOVARIA),
    Spell(id=7, code="SP07", type=SpellType.SLUGULUS_ERECTO),
    Spell(id=8, code="SP08", type=SpellType.VENTUS),
    Spell(id=9, code="SP09", type=SpellType.RICTUMSEMPRA),
    Spell(id=10, code="SP10", type=SpellType.REPARO),
    Spell(id=11, code="SP11", type=SpellType.PIERTOTUM_LOCOMOTOR),
    Spell(id=12, code="SP12", type=SpellType.ALOHOMORA),
    Spell(id=13, code="SP13", type=SpellType.COLLOPORTUS),
    Spell(id=14, code="SP14", type=SpellType.SILENCIO),
    Spell(id=15, code="SP15", type=SpellType.INCENDIO),
    Spell(id=16, code="SP16", type=SpellType.INFLATUS),
    Spell(id=17, code="SP17", type=SpellType.IMMOBULUS),
    Spell(id=18, code="SP18", type=SpellType.APARECIUM),
    Spell(id=19, code="SP19", type=SpellType.ENGORGIO),
    Spell(id=20, code="SP20", type=SpellType.SWITCHING),
    Spell(id=21, code="SP21", type=SpellType.CANTIS),
    Spell(id=22, code="SP22", type=SpellType.PEPPER_BREATH),
    Spell(id=23, code="SP23", type=SpellType.VERA_VERTO),
    Spell(id=24, code="SP24", type=SpellType.DENSAUGEO),
    Spell(id=25, code="SP25", type=SpellType.HORN_TONGUE),
    Spell(id=26, code="SP26", type=SpellType.FLIPENDO),
    Spell(id=27, code="SP27", type=SpellType.EXPECTO_PATRONUM),
    Spell(id=28, code="SP28", type=SpellType.LUMOS_MAXIMA),
    Spell(id=29, code="SP29", type=SpellType.HERBIVICIUS),
    Spell(id=30, code="SP30", type=SpellType.NEBULUS),
]


class SpellList:
    def __init__(self, logger: Logger) -> None:
        self._logger = logger

        self._spells_by_type: dict[SpellType, Spell] = {spell.type: spell for spell in _SPELLS}
        self._spells_by_code: dict[str, Spell] = {spell.code: spell for spell in _SPELLS}
        self._spells_by_id: dict[int, Spell] = {spell.id: spell for spell in _SPELLS}

    @property
    def items(self) -> list[Spell]:
        return list(_SPELLS)

    @property
    def names(self) -> list[str]:
        return [spell.name for spell in _SPELLS]

    @property
    def long_names(self) -> list[str]:
        return [spell.long_name for spell in _SPELLS]

    @property
    def ids(self) -> list[int]:
        return [spell.id for spell in _SPELLS]

    @property
    def codes(self) -> list[str]:
        return [spell.code for spell in _SPELLS]

    @property
    def count(self) -> int:
        return len(_SPELLS)

    def get_default(self) -> Spell:
        return _DEFAULT_SPELL

    def get_by_name(self, name: str) -> Spell:
        return next((spell for spell in _SPELLS if spell.name.casefold() == name.casefold()), _DEFAULT_SPELL)

    def get_by_type(self, type: SpellType) -> Spell:
        spell = self._spells_by_type.get(type)
        if spell is None:
            self._logger.error(f"No spell defined for type: {type}!")
            return _DEFAULT_SPELL

        return spell

    def get_by_id(self, id: int) -> Spell:
        spell = self._spells_by_id.get(id)
        if spell is None:
            self._logger.error(f"No spell defined with id: {id}!")
            return _DEFAULT_SPELL

        return spell

    def get_by_code(self, code: str) -> Spell:
        spell = self._spells_by_code.get(code)
        if spell is None:
            self._logger.error(f"No spell defined with code: {code}!")
            return _DEFAULT_SPELL

        return spell
