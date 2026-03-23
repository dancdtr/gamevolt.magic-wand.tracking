class AnchorArea:
    def __init__(self) -> None:
        self._present_ids: set[str] = set()

    def enter(self, wand_id: str) -> None:
        self._present_ids.add(wand_id.upper())

    def exit(self, wand_id: str) -> None:
        self._present_ids.discard(wand_id.upper())

    def is_present(self, wand_id: str) -> bool:
        return wand_id.upper() in self._present_ids

    def ids(self) -> list[str]:
        return list(self._present_ids)
