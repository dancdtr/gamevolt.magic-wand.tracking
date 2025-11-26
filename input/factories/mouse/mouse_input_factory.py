from logging import Logger

from gamevolt.visualisation.visualiser import RootSettings
from input.factories.mouse.configuration.mouse_settings import MouseSettings
from input.motion_input_base import MotionInputBase
from input.motion_input_factory import MotionInputFactory
from input.mouse_input import MouseInput

_TK_PREVIEW_SETTINGS = RootSettings(
    title="Mouse Input",
    width=800,
    height=800,
    buffer=100,
)

_MOUSE_INPUT_SETTINGS = MouseSettings(invert_x=False, invert_y=False, sample_frequency=30)


class MouseInputFactory(MotionInputFactory):
    def __init__(
        self,
        logger: Logger,
    ) -> None:
        self._logger = logger

    def create(self) -> MotionInputBase:
        return MouseInput(self._logger, _MOUSE_INPUT_SETTINGS)
