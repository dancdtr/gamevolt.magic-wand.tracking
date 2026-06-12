from gamevolt.configuration.appsetting import appsetting
from motion.stroke.configuration.lead_in_trim_settings import LeadInTrimSettings
from wand.interpreters.configuration.rmf_settings import RMFSettings


@appsetting
class WandSettings:
    rmf: RMFSettings
    lead_in_trim: LeadInTrimSettings
