from __future__ import annotations

import tkinter as tk

from gamevolt_debugging import TickMonitor
from gamevolt_logging import get_logger

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

_SAMPLE_FREQUENCY_HZ = 32
_INTERVAL_MS = int(1000 / _SAMPLE_FREQUENCY_HZ)


def _create_spell_definitions(spell_types: list[SpellType], difficulty: SpellDifficultyType) -> list[SpellDefinition]:
    return [spell_definition_factory.create(spell_type, difficulty) for spell_type in spell_types]


logger = get_logger()
tick_monitor = TickMonitor(30)

history = GestureHistory(max_segments=20, max_age_s=5.0)

spell_definition_factory = SpellDefinitionFactory()
difficulty_controller = SpellDifficultyController()
spell_types = [SpellType.LOCOMOTOR, SpellType.REVELIO]
# spell_types = [SpellType.SQUARIO, SpellType.OBLONGIUM, SpellType.RECTANGLIA, SpellType.REVELIO, SpellType.RICTUMSEMPRA]

easy_matcher = EasySpellMatcher(_create_spell_definitions(spell_types, SpellDifficultyType.EASY))
hard_matcher = SpellMatcher(_create_spell_definitions(spell_types, SpellDifficultyType.HARD))

matcher_manager = SpellMatcherManager(difficulty_controller.difficulty)
matcher_manager.register(SpellDifficultyType.EASY, easy_matcher)
matcher_manager.register(SpellDifficultyType.HARD, hard_matcher)

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
    # print(s)
    trail.add(s)
    trail.draw()


def on_state_changed(dir: DirectionType) -> None:
    # print(f"State: {dir.name}")
    pass


def on_motion_changed(dir: MotionType) -> None:
    # print(f"Motion: {dir.name}")
    pass


def on_difficulty_toggled() -> None:
    difficulty_controller.toggle_difficulty()
    matcher_manager.set_difficulty(difficulty_controller.difficulty)


def on_segment_completed(segment: GestureSegment):
    print(f"Completed '{segment.direction_type.name}' ({segment.direction:.3f}): {segment.duration_s}s")
    history.add(segment)
    matcher_manager.try_match(history.tail())


def on_spell(match: SpellMatch):
    print(
        f"{name_provider.get_name()} cast {match.spell_name}! ✨✨ ({match.duration_s:.3f}s duration), {match.segments_used}/{match.total_segments}={match.accuracy * 100:.1f}% accuracy."
    )
    history.clear()


def main():
    input.position_updated.subscribe(on_sample)
    processor.state_changed.subscribe(on_state_changed)
    processor.motion_changed.subscribe(on_motion_changed)
    processor.segment_completed.subscribe(on_segment_completed)
    matcher_manager.matched.subscribe(on_spell)

    root.bind("c", lambda e: trail.clear())
    root.bind("d", lambda e: on_difficulty_toggled())

    input.start()
    processor.start()

    def tick():
        tick_monitor.tick()
        input.update()
        root.after(_INTERVAL_MS, tick)

    root.after(_INTERVAL_MS, tick)
    root.mainloop()


if __name__ == "__main__":
    main()
