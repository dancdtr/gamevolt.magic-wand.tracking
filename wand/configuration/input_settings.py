from gamevolt.configuration.appsetting import appsetting
from wand.configuration.wand_settings import WandSettings


@appsetting
class InputSettings:
    wand: WandSettings
