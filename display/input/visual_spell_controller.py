import tkinter as tk
from collections.abc import Callable
from logging import Logger

from display.input.drop_down import DropDown
from display.input.key_input import KeyInput
from display.input.numeric_input import NumericInput
from gamevolt.events.event import Event
from gamevolt.messaging.udp.udp_tx import UdpTx
from gamevolt.visualisation.visualiser import Visualiser
from messaging.target_spell_updated_message import TargetSpellUpdatedMessage
from spells.control.spell_controller import SpellController
from spells.spell import Spell
from spells.spell_list import SpellList


class VisualSpellController(SpellController):
    def __init__(
        self,
        logger: Logger,
        spell_list: SpellList,
        visualiser: Visualiser,
        udp_tx: UdpTx,
        parent: tk.Misc | None = None,
    ) -> None:
        super().__init__(logger, spell_list)

        self._udp_tx = udp_tx
        root = visualiser.root
        dropdown_parent = parent or root

        self._dropdown = DropDown(dropdown_parent, {k: v for k, v in zip(spell_list.ids, spell_list.names)})
        self._key_input = KeyInput(root)
        self._numeric_input = NumericInput(root)

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

    @property
    def target_spell_updated(self) -> Event[Callable[[Spell], None]]:
        return super().target_spell_updated

    @property
    def toggle_history(self) -> Event[Callable[[], None]]:
        return super().toggle_history

    @property
    def quit(self) -> Event[Callable[[], None]]:
        return super().quit

    def _on_numeric_input_updated(self, spell_id: int) -> None:
        self._logger.debug(f"Numeric input updated: {spell_id}")
        self.set_target_by_id(spell_id)
        self._dropdown.show_value(self._current_index)

    def _on_dropdown_updated(self, value: int) -> None:
        self._logger.debug(f"Dropdown updated: {value}")
        spell = self._spell_list.get_by_id(value)
        self.set_target_by_type(spell.type)

    def _on_cycle_spell(self, idx_adjustment: int) -> None:
        self._logger.debug(f"Cycle spell by: {idx_adjustment}")
        self.cycle_target(idx_adjustment)

    def _on_toggle_history_visibility(self) -> None:
        self._logger.debug("Toggling history visibility")
        self.toggle_history.invoke()

    def _on_quit(self) -> None:
        self._logger.info("VisualiserSpellSelector quit requested")
        self.quit.invoke()

    def _set_target(self, spell: Spell) -> None:
        super()._set_target(spell)

        message = TargetSpellUpdatedMessage(spell.name.upper())
        self._udp_tx.send(message.to_dict())
