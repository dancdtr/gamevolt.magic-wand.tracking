from spells.matching.rules.distance_rule import DurationRule
from spells.matching.rules.duration_rule import DistanceRule
from spells.matching.rules.group_distance_duration_rule import GroupDistanceRatioRule
from spells.matching.rules.group_duration_ratio_rule import GroupDurationRatioRule
from spells.matching.rules.max_filler_rule import MaxFillerRule
from spells.matching.rules.min_steps_rule import MinStepsRule
from spells.matching.rules.pause_at_end_rule import PauseAtEndRule
from spells.matching.rules.pause_before_start_rule import PauseBeforeStartRule
from spells.matching.rules.required_steps_rule import RequiredStepsRule
from spells.matching.rules.spell_rule import SpellRule
from spells.matching.spell_match_context import SpellMatchContext
from spells.spell_definition import SpellDefinition


class RulesValidator:
    def __init__(self):
        pass

    def validate(self, ctx: SpellMatchContext) -> bool:
        spell = ctx.spell
        rules: list[SpellRule] = []

        # Structural completion rules
        rules.append(RequiredStepsRule())
        rules.append(MinStepsRule())

        # Duration / distance
        if spell.check_duration:
            rules.append(DurationRule())  # covers min+max total duration

        if spell.check_distance:
            rules.append(DistanceRule())

        if spell.check_group_distance_ratio:
            rules.append(GroupDistanceRatioRule())

        # Pause rules
        if spell.min_pre_pause_s and spell.min_pre_pause_s > 0:
            rules.append(PauseBeforeStartRule())

        if spell.min_post_pause_s and spell.min_post_pause_s > 0:
            rules.append(PauseAtEndRule())

        # Filler
        # Always allowed to exceed in the matcher;
        # this rule decides if that's acceptable.
        rules.append(MaxFillerRule())

        for rule in rules:
            if not rule.validate(ctx):
                return False

        return True
