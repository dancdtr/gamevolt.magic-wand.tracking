from dataclasses import field
from typing import Any, ClassVar

from gamevolt.configuration.appsetting import appsetting
from wizards.hogwarts_house import HogwartsHouse


def _parse_houses(value: Any) -> dict[str, HogwartsHouse]:
    if not isinstance(value, dict):
        raise ValueError(f"houses must be a mapping of wand id -> house, got {value!r}")
    out: dict[str, HogwartsHouse] = {}
    for wand_id, house in value.items():
        if isinstance(house, HogwartsHouse):
            out[str(wand_id).upper()] = house
            continue
        name = str(house).strip().upper().replace("-", "_")
        if name not in HogwartsHouse.__members__:
            allowed = ", ".join(HogwartsHouse.__members__)
            raise ValueError(f"unknown house {house!r} for wand {wand_id!r}; expected one of {{{allowed}}}")
        out[str(wand_id).upper()] = HogwartsHouse[name]
    return out


@appsetting
class WandHouseLookup:
    """Maps a wand id to its assigned Hogwarts house. Returns UNASSIGNED for unknown wands."""

    houses: dict[str, HogwartsHouse] = field(default_factory=dict)

    FIELD_HANDLERS: ClassVar[dict[str, Any]] = {
        "houses": _parse_houses,
    }

    def get_house(self, wand_id: str) -> HogwartsHouse:
        return self.houses.get(wand_id.upper(), HogwartsHouse.GRYFFINDOR)
