from __future__ import annotations

import asyncio
import tkinter as tk

from gamevolt_logging import get_logger
from gamevolt_logging.configuration import LoggingSettings

from analysis.spell_trace_adapter_factory import SpellTraceAdapterFactory
from analysis.spell_trace_session import SpellTraceSessionManager
from appsettings import AppSettings
from difficulty.spell_difficulty_controller import SpellDifficultyController
from input.factories.configuration.input_type import InputType
from input.mouse_input import MouseInput
from input.wand.wand_input import WandInput
from input.wand_position import WandPosition
from messaging.unity_udp_tx import UnityUdpTx
from motion.direction.direction_type import DirectionType
from motion.gesture.gesture_history import GestureHistory
from motion.gesture.gesture_segment import GestureSegment
from motion.motion_phase_type import MotionPhaseType
from motion.motion_processor import MotionProcessor
from spells.accuracy.spell_accuracy_scorer import SpellAccuracyScorer
from spells.easy_spell_matcher import EasySpellMatcher
from spells.library.spell_definition_factory import SpellDefinitionFactory
from spells.library.spell_difficulty_type import SpellDifficultyType
from spells.spell_match import SpellMatch
from spells.spell_matcher import SpellMatcher
from spells.spell_matcher_manager import SpellMatcherManager
from visualisation.wand_visualiser import WandVisualiser
from wizards.wizard_names_provider import WizardNameProvider

_WAND_ID = "DefaultWand"

settings = AppSettings.load(config_path="./appsettings.yml", config_env_path=None)
print(settings)

logger = get_logger(LoggingSettings(file_path=settings.logging.file_path, minimum_level=settings.logging.minimum_level))

history = GestureHistory(settings.motion.gesture_history)
spell_definition_factory = SpellDefinitionFactory()
difficulty_controller = SpellDifficultyController(logger, start_difficulty=SpellDifficultyType.STRICT)

trace_manager = SpellTraceSessionManager(
    logger=logger,
    trace_factory=SpellTraceAdapterFactory(),
    start_active=False,
    settings=settings.spell_trace_session,
)

unity_udp_tx = UnityUdpTx(logger, settings.unity_udp)

matcher_manager = SpellMatcherManager(difficulty_controller.difficulty)
matcher_manager.register(
    SpellDifficultyType.FORGIVING,
    EasySpellMatcher(logger, spell_definition_factory.create_spells(settings.spells.targets, SpellDifficultyType.FORGIVING)),
)
matcher_manager.register(
    SpellDifficultyType.STRICT,
    SpellMatcher(
        logger=logger,
        accuracy_scorer=SpellAccuracyScorer(settings=settings.accuracy),
        spells=spell_definition_factory.create_spells(settings.spells.targets, SpellDifficultyType.STRICT),
    ),
)

visualiser = WandVisualiser(settings=settings.wand_visualiser)

if settings.input.input_type is InputType.MOUSE:
    input = MouseInput(logger, settings.input.mouse, visualiser)
elif settings.input.input_type is InputType.WAND:
    input = WandInput(logger, settings.input.wand)
else:
    raise RuntimeError(f"No input defined for type '{settings.input.input_type}'.")


processor = MotionProcessor(settings=settings.motion.processor, input=input)
name_provider = WizardNameProvider(settings.wizard)


def on_position_updated(pos: WandPosition) -> None:
    visualiser.add_position(pos)


def on_direction_changed(dir: DirectionType) -> None:
    # logger.info(f"State: {dir.name}")
    return


def on_motion_changed(mode: MotionPhaseType) -> None:
    trace_manager.on_motion_changed(mode)
    if mode is MotionPhaseType.STATIONARY:
        visualiser.clear()
        input.reset()
        processor.reset()
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
        f"{name_provider.get_name()} cast {match.spell_name}! ✨✨"
        # f"({match.duration_s:.3f}s), {match.segments_used}/{match.total_segments}="
        f"{match.accuracy * 100:.1f}%."
    )

    unity_udp_tx.on_spell_detected(match)
    trace_manager.on_match(match)
    history.clear()
    processor.reset()


# def on_difficulty_toggled() -> None:
#     # difficulty_controller.toggle_difficulty()
#     # matcher_manager.set_difficulty(difficulty_controller.difficulty)
#     trace_manager.on_difficulty_changed()


processor.direction_changed.subscribe(on_direction_changed)
processor.motion_changed.subscribe(on_motion_changed)
processor.segment_completed.subscribe(on_segment_completed)
matcher_manager.matched.subscribe(on_spell)
input.position_updated.subscribe(on_position_updated)


async def main():
    try:
        await input.start()
        processor.start()
        visualiser.start()
    except Exception as ex:
        raise ex

    try:
        while True:
            input.update()
            visualiser.update()
            await asyncio.sleep(0.01)
    except tk.TclError:
        pass
    except Exception as ex:
        raise ex


if __name__ == "__main__":
    asyncio.run(main())
