from __future__ import annotations

import asyncio
import time
import tkinter as tk

from gamevolt_logging import get_logger
from gamevolt_logging.configuration import LoggingSettings

from analysis.spell_trace_adapter_factory import SpellTraceAdapterFactory
from analysis.spell_trace_session import SpellTraceSessionManager
from analysis.spell_trace_session_settings import SpellTraceSessionSettings
from difficulty.spell_difficulty_controller import SpellDifficultyController
from gamevolt.serial.configuration.serial_receiver_settings import SerialReceiverSettings
from gamevolt.serial.serial_receiver import SerialReceiver
from input.mouse_tk_input import MouseTkInput
from input.wand_input import WandInput
from input.wand_position import WandPosition
from motion.direction_type import DirectionType
from motion.gesture_history import GestureHistory
from motion.gesture_segment import GestureSegment
from motion.motion_processor import DirectionType, MotionProcessor
from motion.motion_type import MotionType
from spell_library import *
from spells.easy_spell_matcher import EasySpellMatcher
from spells.library.spell_definition_factory import SpellDefinitionFactory
from spells.library.spell_difficulty_type import SpellDifficultyType
from spells.spell_match import SpellMatch
from spells.spell_matcher import SpellMatcher
from spells.spell_matcher_manager import SpellMatcherManager
from spells.spell_type import SpellType
from wand_data_reader import WandDataReader
from wand_yawpitch_rmf_interpreter import RMFSettings, YawPitchRMFInterpreter
from wizard_names_provider import WizardNameProvider

# _SPELL_TYPES = [SpellType.LOCOMOTOR, SpellType.REVELIO]
_SPELL_TYPES = [SpellType.LUMOS_MAXIMA, SpellType.VENTUS]
# _SPELL_TYPES = [SpellType.LOCOMOTOR]
# _SPELL_TYPES = [SpellType.REVELIO]
# _SPELL_TYPES = [SpellType.SQUARIO, SpellType.OBLONGIUM, SpellType.RECTANGLIA, SpellType.REVELIO, SpellType.RICTUMSEMPRA]

logger = get_logger(LoggingSettings(minimum_level="INFORMATION"))
history = GestureHistory(max_segments=20, max_age_s=5.0)
spell_definition_factory = SpellDefinitionFactory()
difficulty_controller = SpellDifficultyController(logger, start_difficulty=SpellDifficultyType.FORGIVING)

trace_manager = SpellTraceSessionManager(
    logger=logger,
    trace_factory=SpellTraceAdapterFactory(),
    start_active=False,
    settings=SpellTraceSessionSettings(
        natural_break_s=1,
        clear_history_on_flush=True,
        label_prefix="ATTEMPT",
    ),
)


matcher_manager = SpellMatcherManager(difficulty_controller.difficulty)
matcher_manager.register(
    SpellDifficultyType.FORGIVING, EasySpellMatcher(spell_definition_factory.create_spells(_SPELL_TYPES, SpellDifficultyType.FORGIVING))
)
matcher_manager.register(
    SpellDifficultyType.STRICT, SpellMatcher(spell_definition_factory.create_spells(_SPELL_TYPES, SpellDifficultyType.STRICT))
)

# input = MouseTkInput(logger=logger, sample_frequency=30)

serial_reader = SerialReceiver(
    logger=logger,
    settings=SerialReceiverSettings(
        port="/dev/tty.usbmodem1101",
        baud=115200,
        timeout=3,
        retry_interval=2,
    ),
)

reader = WandDataReader(logger, serial_reader, imu_hz=120.0, target_hz=30.0)
interpreter = YawPitchRMFInterpreter(RMFSettings(invert_x=True, invert_y=True, gain_x=1.0, gain_y=1.0))
input = WandInput(logger, reader, interpreter)

processor = MotionProcessor(input=input)
name_provider = WizardNameProvider()


def on_direction_changed(dir: DirectionType) -> None:
    return
    logger.debug(f"State: {dir.name}")


def on_motion_changed(mode: MotionType) -> None:
    trace_manager.on_motion_changed(mode)
    # return
    if mode is MotionType.STATIONARY:
        print("resetting input")
        input.reset()
    logger.debug(f"Motion: {mode.name}")


def on_segment_completed(segment: GestureSegment):
    logger.debug(f"Completed '{segment.direction_type.name}' ({segment.direction:.3f}): {segment.duration_s}s")
    history.add(segment)
    trace_manager.on_segment(
        segment,
        history.tail(),
        matcher_manager,
    )


def on_spell(match: SpellMatch):
    logger.info(
        f"{name_provider.get_name()} cast {match.spell_name}! ✨✨ "
        # f"({match.duration_s:.3f}s), {match.segments_used}/{match.total_segments}="
        # f"{match.accuracy * 100:.1f}%."
    )
    trace_manager.on_match(match)
    history.clear()


# def on_difficulty_toggled() -> None:
#     # difficulty_controller.toggle_difficulty()
#     # matcher_manager.set_difficulty(difficulty_controller.difficulty)
#     trace_manager.on_difficulty_changed()


# input.position_updated.subscribe(on_sample)
processor.state_changed.subscribe(on_direction_changed)
processor.motion_changed.subscribe(on_motion_changed)
processor.segment_completed.subscribe(on_segment_completed)
matcher_manager.matched.subscribe(on_spell)


async def main():
    await serial_reader.start()
    input.start()
    processor.start()

    try:
        while True:
            input.update()
            await asyncio.sleep(0.01)
    except tk.TclError:
        pass


if __name__ == "__main__":
    asyncio.run(main())
