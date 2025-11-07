# wand_input.py
from __future__ import annotations

from logging import Logger
from typing import Callable

from gamevolt.events.event import Event
from input.motion_input_base import MotionInputBase
from input.wand_position import WandPosition
from wand_data_reader import WandDataMessage, WandDataReader
from wand_yawpitch_rmf_interpreter import YawPitchRMFInterpreter

_INVERT_X = False
_INVERT_Y = False


class WandInput(MotionInputBase):
    def __init__(self, logger: Logger, wand_data_reader: WandDataReader, yaw_pitch_interpreter: YawPitchRMFInterpreter) -> None:
        super().__init__(logger)

        self._yaw_pitch_interpreter = yaw_pitch_interpreter
        self._wand_data_reader = wand_data_reader

        self.position_updated: Event[Callable[[WandPosition], None]] = Event()

    def start(self) -> None:
        self._wand_data_reader.wand_position_updated.subscribe(self._on_wand_data_message)
        self._wand_data_reader.start()

    def stop(self) -> None:
        self._wand_data_reader.wand_position_updated.unsubscribe(self._on_wand_data_message)

    def update(self) -> None:
        pass

    def reset(self) -> None:
        self._yaw_pitch_interpreter.reset()

    def _on_wand_data_message(self, m: WandDataMessage) -> None:
        wand_pos = self._yaw_pitch_interpreter.on_sample(m.ms, m.yaw, m.pitch)
        adjusted_wand_position = WandPosition(
            ts_ms=wand_pos.ts_ms,
            x_delta=wand_pos.x_delta * -1 if _INVERT_X else wand_pos.x_delta,
            y_delta=wand_pos.y_delta * -1 if _INVERT_Y else wand_pos.y_delta,
            x=wand_pos.x,
            y=wand_pos.y,
        )
        self.position_updated.invoke(adjusted_wand_position)
