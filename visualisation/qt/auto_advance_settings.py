from __future__ import annotations

from dataclasses import dataclass, field

from spells.spell_cast_quality import SpellCastQuality


@dataclass
class AutoAdvanceSettings:
    """Live, mutable dev toggles shared between the settings panel (writer) and the
    zone controls (reader). Read on each recognized cast, so flips take effect at once.

    - auto_advance: on a recognized cast, move to the next spell/zone.
    - randomise:    pick the next spell at random from the pool instead of sequentially.
    - in_park_only: restrict the advance pool + Up/Down cycle to in-park spells
                    (explicit numeric-key / dropdown selection still reaches any zone).
    - min_advance_quality: the lowest cast quality tier that advances. A cast below
                    this tier stays on the same spell so the player can retry / improve.
    """

    auto_advance: bool = True
    randomise: bool = True
    in_park_only: bool = True
    min_advance_quality: SpellCastQuality = field(default=SpellCastQuality.RUDIMENTARY)
