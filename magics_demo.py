from __future__ import annotations

import tkinter as tk

from gamevolt_debugging import TickMonitor
from gamevolt_logging import get_logger

from input.mouse_tk_input import MouseTkInput
from input.wand_position import WandPosition
from motion.direction_type import DirectionType
from motion.gesture_history import GestureHistory
from motion.gesture_segment import GestureSegment
from motion.motion_processor import DirectionType, MotionProcessor
from motion.motion_processor_settings import MotionProcessorSettings
from spell_library import *
from spells.spell_match import SpellMatch
from spells.spell_matcher import SpellMatcher
from wand_trail import WandTrail

_SAMPLE_FREQUENCY_HZ = 32
_INTERVAL_MS = int(1000 / _SAMPLE_FREQUENCY_HZ)

logger = get_logger()
tick_monitor = TickMonitor(30)

history = GestureHistory(max_segments=20, max_age_s=5.0)
# matcher = SpellMatcher([SQUARIO, OBLONGIUM, RECTANGLIA, REVELIO, RICTUMSEMPRA])
# matcher = SpellMatcher([RICTUMSEMPRA])
# matcher = SpellMatcher([SQUARIO, OBLONGIUM, RECTANGLIA])
matcher = SpellMatcher([LOCOMOTOR, REVELIO])
# matcher = SpellMatcher([RICTUMSEMPRA])


root = tk.Tk()
root.title("Mock Wand Input")
root.geometry("800x600+100+100")
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


processor = MotionProcessor(
    input=input,
    settings=MotionProcessorSettings(
        speed_start=0.50,
        speed_stop=0.20,
        min_state_duration_s=0.03,
        min_dir_duration_s=0.03,
        axis_deadband_per_s=0.10,
    ),
)


def on_sample(s: WandPosition) -> None:
    status.config(text=f"({s.x:.3f}, {s.y:.3f}) | {tick_monitor.tick_rate}hz")
    # print(s)
    trail.add(s)
    trail.draw()


def on_motion_started(flag: DirectionType) -> None:
    return
    print(f"Started motion: {flag.name}")


def on_segment_completed(segment: GestureSegment):
    # print(f"Completed '{segment.direction_type.name}' ({segment.direction:.3f}): {segment.duration_s}s")
    history.add(segment)
    matcher.try_match(history.tail())


def on_spell(match: SpellMatch):
    print(
        f"Dan cast {match.spell_name}! ✨✨"  # ({match.duration_s:.3f}s duration), {match.segments_used}/{match.total_segments}={match.accuracy * 100:.1f}% accuracy."
    )
    history.clear()


def main():
    input.position_updated.subscribe(on_sample)
    processor.state_changed.subscribe(on_motion_started)
    processor.segment_completed.subscribe(on_segment_completed)
    matcher.matched.subscribe(on_spell)

    root.bind("c", lambda e: trail.clear())

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
