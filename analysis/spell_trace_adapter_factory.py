from logging import Logger

from analysis.spell_trace_adapter import SpellTraceAdapter
from analysis.spell_tracer import SpellAttemptTrace


class SpellTraceAdapterFactory:
    # def __init__(self, logger: Logger) -> None:
    #     self._logger = logger

    def create(self) -> SpellTraceAdapter:
        return SpellTraceAdapter(SpellAttemptTrace(spell_id="", spell_name="", key_count=0))
