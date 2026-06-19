from gamevolt.configuration.appsetting import appsetting
from visualisation.configuration.trail_settings import TrailSettings
from visualisation.configuration.wand_visualiser_settings import WindowSettings


@appsetting
class MultiWandVisualiserSettings:
    """RTLS visualiser: every active wand's live trail on one shared canvas, colour-keyed by id.

    `palette` is assigned to `tracked_wand_ids` in order (wraps if more wands than colours).
    `trail` is the shared comet look; per-wand `line_colour`/`head_colour` come from the palette,
    so the configured trail colours act only as a fallback for unpalettable wands.
    """

    is_enabled: bool
    palette: list[str]
    window: WindowSettings
    trail: TrailSettings
