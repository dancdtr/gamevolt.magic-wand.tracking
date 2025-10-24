from dataclasses import dataclass


@dataclass
class SpellTraceSessionSettings:
    natural_break_s: float = 0.9  # idle NONE ≥ this ends the attempt
    clear_history_on_flush: bool = True
    label_prefix: str = "TRACE"
