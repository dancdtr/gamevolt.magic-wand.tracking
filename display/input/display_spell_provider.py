import tkinter as tk
from collections.abc import Callable
from logging import Logger

from display.input.display_spell_entry import DisplaySpellEntry
from display.input.drop_down import DropDown
from display.input.key_input import KeyInput
from display.input.numeric_input import NumericInput
from gamevolt.events.event import Event
from spells.spell import Spell
from spells.spell_factory import SpellFactory
from spells.spell_provider_base import SpellProviderBase
from spells.spell_type import SpellType

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
    9: SpellType.RICTUMSEMPRA,
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
    20: SpellType.SWITCHING,
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


class DisplaySpellProvider(SpellProviderBase):
    def __init__(self, logger: Logger, spell_factory: SpellFactory, root: tk.Misc) -> None:
        super().__init__(logger)
        self._spell_factory = spell_factory

        self._spell_entries: list[DisplaySpellEntry] = [
            DisplaySpellEntry(
                id=spell_id,
                type=spell_type,
                dropdown_name=f"{spell_id}{_DIVIDER}{spell_type.name.lower()}",
            )
            for spell_id, spell_type in _SPELL_TYPE_MAPPINGS.items()
        ]

        self._by_id: dict[int, DisplaySpellEntry] = {e.id: e for e in self._spell_entries}
        self._by_type: dict[SpellType, DisplaySpellEntry] = {e.type: e for e in self._spell_entries}
        self._by_dropdown: dict[str, DisplaySpellEntry] = {e.dropdown_name.casefold(): e for e in self._spell_entries}

        self._dropdown = DropDown(root, [e.dropdown_name for e in self._spell_entries])

        self._key_input = KeyInput(root)
        self._numeric_input = NumericInput(root)

        self._target_spells: list[Spell] = []
        self._current_spell_entry_index = 0

        self._target_spells_updated: Event[Callable[[list[Spell]], None]] = Event()
        self._toggle_history: Event[Callable[[], None]] = Event()
        self._quit: Event[Callable[[], None]] = Event()

    @property
    def target_spells_updated(self) -> Event[Callable[[list[Spell]], None]]:
        return self._target_spells_updated

    @property
    def toggle_history(self) -> Event[Callable[[], None]]:
        return self._toggle_history

    @property
    def quit(self) -> Event[Callable[[], None]]:
        return self._quit

    @property
    def target_spells(self) -> list[Spell]:
        return self._target_spells

    def start(self) -> None:
        self._key_input.quit.subscribe(self._on_quit)
        self._key_input.cycle_spell.subscribe(self._on_cycle_spell)
        self._key_input.toggle_history.subscribe(self._on_toggle_history_visibility)

        self._dropdown.updated.subscribe(self._on_dropdown_updated)
        self._numeric_input.updated.subscribe(self._on_numeric_input_updated)

    def stop(self) -> None:
        self._key_input.toggle_history.unsubscribe(self._on_toggle_history_visibility)
        self._key_input.cycle_spell.unsubscribe(self._on_cycle_spell)
        self._key_input.quit.unsubscribe(self._on_quit)

        self._numeric_input.updated.unsubscribe(self._on_numeric_input_updated)
        self._dropdown.updated.unsubscribe(self._on_dropdown_updated)

    def _on_numeric_input_updated(self, spell_id: int) -> None:
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

        self._current_spell_entry_index = next(idx for idx, spell_type in _SPELL_TYPE_MAPPINGS.items() if spell_type is target)
        self._target_spells = [self._spell_factory.create(t) for t in targets]

        for spell in self._target_spells:
            if not spell.is_implemented:
                self._logger.warning(f"Spell '{spell.name}' is not yet implemented! You will be unable to cast. 💀")

        self.target_spells_updated.invoke(self._target_spells)

    def _on_cycle_spell(self, idx_adjustment: int) -> None:
        target_idx = self._current_spell_entry_index + idx_adjustment
        clamped_target_idx = max(0, min(target_idx, len(_SPELL_TYPE_MAPPINGS) - 1))

        if clamped_target_idx == self._current_spell_entry_index:
            return

        self._on_numeric_input_updated(clamped_target_idx)

    def _on_quit(self) -> None:
        self._quit.invoke()

    def _on_toggle_history_visibility(self) -> None:
        self._toggle_history.invoke()
