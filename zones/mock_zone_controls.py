from __future__ import annotations

import tkinter as tk
from collections.abc import Callable

from display.input.drop_down import DropDown
from display.input.numeric_input import NumericInput
from display.input.spell_visualiser_key_input import SpellVisualiserKeyInput
from gamevolt.events.event import Event
from gamevolt.logging import Logger
from spells.control.spell_target_store import SpellTargetStore
from spells.spell import Spell
from spells.spell_registry import SpellRegistry
from zones.mock_zone_manager import MockZoneManager


class MockZoneControls:
    def __init__(
        self, logger: Logger, spell_registry: SpellRegistry, zone_manager: MockZoneManager, root: tk.Misc, parent: tk.Misc | None = None
    ) -> None:
        self.quit: Event[Callable[[], None]] = Event()

        self._zone_manager = zone_manager
        self._logger = logger

        self._dropdown = DropDown(parent or root, {k: v for k, v in zip(spell_registry.ids, spell_registry.names)})
        self._spell_store = SpellTargetStore(logger, spell_registry)
        self._key_input = SpellVisualiserKeyInput(root)
        self._numeric_input = NumericInput(root)

    async def start_async(self) -> None:
        self._spell_store.target_spell_updated.subscribe(self._on_target_spell_updated)
        self._numeric_input.updated.subscribe(self._on_numeric_input_updated)
        self._key_input.cycle_spell.subscribe(self._on_cycle_spell)
        self._dropdown.updated.subscribe(self._on_dropdown_updated)
        self._key_input.quit.subscribe(self._on_quit)

    async def stop_async(self) -> None:
        self._spell_store.target_spell_updated.unsubscribe(self._on_target_spell_updated)
        self._numeric_input.updated.unsubscribe(self._on_numeric_input_updated)
        self._key_input.cycle_spell.unsubscribe(self._on_cycle_spell)
        self._dropdown.updated.unsubscribe(self._on_dropdown_updated)
        self._key_input.quit.unsubscribe(self._on_quit)

    def _on_target_spell_updated(self, spell: Spell) -> None:
        self._zone_manager.set_spell(spell)

    def _on_numeric_input_updated(self, spell_id: int) -> None:
        self._logger.verbose(f"Numeric input updated: {spell_id}")
        self._spell_store.set_target_by_id(spell_id)
        self._dropdown.show_value(self._spell_store.current_index)

    def _on_dropdown_updated(self, value: int) -> None:
        self._logger.verbose(f"Dropdown updated: {value}")
        self._spell_store.set_target_by_id(value)

    def _on_cycle_spell(self, idx_adjustment: int) -> None:
        self._logger.verbose(f"Cycle spell by: {idx_adjustment}")
        self._spell_store.cycle_target(idx_adjustment)
        self._dropdown.show_value(self._spell_store.current_index)

    def _on_quit(self) -> None:
        self._logger.info("MockZoneControls quit requested")
        self.quit.invoke()
