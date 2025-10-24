from __future__ import annotations

import time
import tkinter as tk

from gamevolt_debugging import TickMonitor
from gamevolt_logging import get_logger
from gamevolt_logging.configuration import LoggingSettings

from analysis.spell_trace_adapter_factory import SpellTraceAdapterFactory
from analysis.spell_trace_session import SpellTraceSessionManager
from analysis.spell_trace_session_settings import SpellTraceSessionSettings
from difficulty.spell_difficulty_controller import SpellDifficultyController
from input.mouse_tk_input import MouseTkInput
from input.wand_position import WandPosition
from motion.direction_type import DirectionType
from motion.gesture_history import GestureHistory
from motion.gesture_segment import GestureSegment
from motion.motion_processor import DirectionType, MotionProcessor
from motion.motion_type import MotionType
from preview import TkPreview, TkPreviewSettings
from spell_library import *
from spells.easy_spell_matcher import EasySpellMatcher
from spells.library.spell_definition_factory import SpellDefinitionFactory
from spells.library.spell_difficulty_type import SpellDifficultyType
from spells.spell_match import SpellMatch
from spells.spell_matcher import SpellMatcher
from spells.spell_matcher_manager import SpellMatcherManager
from spells.spell_type import SpellType
from wand_trail import WandTrail
from wizard_names_provider import WizardNameProvider

_SAMPLE_FREQUENCY_HZ = 30
_SPELL_TYPES = [SpellType.LOCOMOTOR]
# _SPELL_TYPES = [SpellType.REVELIO]
# _SPELL_TYPES = [SpellType.SQUARIO, SpellType.OBLONGIUM, SpellType.RECTANGLIA, SpellType.REVELIO, SpellType.RICTUMSEMPRA]

logger = get_logger(LoggingSettings(minimum_level="DEBUG"))

tick_monitor = TickMonitor(30)

history = GestureHistory(max_segments=20, max_age_s=5.0)

spell_definition_factory = SpellDefinitionFactory()

difficulty_controller = SpellDifficultyController(logger)

trace_manager = SpellTraceSessionManager(
    logger=logger,
    trace_factory=SpellTraceAdapterFactory(),
    settings=SpellTraceSessionSettings(
        natural_break_s=0.9,
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

preview = TkPreview(
    TkPreviewSettings(
        title="Mock Wand Input",
        width=800,
        height=800,
        buffer=100,
    )
)

input = MouseTkInput(logger=logger, preview=preview)

trail = WandTrail(
    preview=preview,
    max_points=90,
    line_width=4,
    line_color="#00ffcc",
    smooth=False,
    draw_points=True,
    point_radius=4,
    point_colour="#FFFFFF",
)

processor = MotionProcessor(input=input)

name_provider = WizardNameProvider()


def on_sample(s: WandPosition) -> None:
    preview.set_status(f"({s.x:.3f}, {s.y:.3f}) | {tick_monitor.tick_rate}hz")
    trail.add(s)
    trail.draw()


def on_direction_changed(dir: DirectionType) -> None:
    return
    logger.debug(f"State: {dir.name}")


def on_motion_changed(mode: MotionType) -> None:
    trace_manager.on_motion_changed(mode)
    # return
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


def on_difficulty_toggled() -> None:
    difficulty_controller.toggle_difficulty()
    matcher_manager.set_difficulty(difficulty_controller.difficulty)
    trace_manager.on_difficulty_changed()


def main():
    input.position_updated.subscribe(on_sample)
    processor.state_changed.subscribe(on_direction_changed)
    processor.motion_changed.subscribe(on_motion_changed)
    processor.segment_completed.subscribe(on_segment_completed)
    matcher_manager.matched.subscribe(on_spell)
    preview.register_key_callback("t", trace_manager.toggle)
    preview.register_key_callback("c", trail.clear)
    preview.register_key_callback("d", on_difficulty_toggled)

    input.start()
    processor.start()
    preview.start()

    interval_s = 1.0 / _SAMPLE_FREQUENCY_HZ
    next_t = time.perf_counter() + interval_s

    try:
        while True:
            preview.update()

            now = time.perf_counter()
            if now >= next_t:
                tick_monitor.tick()
                input.update()
                next_t += interval_s

                if now - next_t > 0.25:
                    next_t = now + interval_s

            time.sleep(0.001)
    except tk.TclError:
        pass


if __name__ == "__main__":
    main()
