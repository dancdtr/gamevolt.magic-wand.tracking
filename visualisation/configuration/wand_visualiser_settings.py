from gamevolt.configuration.appsetting import appsetting
from visualisation.configuration.trail_settings import TrailSettings


@appsetting
class WindowSettings:
    title: str
    width: int
    height: int
    background_colour: str
    panel_colour: str
    text_colour: str


@appsetting
class SnapshotSettings:
    # Minimum raw $1 match accuracy for an attempt to replace the held snapshot.
    # Keeps noise flicks from clobbering the last real attempt.
    min_match_accuracy: float
    template_colour: str


@appsetting
class WandVisualiserSettings:
    is_enabled: bool
    wand_id: str  # the single wand this visualiser follows
    window: WindowSettings
    trail: TrailSettings
    snapshot: SnapshotSettings
