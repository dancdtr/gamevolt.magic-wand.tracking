from logging import Logger

from gamevolt.messaging.udp.udp_tx import UdpTx
from messaging.show_system_spell_cast_message import ShowSystemSpellCastMessage
from spells.spell_cast_quality import SpellCastQuality
from spells.spell_type import SpellType
from wizards.hogwarts_house import HogwartsHouse


class ShowControlDestination:
    """A live show-control endpoint plus the spells routed to it."""

    def __init__(self, name: str, tx: UdpTx, spells: set[SpellType]) -> None:
        self.name = name
        self.tx = tx
        self.spells = spells


class ShowSystemController:
    """Routes recognised casts to the show-control destinations that subscribe to the spell.

    A spell may fan out to several destinations. Spells claimed by no destination warn and drop."""

    def __init__(self, logger: Logger, destinations: list[ShowControlDestination]) -> None:
        self._logger = logger
        self._destinations = destinations

        self._routes: dict[SpellType, list[ShowControlDestination]] = {}
        for destination in destinations:
            for spell in destination.spells:
                self._routes.setdefault(spell, []).append(destination)

    def play_spell(self, wand_id: str, spell_type: SpellType, quality: SpellCastQuality, house: HogwartsHouse) -> None:
        targets = self._routes.get(spell_type)
        if not targets:
            self._logger.warning(f"No show-control destination for spell '{spell_type.name}'; cast not routed.")
            return

        message = ShowSystemSpellCastMessage(
            wand_id=self._format_wand_id(wand_id),
            spell_type=spell_type,
            quality=quality,
            house=house,
        )
        payload = message.to_dict()

        for destination in targets:
            self._logger.info(
                f"Notifying '{destination.name}' to play '{spell_type.name}' for quality '{quality.name}', house: '{house.name}'..."
            )
            destination.tx.send(payload)

    @staticmethod
    def _format_wand_id(wand_id: str) -> str:
        """Wand ids are bare upper hex internally; the show system / RTLS wire
        form keeps the `0x` prefix so downstream consumers handle it directly."""
        return wand_id if wand_id.lower().startswith("0x") else f"0x00{wand_id}"
