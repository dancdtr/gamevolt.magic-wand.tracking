from __future__ import annotations

from logging import Logger

from visualisation.configuration.multi_wand_visualiser_settings import MultiWandVisualiserSettings
from visualisation.headless_visualiser import HeadlessVisualiser
from visualisation.visualiser_protocol import WandVisualiserProtocol


class MultiWandVisualiserFactory:
    def __init__(
        self,
        logger: Logger,
        settings: MultiWandVisualiserSettings,
        tracked_wand_ids: list[str],
    ) -> None:
        self._logger = logger
        self._settings = settings
        self._tracked_wand_ids = tracked_wand_ids

    def create(self) -> WandVisualiserProtocol:
        if not self._settings.is_enabled:
            return HeadlessVisualiser()

        # Imported lazily so headless / CI runs don't require a Qt platform plugin.
        from visualisation.qt.qt_multi_wand_visualiser import QtMultiWandVisualiser

        return QtMultiWandVisualiser(
            logger=self._logger,
            settings=self._settings,
            wand_ids=self._tracked_wand_ids,
        )
