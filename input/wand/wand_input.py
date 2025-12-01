# wand_input.py
from __future__ import annotations

from logging import Logger
from typing import Callable

from gamevolt.events.event import Event
from input.factories.wand.configuration.wand_settings import WandSettings
from input.motion_input_base import MotionInputBase
from input.wand.interpreters.wand_yawpitch_rmf_interpreter import YawPitchRMFInterpreter
from input.wand.wand_data_reader import WandDataMessage, WandDataReader
from input.wand_position import WandPosition

# def _wrap180(deg: float) -> float:
#     return ((deg + 180.0) % 360.0) - 180.0


# def _clamp_unit(v: float) -> float:
#     return -1.0 if v < -1.0 else (1.0 if v > 1.0 else v)


class WandInput(MotionInputBase):
    def __init__(self, logger: Logger, settings: WandSettings) -> None:
        super().__init__(logger)
        self._settings = settings

        self._wand_data_reader = WandDataReader(logger, settings.wand_data_reader)
        self._yaw_pitch_interpreter = YawPitchRMFInterpreter(settings.rmf)

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
        wand_pos = self._yaw_pitch_interpreter.on_sample(message.id, message.ms, message.yaw, message.pitch)
        adjusted_wand_position = WandPosition(
            id=message.id,
            ts_ms=wand_pos.ts_ms,
            x_delta=wand_pos.x_delta,
            y_delta=wand_pos.y_delta,
            nx=wand_pos.nx,
            ny=wand_pos.ny,
        )
        self.position_updated.invoke(adjusted_wand_position)
