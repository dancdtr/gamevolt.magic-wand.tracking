from __future__ import annotations

from logging import Logger

from spells.matching.rules.distance_rule import DistanceRule
from spells.matching.rules.duration_rule import DurationRule
from spells.matching.rules.group_distance_duration_rule import GroupDistanceRatioRule
from spells.matching.rules.group_duration_ratio_rule import GroupDurationRatioRule
from spells.matching.rules.max_filler_rule import MaxFillerRule
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

        # Structural completion rules
        rules.append(RequiredStepsRule())
        rules.append(MinStepsRule())

        # Duration / distance
        if definition.check_duration:
            rules.append(DurationRule())

        if definition.check_distance:
            rules.append(DistanceRule())

        if definition.check_group_distance_ratio:
            rules.append(GroupDistanceRatioRule())

        if definition.check_group_duration_ratio:
            rules.append(GroupDurationRatioRule())

        # Group step minimums
        rules.append(MinGroupStepsRule())

        # Pause rules
        if definition.check_pre_start_pause and definition.min_pre_pause_s > 0:
            rules.append(PauseBeforeStartRule())

        if definition.check_post_end_pause and definition.min_post_pause_s > 0:
            rules.append(PauseAtEndRule())

        # Filler
        rules.append(MaxFillerRule())

        return tuple(rules)
