"""Spell scoring settings, SettingsBase-backed so they live in appsettings.yml.

Two layers:
  - global bonus magnitudes (`bonuses`)
  - per-spell tuning: a `default` block + a list of per-spell `overrides`, each a partial
    `tuning` that inherits anything it omits from `default` (then from the code defaults).

SettingsBase can't take a `dict[str, ...]` field and ignores dataclass defaults for missing
keys, so overrides are a *list* (keyed by `spell`) and tuning fields are all Optional.

`spell_settings(label)` resolves the merged runtime `SpellSettings` the scorer consumes —
this replaces the old SpellSettingsLibrary.
"""

from __future__ import annotations

from gamevolt.configuration.appsetting import appsetting
from spells.settings.spell_settings import GateSettings, SpellSettings, TempoSettings
from spells.spell_cast_quality import SpellCastQuality
from spells.spell_type import SpellType

# Single source of code-level fallbacks (used when neither override nor default specify a field).
_CODE_DEFAULT = SpellSettings()


@appsetting
class BonusSettings:
    """Global bonus magnitudes (shared across all spells)."""

    xp_per_unique_spell: float
    xp_max: float
    cadence_max: float
    tempo_max: float
    streak_per_fail: float


@appsetting
class SpellTuningSettings:
    """Per-spell tuning. All Optional so a `default` or an override `tuning` may be partial;
    a missing field inherits (override → default → code default)."""

    difficulty_weight: float | None = None
    min_match_accuracy: float | None = None
    min_duration_s: float | None = None
    max_duration_s: float | None = None
    min_path_length: float | None = None
    tempo_ideal_min_s: float | None = None
    tempo_ideal_max_s: float | None = None
    tempo_decay_s: float | None = None
    # Quality tiers, SpellCastQuality name -> threshold. If an override sets this, it REPLACES
    # the default set wholesale (a spell can thus drop tiers — not every spell needs all four).
    thresholds: dict[str, int] | None = None


@appsetting
class SpellOverrideSettings:
    spell: SpellType
    tuning: SpellTuningSettings


@appsetting
class SpellScoringSettings:
    bonuses: BonusSettings
    default: SpellTuningSettings
    overrides: list[SpellOverrideSettings]

    def __post_init__(self) -> None:
        super().__post_init__()
        self._by_name = {o.spell.name: o for o in self.overrides}

    def spell_settings(self, label: str) -> SpellSettings:
        """Merge default + per-spell override into the runtime SpellSettings for `label`."""
        override = self._by_name.get(label.upper())
        default = self.default
        tuning = override.tuning if override else None

        def pick(field: str, code_default):
            if tuning is not None and getattr(tuning, field) is not None:
                return getattr(tuning, field)
            if getattr(default, field) is not None:
                return getattr(default, field)
            return code_default

        gates = GateSettings(
            min_match_accuracy=pick("min_match_accuracy", _CODE_DEFAULT.gates.min_match_accuracy),
            min_duration_s=pick("min_duration_s", _CODE_DEFAULT.gates.min_duration_s),
            max_duration_s=pick("max_duration_s", _CODE_DEFAULT.gates.max_duration_s),
            min_path_length=pick("min_path_length", _CODE_DEFAULT.gates.min_path_length),
        )
        tempo = TempoSettings(
            ideal_min_s=pick("tempo_ideal_min_s", _CODE_DEFAULT.tempo.ideal_min_s),
            ideal_max_s=pick("tempo_ideal_max_s", _CODE_DEFAULT.tempo.ideal_max_s),
            decay_s=pick("tempo_decay_s", _CODE_DEFAULT.tempo.decay_s),
        )
        return SpellSettings(
            difficulty_weight=pick("difficulty_weight", _CODE_DEFAULT.difficulty_weight),
            gates=gates,
            tempo=tempo,
            quality_thresholds=self._resolve_thresholds(tuning, default),
        )

    def _resolve_thresholds(
        self,
        tuning: SpellTuningSettings | None,
        default: SpellTuningSettings,
    ) -> dict[SpellCastQuality, int]:
        # Override tiers (if it sets any) replace the set wholesale; else default's; else code.
        if tuning is not None:
            override_tiers = _tier_map(tuning)
            if override_tiers:
                return override_tiers
        default_tiers = _tier_map(default)
        return default_tiers or dict(_CODE_DEFAULT.quality_thresholds)


def _tier_map(t: SpellTuningSettings) -> dict[SpellCastQuality, int]:
    if not t.thresholds:
        return {}
    return {SpellCastQuality[name.upper()]: value for name, value in t.thresholds.items()}
