from logging import Logger

from input.factories.mouse.configuration.mouse_input_settings import MouseInputSettings
from input.motion_input_base import MotionInputBase
from input.motion_input_factory import MotionInputFactory
from input.mouse_tk_input import MouseTkInput
from preview import TkPreviewSettings

_TK_PREVIEW_SETTINGS = TkPreviewSettings(
    title="Mouse Input",
    width=800,
    height=800,
    buffer=100,
)

_MOUSE_INPUT_SETTINGS = MouseInputSettings(invert_x=False, invert_y=False, sample_frequency=30)


class MouseInputFactory(MotionInputFactory):
    def __init__(
        self,
        logger: Logger,
    ) -> None:
        self._logger = logger

    def create(self) -> MotionInputBase:
        return MouseTkInput(self._logger, _MOUSE_INPUT_SETTINGS)
