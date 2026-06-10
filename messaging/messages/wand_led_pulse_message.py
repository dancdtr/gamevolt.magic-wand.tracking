from dataclasses import dataclass

from gamevolt.messaging.message import Message


@dataclass
class WandLedPulseMessage(Message):
    """Time-bounded LED blink cue. Sink restores idle state when the pulse ends.

    `colour` names a `pekio_client.Colour` enum member (e.g. "GREEN", "RED"). The
    sink resolves the name; multi-bit forms via pipe-join ("RED|GREEN") are
    accepted.
    """

    tag_id: str
    colour: str
    period_ms: int
    duty_ms: int
    duration_s: float
