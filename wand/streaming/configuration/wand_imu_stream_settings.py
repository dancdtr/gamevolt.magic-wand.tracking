from gamevolt.configuration.appsetting import appsetting
from wand.streaming.eliko.configuration.eliko_stream_settings import ElikoStreamSettings
from wand.streaming.eliko_single_anchor.configuration.eliko_single_anchor_stream_settings import (
    ElikoSingleAnchorStreamSettings,
)


@appsetting
class WandImuStreamSettings:
    eliko: ElikoStreamSettings | None
    eliko_single_anchor: ElikoSingleAnchorStreamSettings | None
