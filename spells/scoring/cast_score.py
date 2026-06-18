from __future__ import annotations

from dataclasses import dataclass

from spells.spell_cast_quality import SpellCastQuality


@dataclass(frozen=True)
class CastScore:
    label: str
    match_accuracy: float  # raw $1 score, 0..1

    # Additive components (points).
    base: float
    xp_bonus: float
    cadence_bonus: float
    tempo_bonus: float
    streak_bonus: float
    difficulty_weight: float

    total: float
    quality: SpellCastQuality | None  # None = below lowest tier (a failed attempt)

    # Boolean veto outcome. When a gate fails, the cast is rejected and no quality is awarded.
    passed_gates: bool
    gate_failures: tuple[str, ...] = ()

    # True when the cast only reached a tier thanks to the pity (streak) bonus.
    pity_pass: bool = False

    @property
    def recognized(self) -> bool:
        return self.passed_gates and self.quality is not None

    def summary(self) -> str:
        if not self.passed_gates:
            return f"{self.label} REJECTED ({', '.join(self.gate_failures)})"
        tier = self.quality.name if self.quality else "FAILED"
        pity = " [pity]" if self.pity_pass else ""
        return (
            f"{self.label} {tier}{pity} total={self.total:.1f} "
            f"(base={self.base:.1f} xp={self.xp_bonus:.1f} "
            f"cadence={self.cadence_bonus:.1f} tempo={self.tempo_bonus:.1f} streak={self.streak_bonus:.1f})"
        )
