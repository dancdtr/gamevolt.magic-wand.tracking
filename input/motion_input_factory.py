from abc import ABC

from input.motion_input_base import MotionInputBase


class MotionInputFactory(ABC):
    def create(self) -> MotionInputBase: ...
