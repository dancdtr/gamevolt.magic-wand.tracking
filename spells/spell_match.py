from dataclasses import dataclass


@dataclass(frozen=True)
class SpellMatch:
    spell_id: str
    spell_name: str
    start_ts_ms: int
    end_ts_ms: int
    duration_s: float
    segments_used: int
    total_segments: int

    @property
    def accuracy(self) -> float:
        return self.segments_used / self.total_segments
