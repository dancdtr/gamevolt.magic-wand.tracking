from gamevolt.configuration.appsetting import appsetting
from motion.stroke.configuration.stroke_trim_settings import StrokeTrimSettings
from wand.interpreters.configuration.rmf_settings import RMFSettings


@appsetting
class WandSettings:
    rmf: RMFSettings
    lead_in_trim: StrokeTrimSettings
    tail_trim: StrokeTrimSettings
