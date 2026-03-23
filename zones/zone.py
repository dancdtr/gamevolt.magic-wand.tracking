from logging import Logger

from spells.spell_type import SpellType


class Zone:
    def __init__(self, logger: Logger, id: str, spell_type: SpellType) -> None:
        self._spell_type = spell_type
        self._logger = logger
        self._id = id

        self._wand_ids: set[str] = set()

    @property
    def id(self) -> str:
        return self._id

    @property
    def wand_ids(self) -> tuple[str, ...]:
        return tuple(self._wand_ids)

    @property
    def wand_count(self) -> int:
        return len(self._wand_ids)

    @property
    def spell_type(self) -> SpellType:
        return self._spell_type

    def contains_wand_id(self, wand_id: str) -> bool:
        return wand_id in self._wand_ids

    def on_wand_enter(self, wand_id: str) -> None:
        if wand_id in self._wand_ids:
            self._logger.warning(f"Wand ({wand_id}) was already present in zone '{self._id}!'")
            return

        self._wand_ids.add(wand_id)
        self._logger.info(f"Wand ({wand_id}) has entered zone ({self._id}).")

    def on_wand_exit(self, wand_id: str) -> None:
        if wand_id not in self._wand_ids:
            self._logger.warning(f"Wand ({wand_id}) was not present in zone ({self._id}) to exit!")
            return

        self._wand_ids.discard(wand_id)
        self._logger.info(f"Wand ({wand_id}) has exited zone ({self._id}).")

    def on_wand_disconnected(self, wand_id) -> None:
        self._wand_ids.discard(wand_id)
        self._logger.info(f"Wand ({wand_id}) discarded from zone ({self._id}).")
