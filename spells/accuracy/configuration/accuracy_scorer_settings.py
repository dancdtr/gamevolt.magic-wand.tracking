from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase
from spells.accuracy.spell_accuracy_weights_settings import SpellAccuracyWeightsSettings


@dataclass
class SpellAccuracyScorerSettings(SettingsBase):
    weights: SpellAccuracyWeightsSettings
    fudge: int
