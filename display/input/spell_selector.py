# spells/control/visual_spell_controller.py
from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from logging import Logger

from display.input.drop_down import DropDown
from display.input.numeric_input import NumericInput
from display.input.spell_visualiser_key_input import SpellVisualiserKeyInput
from gamevolt.events.event import Event
from gamevolt.messaging.udp.udp_tx import UdpTx
from gamevolt.visualisation.visualiser import Visualiser
from messaging.target_spell_updated_message import TargetSpellUpdatedMessage
from spells.control.spell_target_store import SpellTargetStore
from spells.spell import Spell
from spells.spell_list import SpellList


class SpellSelector:
    def __init__(
        self,
        logger: Logger,
        spell_list: SpellList,
        visualiser: Visualiser,
        udp_tx: UdpTx,
        parent: tk.Misc | None = None,
    ) -> None:
        self._logger = logger
        self._spell_list = spell_list
        self._store = SpellTargetStore(logger, spell_list)

        self._udp_tx = udp_tx

        root = visualiser.root
        dropdown_parent = parent or root

        self._dropdown = DropDown(dropdown_parent, {k: v for k, v in zip(spell_list.ids, spell_list.names)})
        self._key_input = SpellVisualiserKeyInput(root)
        self._numeric_input = NumericInput(root)

        self._toggle_history: Event[Callable[[], None]] = Event()
        self._quit: Event[Callable[[], None]] = Event()

    @property
    def target_spell(self) -> Spell:
        return self._store.target_spell

    @property
    def target_spell_updated(self) -> Event[Callable[[Spell], None]]:
        return self._store.target_spell_updated

    @property
    def toggle_history(self) -> Event[Callable[[], None]]:
        return self._toggle_history

    @property
    def quit(self) -> Event[Callable[[], None]]:
        return self._quit

    def start(self) -> None:
        self._key_input.quit.subscribe(self._on_quit)
        self._key_input.cycle_spell.subscribe(self._on_cycle_spell)
        self._key_input.toggle_history.subscribe(self._on_toggle_history_visibility)

        self._dropdown.updated.subscribe(self._on_dropdown_updated)
        self._numeric_input.updated.subscribe(self._on_numeric_input_updated)

        self._store.target_spell_updated.subscribe(self._send_target_over_udp)

        self._send_target_over_udp(self._store.target_spell)

    def stop(self) -> None:
        self._store.target_spell_updated.unsubscribe(self._send_target_over_udp)

        self._key_input.toggle_history.unsubscribe(self._on_toggle_history_visibility)
        self._key_input.cycle_spell.unsubscribe(self._on_cycle_spell)
        self._key_input.quit.unsubscribe(self._on_quit)

        self._numeric_input.updated.unsubscribe(self._on_numeric_input_updated)
        self._dropdown.updated.unsubscribe(self._on_dropdown_updated)

    def _on_numeric_input_updated(self, spell_id: int) -> None:
        self._logger.debug(f"Numeric input updated: {spell_id}")
        self._store.set_target_by_id(spell_id)
        self._dropdown.show_value(self._store.current_index)

    def _on_dropdown_updated(self, value: int) -> None:
        self._logger.debug(f"Dropdown updated: {value}")
        self._store.set_target_by_id(value)

    def _on_cycle_spell(self, idx_adjustment: int) -> None:
        self._logger.debug(f"Cycle spell by: {idx_adjustment}")
        self._store.cycle_target(idx_adjustment)
        self._dropdown.show_value(self._store.current_index)

    def _on_toggle_history_visibility(self) -> None:
        self._logger.debug("Toggling history visibility")
        self._toggle_history.invoke()

    def _on_quit(self) -> None:
        self._logger.info("VisualiserSpellSelector quit requested")
        self._quit.invoke()

    def _send_target_over_udp(self, spell: Spell) -> None:
        message = TargetSpellUpdatedMessage(spell.name.upper())
        self._udp_tx.send(message.to_dict())
