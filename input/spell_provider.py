import tkinter as tk
from abc import ABC
from collections.abc import Callable
from dataclasses import dataclass
from logging import Logger

from classification.classifiers.spells.spell import Spell
from classification.classifiers.spells.spell_factory import SpellFactory
from gamevolt.events.event import Event
from input.dropdown import Dropdown
from input.numeric_input import NumericInput
from spell_type import SpellType

_SPELL_TYPE_MAPPINGS = {
    0: SpellType.NONE,
    1: SpellType.REVELIO,
    2: SpellType.LOCOMOTOR,
    3: SpellType.ARRESTO_MOMENTUM,
    4: SpellType.WINGARDIUM_LEVIOSA,
    5: SpellType.METEOLOJINX,
    6: SpellType.COLOVARIA,
    7: SpellType.SLUGULUS_ERECTO,
    8: SpellType.VENTUS,
    9: SpellType.RICTUSEMPRA,
    10: SpellType.REPARO,
    11: SpellType.PIERTOTUM_LOCOMOTOR,
    12: SpellType.ALOHOMORA,
    13: SpellType.COLLOPORTUS,
    14: SpellType.SILENCIO,
    15: SpellType.INCENDIO,
    16: SpellType.INFLATUS,
    17: SpellType.IMMOBULUS,
    18: SpellType.APARECIUM,
    19: SpellType.ENGORGIO,
    20: SpellType.SQITCHING,
    21: SpellType.CANTIS,
    22: SpellType.PEPPER_BREATH,
    23: SpellType.VERA_VERTO,
    24: SpellType.DENSAUGEO,
    25: SpellType.HORN_TONGUE,
    26: SpellType.FLIPENDO,
    27: SpellType.EXPECTO_PATRONUM,
    28: SpellType.LUMOS_MAXIMA,
    29: SpellType.HERBIVICIUS,
    30: SpellType.NEBULUS,
}

_DIVIDER = " - "


@dataclass(frozen=True)
class SpellEntry:
    id: int
    type: SpellType
    dropdown_name: str  # eg "12 - alohomora"


class SpellProviderBase(ABC):
    def __init__(self, logger: Logger) -> None:
        super().__init__()
        self._logger = logger

    @property
    def target_spells(self) -> list[Spell]: ...

    def start(self) -> None: ...

    def stop(self) -> None: ...

    @property
    def target_spells_updated(self) -> Event[Callable[[list[Spell]], None]]: ...


class SpellProvider(SpellProviderBase):
    def __init__(self, logger: Logger, spell_factory: SpellFactory, root: tk.Misc) -> None:
        super().__init__(logger)
        self._spell_factory = spell_factory

        self._spell_entries: list[SpellEntry] = [
            SpellEntry(
                id=spell_id,
                type=spell_type,
                dropdown_name=f"{spell_id}{_DIVIDER}{spell_type.name.lower()}",
            )
            for spell_id, spell_type in _SPELL_TYPE_MAPPINGS.items()
        ]

        self._by_id: dict[int, SpellEntry] = {e.id: e for e in self._spell_entries}
        self._by_type: dict[SpellType, SpellEntry] = {e.type: e for e in self._spell_entries}
        self._by_dropdown: dict[str, SpellEntry] = {e.dropdown_name.casefold(): e for e in self._spell_entries}

        self._dropdown = Dropdown(root, [e.dropdown_name for e in self._spell_entries])
        self._key_input = NumericInput(root)

        self._target_spells: list[Spell] = []

        self._target_spells_updated: Event[Callable[[list[Spell]], None]] = Event()

    @property
    def target_spells_updated(self) -> Event[Callable[[list[Spell]], None]]:
        return self._target_spells_updated

    @property
    def target_spells(self) -> list[Spell]:
        return self._target_spells

    def start(self) -> None:
        self._key_input.updated.subscribe(self._on_key_input_updated)
        self._dropdown.updated.subscribe(self._on_dropdown_updated)

        self._on_targets_updated(SpellType.NONE)  # set a default spell to start

    def stop(self) -> None:
        self._key_input.updated.unsubscribe(self._on_key_input_updated)
        self._dropdown.updated.unsubscribe(self._on_dropdown_updated)

    def _on_key_input_updated(self, spell_id: int) -> None:
        entry = self._by_id.get(spell_id)
        if entry is not None:
            self._on_targets_updated(entry.type)
        else:
            self._logger.warning("Unknown spell id: %s", spell_id)

    def _on_dropdown_updated(self, value: str) -> None:
        entry = self._by_dropdown.get(value.casefold())
        if entry is not None:
            self._on_targets_updated(entry.type)
        else:
            self._logger.warning(f"Unknown dropdown value: {value}")

    def _on_targets_updated(self, target: SpellType) -> None:
        self._logger.info(f"Setting spell target to: {target.name}")

        entry = self._by_type.get(target)
        if entry is not None:
            self._dropdown.show_value(entry.dropdown_name)

        targets = [target]  # TODO temp until support added for multiple simultaneous spell targets
        self._target_spells = [self._spell_factory.create(t) for t in targets]
        self._target_spells_updated.invoke(self._target_spells)
