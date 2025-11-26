from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase


@dataclass
class SpellAccuracyWeightsSettings(SettingsBase):
    # more score for optional steps (0) -> more score for required steps (1)
    required_step_bias: float = 0.5

    # how much weight towards the accuracy score
    step_count_weight: float = 0.7
    relative_group_distance_weight: float = 0.15
    relative_group_duration_weight: float = 0.15
