# wand_input.py
from __future__ import annotations

from logging import Logger
from math import fmod
from typing import Callable

from gamevolt.events.event import Event
from input.motion_input_base import MotionInputBase
from input.wand_position import WandPosition
from wand_data_reader import WandDataMessage, WandDataReader
from wand_yawpitch_rmf_interpreter import YawPitchRMFInterpreter


def _wrap180(deg: float) -> float:
    return ((deg + 180.0) % 360.0) - 180.0


def _clamp_unit(v: float) -> float:
    return -1.0 if v < -1.0 else (1.0 if v > 1.0 else v)


class WandInput(MotionInputBase):
    def __init__(self, logger: Logger, wand_data_reader: WandDataReader, yaw_pitch_interpreter: YawPitchRMFInterpreter) -> None:
        super().__init__(logger)

        self._yaw_pitch_interpreter = yaw_pitch_interpreter
        self._wand_data_reader = wand_data_reader

        self.position_updated: Event[Callable[[WandPosition], None]] = Event()

    async def start(self) -> None:
        await self._wand_data_reader.start()
        self._wand_data_reader.wand_position_updated.subscribe(self._on_wand_data_message)

    async def stop(self) -> None:
        self._wand_data_reader.wand_position_updated.unsubscribe(self._on_wand_data_message)
        await self._wand_data_reader.stop()

    def update(self) -> None:
        pass

    def reset(self) -> None:
        self._yaw_pitch_interpreter.reset()

    def _on_wand_data_message(self, message: WandDataMessage) -> None:
        wand_pos = self._yaw_pitch_interpreter.on_sample(message.ms, message.yaw, message.pitch)

        adjusted_wand_position = WandPosition(
            ts_ms=wand_pos.ts_ms,
            x_delta=wand_pos.x_delta,
            y_delta=wand_pos.y_delta,
            nx=wand_pos.nx,
            ny=wand_pos.ny,
        )
        self.position_updated.invoke(adjusted_wand_position)
