from __future__ import annotations

from gamevolt.logging._logger import Logger
from services.spell_cast_reporter_base import SpellCastReporterBase
from spells.spell_match import SpellMatch


class LocalSpellCastReporter(SpellCastReporterBase):
    """Log-only stand-in. Real impl will POST to the hub; hub determines success + triggers show responses."""

    def __init__(self, logger: Logger) -> None:
        self._logger = logger

    async def report_spell_cast(self, match: SpellMatch) -> None:
        self._logger.info(
            f"LocalSpellCastReporter wand ({match.wand_id}) '{match.spell_name}' "
            f"score={match.accuracy_score:.3f} response={match.spell_reponse_type.name}"
        )
