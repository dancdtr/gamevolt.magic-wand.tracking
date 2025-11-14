from __future__ import annotations

import asyncio
import tkinter as tk

from gamevolt_logging import get_logger
from gamevolt_logging.configuration import LoggingSettings

from analysis.spell_trace_adapter_factory import SpellTraceAdapterFactory
from analysis.spell_trace_session import SpellTraceSessionManager
from appsettings import AppSettings
from difficulty.spell_difficulty_controller import SpellDifficultyController
from gamevolt.serial.serial_receiver import SerialReceiver
from input.factories.configuration.input_type import InputType
from input.mouse_input import MouseInput
from input.wand.interpreters.wand_yawpitch_rmf_interpreter import YawPitchRMFInterpreter
from input.wand.wand_data_reader import WandDataReader
from input.wand.wand_input import WandInput
from live_wand_preview import LiveWandPreview
from motion.direction_type import DirectionType
from motion.gesture_history import GestureHistory
from motion.gesture_segment import GestureSegment
from motion.motion_processor import DirectionType, MotionProcessor
from motion.motion_type import MotionType
from preview import TkPreview
from spell_library import *
from spells.easy_spell_matcher import EasySpellMatcher
from spells.library.spell_definition_factory import SpellDefinitionFactory
from spells.library.spell_difficulty_type import SpellDifficultyType
from spells.spell_match import SpellMatch
from spells.spell_matcher import SpellMatcher
from spells.spell_matcher_manager import SpellMatcherManager
from wizard_names_provider import WizardNameProvider

# _INPUT_TYPE = InputType.WAND
# _SPELL_TYPES = [SpellType.LOCOMOTOR, SpellType.REVELIO]
# _SPELL_TYPES = [SpellType.LUMOS_MAXIMA, SpellType.VENTUS]
# _SPELL_TYPES = [SpellType.LOCOMOTOR]
# _SPELL_TYPES = [SpellType.REVELIO]
# _SPELL_TYPES = [SpellType.SQUARIO, SpellType.OBLONGIUM, SpellType.RECTANGLIA, SpellType.REVELIO, SpellType.RICTUMSEMPRA]

settings = AppSettings.load(config_path="./appsettings.yml", config_env_path=None)
print(settings)

logger = get_logger(LoggingSettings(file_path=settings.logging.file_path, minimum_level=settings.logging.minimum_level))

history = GestureHistory(max_segments=20, max_age_s=5.0)
spell_definition_factory = SpellDefinitionFactory()
difficulty_controller = SpellDifficultyController(logger, start_difficulty=SpellDifficultyType.FORGIVING)

trace_manager = SpellTraceSessionManager(
    logger=logger,
    trace_factory=SpellTraceAdapterFactory(),
    start_active=False,
    settings=settings.spell_trace_session,
)


matcher_manager = SpellMatcherManager(difficulty_controller.difficulty)
matcher_manager.register(
    SpellDifficultyType.FORGIVING,
    EasySpellMatcher(spell_definition_factory.create_spells(settings.spells.targets, SpellDifficultyType.FORGIVING)),
)
matcher_manager.register(
    SpellDifficultyType.STRICT, SpellMatcher(spell_definition_factory.create_spells(settings.spells.targets, SpellDifficultyType.STRICT))
)

tk_preview = TkPreview(settings.tk_preview)

if settings.input.input_type is InputType.MOUSE:
    input = MouseInput(logger, settings.input.mouse, tk_preview)
elif settings.input.input_type is InputType.WAND:
    input = WandInput(logger, settings.input.wand)
else:
    raise RuntimeError(f"No input defined for type '{settings.input.input_type}'.")


processor = MotionProcessor(input=input)
name_provider = WizardNameProvider()

preview = LiveWandPreview(
    input_source=input,
    preview=tk_preview,
    settings=settings.live_wand_preview,
)


def on_direction_changed(dir: DirectionType) -> None:
    return
    logger.info(f"State: {dir.name}")


def on_motion_changed(mode: MotionType) -> None:
    trace_manager.on_motion_changed(mode)
    if mode is MotionType.STATIONARY:
        preview.clear()
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


processor.state_changed.subscribe(on_direction_changed)
processor.motion_changed.subscribe(on_motion_changed)
processor.segment_completed.subscribe(on_segment_completed)
matcher_manager.matched.subscribe(on_spell)


async def main():
    try:
        await input.start()
        processor.start()
        tk_preview.start()
        preview.start()
    except Exception as ex:
        raise ex

    try:
        while True:
            input.update()
            tk_preview.update()
            preview.update()
            await asyncio.sleep(0.01)
    except tk.TclError:
        pass
    except Exception as ex:
        raise ex


if __name__ == "__main__":
    asyncio.run(main())
