class WandIdFilter:
    """Allowlist for incoming wand IDs.

    Empty allowlist means allow all (no filtering); non-empty means only
    permit ids in the set. Ids are compared case-insensitively (stored upper).
    """

    def __init__(self, allowed_ids: list[str]) -> None:
        self._allowed_wands: set[str] = {wand_id.upper() for wand_id in allowed_ids}

    @property
    def filtering(self) -> bool:
        return len(self._allowed_wands) > 0

    def add(self, wand_id: str) -> None:
        self._allowed_wands.add(wand_id.upper())

    def remove(self, wand_id: str) -> None:
        self._allowed_wands.discard(wand_id.upper())

    def snapshot(self) -> list[str]:
        return sorted(self._allowed_wands)

    def allows(self, wand_id: str) -> bool:
        if not self.filtering:
            return True

        return wand_id.upper() in self._allowed_wands
