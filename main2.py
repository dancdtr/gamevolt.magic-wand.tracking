from __future__ import annotations

import asyncio
import os
import tkinter as tk

from gamevolt_logging import get_logger
from gamevolt_logging.configuration import LoggingSettings

from analysis.spell_trace_adapter_factory import SpellTraceAdapterFactory
from analysis.spell_trace_session import SpellTraceSessionManager
from appsettings import AppSettings
from input.factories.configuration.input_type import InputType
from input.mouse_input import MouseInput
from input.wand.wand_input import WandInput
from input.wand_position import WandPosition
from messaging.spell_cast_udp_tx import SpellCastUdpTx
from motion.direction.direction_type import DirectionType
from motion.gesture.gesture_history import GestureHistory
from motion.gesture.gesture_segment import GestureSegment
from motion.motion_phase_type import MotionPhaseType
from motion.motion_processor import MotionProcessor
from spells.accuracy.spell_accuracy_scorer import SpellAccuracyScorer
from spells.control.udp_spell_controller import UdpSpellController
from spells.spell_list import SpellList
from spells.spell_match import SpellMatch
from spells.spell_matcher import SpellMatcher
from visualisation.wand_visualiser import WandVisualiser
from visualisation.wand_visualiser_factory import WandVisualiserFactory
from wizards.wizard_names_provider import WizardNameProvider

application_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(application_dir, "appsettings.yml")
config_env_path = os.path.join(application_dir, "appsettings.env.yml")
settings = AppSettings.load(config_file_path=config_path, config_env_file_path=config_env_path)
print(settings)

logger = get_logger(LoggingSettings(file_path=settings.logging.file_path, minimum_level=settings.logging.minimum_level))

history = GestureHistory(settings.motion.gesture_history)

trace_manager = SpellTraceSessionManager(
    logger=logger,
    trace_factory=SpellTraceAdapterFactory(),
    start_active=False,
    settings=settings.spell_trace_session,
)

spell_list = SpellList(logger)

udp_tx = SpellCastUdpTx(logger, settings.udp_peer.udp_transmitter)
spell_controller = UdpSpellController(logger, settings.udp_peer, spell_list)

matcher = SpellMatcher(logger=logger, accuracy_scorer=SpellAccuracyScorer(settings=settings.accuracy), spell_controller=spell_controller)

visualiser = WandVisualiserFactory(logger, settings.wand_visualiser).create()

if settings.input.input_type is InputType.MOUSE:
    if not isinstance(visualiser, WandVisualiser):
        raise RuntimeError(
            f"Cannot use the mock mouse input system without a visualiser - ensure wand_visualiser is enabled in appsettings.env.yml."
        )
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
        # print([seg.direction_type.name for seg in history.tail()])
        history.clear()
    logger.debug(f"Motion: {mode.name}")


def on_segment_completed(segment: GestureSegment):
    logger.debug(f"Completed '{segment.direction_type.name}' ({segment.direction:.3f}): {segment.duration_s}s")
    history.add(segment)
    trace_manager.on_segment(
        segment,
        history.tail(),
        matcher,
    )


def on_spell(match: SpellMatch):
    logger.info(
        f"{name_provider.get_name()} cast {match.spell_name}! ✨✨"
        # f"({match.duration_s:.3f}s), {match.segments_used}/{match.total_segments}="
        f"{match.accuracy_score * 100:.1f}%"
    )

    udp_tx.on_spell_detected(match)
    trace_manager.on_match(match)
    # print([seg.direction_type.name for seg in history.tail()])
    history.clear()
    processor.reset()


quit_event = asyncio.Event()

spell_controller.start()
processor.direction_changed.subscribe(on_direction_changed)
processor.motion_changed.subscribe(on_motion_changed)
processor.segment_completed.subscribe(on_segment_completed)
matcher.matched.subscribe(on_spell)
input.position_updated.subscribe(on_position_updated)
visualiser.quit.subscribe(lambda: quit_event.set())


async def main():
    logger.info(f"Running '{settings.name}' version: '{settings.version}'...")
    try:
        await input.start()
        processor.start()
        visualiser.start()
    except Exception as ex:
        raise ex

    try:
        while not quit_event.is_set():
            input.update()
            visualiser.update()
            await asyncio.sleep(0.01)
    except tk.TclError:
        pass
    except Exception as ex:
        raise ex


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Exiting on user interrupt...")
    finally:
        logger.info(f"Exited '{settings.name}'.")
