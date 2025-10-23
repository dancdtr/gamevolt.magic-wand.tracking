from __future__ import annotations

import time
import tkinter as tk

from gamevolt_debugging import TickMonitor
from gamevolt_logging import get_logger
from gamevolt_logging.configuration import LoggingSettings

from analysis.spell_trace_adapter import SpellTraceAdapter
from analysis.spell_trace_session import SpellTraceSessionConfig, SpellTraceSessionManager
from analysis.spell_tracer import SpellAttemptTrace
from difficulty.spell_difficulty_controller import SpellDifficultyController
from input.mouse_tk_input import MouseTkInput
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
from wand_trail import WandTrail
from wizard_names_provider import WizardNameProvider

_SAMPLE_FREQUENCY_HZ = 30

logger = get_logger(LoggingSettings(minimum_level="INFORMATION"))
tick_monitor = TickMonitor(30)

history = GestureHistory(max_segments=20, max_age_s=5.0)

spell_definition_factory = SpellDefinitionFactory()
difficulty_controller = SpellDifficultyController(logger)
spell_types = [SpellType.LOCOMOTOR]
# spell_types = [SpellType.REVELIO]
# spell_types = [SpellType.SQUARIO, SpellType.OBLONGIUM, SpellType.RECTANGLIA, SpellType.REVELIO, SpellType.RICTUMSEMPRA]


def create_spell_definitions(spell_types: list[SpellType], difficulty: SpellDifficultyType) -> list[SpellDefinition]:
    return [spell_definition_factory.create(spell_type, difficulty) for spell_type in spell_types]


# tracer factory
def _make_trace() -> SpellTraceAdapter:
    return SpellTraceAdapter(SpellAttemptTrace(spell_id="", spell_name="", key_count=0))


trace_session = SpellTraceSessionManager(
    trace_factory=_make_trace,
    config=SpellTraceSessionConfig(
        natural_break_s=0.9,
        clear_history_on_flush=True,
        label_prefix="ATTEMPT",
    ),
)

easy_matcher = EasySpellMatcher(create_spell_definitions(spell_types, SpellDifficultyType.FORGIVING))
hard_matcher = SpellMatcher(create_spell_definitions(spell_types, SpellDifficultyType.STRICT))

matcher_manager = SpellMatcherManager(difficulty_controller.difficulty)
matcher_manager.register(SpellDifficultyType.FORGIVING, easy_matcher)
matcher_manager.register(SpellDifficultyType.STRICT, hard_matcher)

root = tk.Tk()
root.title("Mock Wand Input")
root.geometry("800x800+100+100")
canvas = tk.Canvas(root, bg="#222", highlightthickness=0)
canvas.pack(fill="both", expand=True)
status = tk.Label(root, text="", fg="#ddd", bg="#111")
status.pack(side="bottom", fill="x")

input = MouseTkInput(logger=logger, root=root, window=canvas)
trail = WandTrail(
    canvas=canvas,
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
    status.config(text=f"({s.x:.3f}, {s.y:.3f}) | {tick_monitor.tick_rate}hz")
    trail.add(s)
    trail.draw()


def on_state_changed(dir: DirectionType) -> None:
    logger.debug(f"State: {dir.name}")


def on_motion_changed(mode: MotionType) -> None:
    logger.debug(f"Motion: {mode.name}")
    trace_session.on_motion_changed(mode)


def on_segment_completed(segment: GestureSegment):
    logger.debug(f"Completed '{segment.direction_type.name}' ({segment.direction:.3f}): {segment.duration_s}s")
    history.add(segment)
    trace_session.on_segment(
        segment,
        history.tail(),
        matcher_manager,
        history_clear_fn=history.clear,  # will be used on natural break if configured
    )


def on_spell(match: SpellMatch):
    logger.info(
        f"{name_provider.get_name()} cast {match.spell_name}! ✨✨ "
        # f"({match.duration_s:.3f}s), {match.segments_used}/{match.total_segments}="
        # f"{match.accuracy * 100:.1f}%."
    )
    trace_session.on_match(match, history_clear_fn=history.clear)


def on_difficulty_toggled() -> None:
    difficulty_controller.toggle_difficulty()
    matcher_manager.set_difficulty(difficulty_controller.difficulty)
    trace_session.on_difficulty_changed()


def main():
    input.position_updated.subscribe(on_sample)
    processor.state_changed.subscribe(on_state_changed)
    processor.motion_changed.subscribe(on_motion_changed)
    processor.segment_completed.subscribe(on_segment_completed)
    matcher_manager.matched.subscribe(on_spell)

    root.bind("t", lambda e: trace_session.toggle())
    root.bind("c", lambda e: trail.clear())
    root.bind("d", lambda e: on_difficulty_toggled())
    root.bind("q", lambda e: root.destroy())

    input.start()
    processor.start()

    interval_s = 1.0 / _SAMPLE_FREQUENCY_HZ
    next_t = time.perf_counter() + interval_s

    try:
        while True:
            root.update_idletasks()
            root.update()

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
