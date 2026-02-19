from __future__ import annotations

from logging import Logger

from spells.matching.rules.group_distance_duration_rule import GroupDistanceRatioRule
from spells.matching.rules.group_duration_ratio_rule import GroupDurationRatioRule
from spells.matching.rules.max_distance_rule import MaxDistanceRule
from spells.matching.rules.max_duration_rule import MaxDurationRule
from spells.matching.rules.max_filler_rule import MaxFillerRule
from spells.matching.rules.min_distance_rule import MinDistanceRule
from spells.matching.rules.min_duration_rule import MinDurationRule
from spells.matching.rules.min_group_steps_rule import MinGroupStepsRule
from spells.matching.rules.min_steps_rule import MinStepsRule
from spells.matching.rules.pause_at_end_rule import PauseAtEndRule
from spells.matching.rules.pause_before_start_rule import PauseBeforeStartRule
from spells.matching.rules.required_steps_rule import RequiredStepsRule
from spells.matching.rules.spell_rule import SpellRule
from spells.spell_definition import SpellDefinition


class RulesFactory:
    def __init__(self, logger: Logger) -> None:
        self._logger = logger

    def create(self, definition: SpellDefinition) -> tuple[SpellRule, ...]:
        rules: list[SpellRule] = []

        if definition.min_spell_steps:
            rules.append(MinStepsRule(self._logger))

        if definition.check_required_steps:
            rules.append(RequiredStepsRule(self._logger))

        if definition.min_total_duration_s:
            rules.append(MinDurationRule(self._logger))

        if definition.max_total_duration_s:
            rules.append(MaxDurationRule(self._logger))

        if definition.min_total_distance:
            rules.append(MinDistanceRule(self._logger))

        if definition.max_total_distance:
            rules.append(MaxDistanceRule(self._logger))

        if definition.check_group_distance_ratio:
            rules.append(GroupDistanceRatioRule(self._logger))

        if definition.check_group_duration_ratio:
            rules.append(GroupDurationRatioRule(self._logger))

        # Group step minimums
        rules.append(MinGroupStepsRule(self._logger))

        # Pause rules
        if definition.min_pre_pause_s and definition.min_pre_pause_s > 0:
            rules.append(PauseBeforeStartRule(self._logger))

        if definition.min_post_pause_s and definition.min_post_pause_s > 0:
            rules.append(PauseAtEndRule(self._logger))

        # Filler
        rules.append(MaxFillerRule(self._logger))

        return tuple(rules)
