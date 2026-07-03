from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AutoAdvanceSettings:
    """Live, mutable dev toggles shared between the settings panel (writer) and the
    zone controls (reader). Read on each recognized cast, so flips take effect at once.

    - auto_advance: on a recognized cast (rudimentary+), move to the next spell/zone.
    - randomise:    pick the next spell at random from the pool instead of sequentially.
    - in_park_only: restrict the advance pool + Up/Down cycle to in-park spells
                    (explicit numeric-key / dropdown selection still reaches any zone).
    """

    auto_advance: bool = False
    randomise: bool = False
    in_park_only: bool = False
