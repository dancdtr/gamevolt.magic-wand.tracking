from gamevolt.configuration.appsetting import appsetting
from gamevolt.visualisation.configuration.visualiser_settings import VisualiserSettings


@appsetting
class ZoneVisualiserSettings:
    visualiser: VisualiserSettings
