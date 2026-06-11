from gamevolt.configuration.appsetting import appsetting
from wand.interpreters.configuration.rmf_settings import RMFSettings


@appsetting
class WandSettings:
    rmf: RMFSettings
