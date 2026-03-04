from wand.configuration.wand_server_settings import WandServerSettings


class WandIdFilter:
    def __init__(self, settings: WandServerSettings) -> None:
        self._allowed_wands: set[str] = set()
        self._settings = settings

        if self._settings.filter_wands:
            for wand_id in self._settings.filtered_wand_ids:
                self.add(wand_id)

    def add(self, wand_id: str) -> None:
        self._allowed_wands.add(wand_id.upper())

    def remove(self, wand_id: str) -> None:
        self._allowed_wands.discard(wand_id.upper())

    def snapshot(self) -> list[str]:
        return sorted(self._allowed_wands)

    def allows(self, wand_id: str) -> bool:
        if not self._settings.filter_wands:
            return True

        return wand_id in self._allowed_wands
