from __future__ import annotations

from dataclasses import dataclass, field

from spells.spell_cast_quality import SpellCastQuality
from spells.spell_tag import SpellTag


@dataclass
class AutoAdvanceSettings:
    """Live, mutable dev toggles shared between the settings panel (writer) and the
    zone controls (reader). Read on each recognized cast, so flips take effect at once.

    - auto_advance: on a recognized cast, move to the next spell/zone.
    - randomise:    pick the next spell at random from the pool instead of sequentially.
    - enabled_tags: restrict the advance pool + Up/Down cycle + dropdown to zones whose
                    spells carry at least one of these tags (explicit numeric-key
                    selection still reaches any zone). Empty set => no zones eligible.
    - min_advance_quality: the lowest cast quality tier that advances. A cast below
                    this tier stays on the same spell so the player can retry / improve.
    """

    auto_advance: bool = True
    randomise: bool = True
    enabled_tags: set[SpellTag] = field(default_factory=lambda: {SpellTag.PARK, SpellTag.CDTR})
    min_advance_quality: SpellCastQuality = field(default=SpellCastQuality.RUDIMENTARY)
