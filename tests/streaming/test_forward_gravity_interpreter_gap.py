from __future__ import annotations

from wand.interpreters.configuration.rmf_settings import RMFSettings
from wand.interpreters.wand_forward_gravity_interpreter import ForwardGravityInterpreter


def test_contiguous_samples_produce_deltas() -> None:
    interpreter = ForwardGravityInterpreter(RMFSettings(max_sample_gap_ms=150.0))
    interpreter.on_sample("W", 0, 1.0, 0.0, 0.0)
    rotation = interpreter.on_sample("W", 8, 0.98, 0.2, 0.0)
    assert rotation.x_delta != 0.0 or rotation.y_delta != 0.0


def test_gap_suppresses_orientation_jump() -> None:
    interpreter = ForwardGravityInterpreter(RMFSettings(max_sample_gap_ms=150.0))
    interpreter.on_sample("W", 0, 1.0, 0.0, 0.0)
    # Wand moved a long way during a 3s outage; the jump must not become a delta.
    rotation = interpreter.on_sample("W", 3000, 0.0, 1.0, 0.0)
    assert rotation.x_delta == 0.0
    assert rotation.y_delta == 0.0
    # Tracking resumes from the new orientation.
    follow_up = interpreter.on_sample("W", 3008, 0.02, 1.0, 0.0)
    assert abs(follow_up.x_delta) < 0.1


def test_backwards_timestamp_treated_as_gap() -> None:
    """A wand reboot rewinds the anchor tick clock; that is a discontinuity."""
    interpreter = ForwardGravityInterpreter(RMFSettings(max_sample_gap_ms=150.0))
    interpreter.on_sample("W", 100_000, 1.0, 0.0, 0.0)
    rotation = interpreter.on_sample("W", 12, 0.0, 1.0, 0.0)
    assert rotation.x_delta == 0.0
    assert rotation.y_delta == 0.0
