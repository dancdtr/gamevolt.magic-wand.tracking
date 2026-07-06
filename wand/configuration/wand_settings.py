from dataclasses import field

from gamevolt.configuration.appsetting import appsetting
from motion.stroke.configuration.stroke_trim_settings import StrokeTrimSettings
from motion.stroke.configuration.stroke_windower_settings import StrokeWindowerSettings
from wand.configuration.cast_assembly_settings import CastAssemblySettings
from wand.configuration.confusion_guard_settings import ConfusionGuardSettings
from wand.interpreters.configuration.rmf_settings import RMFSettings


@appsetting
class WandSettings:
    rmf: RMFSettings
    lead_in_trim: StrokeTrimSettings
    tail_trim: StrokeTrimSettings
    confusion_guard: ConfusionGuardSettings
    stroke_window: StrokeWindowerSettings = field(default_factory=StrokeWindowerSettings)
    cast_assembly: CastAssemblySettings = field(default_factory=CastAssemblySettings)
