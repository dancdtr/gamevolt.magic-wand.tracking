from gamevolt.configuration.appsetting import appsetting
from gamevolt.visualisation.configuration.axes_settings import AxesSettings
from gamevolt.visualisation.configuration.label_settings import LabelSettings
from gamevolt.visualisation.configuration.visualiser_settings import VisualiserSettings
from visualisation.configuration.trail_settings import TrailSettings


@appsetting
class WandVisualiserSettings:
    is_enabled: bool
    visualiser: VisualiserSettings
    label: LabelSettings
    axes: AxesSettings
    trail: TrailSettings
