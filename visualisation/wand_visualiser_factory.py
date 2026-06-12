from __future__ import annotations

from logging import Logger

from visualisation.configuration.wand_visualiser_settings import WandVisualiserSettings
from visualisation.headless_visualiser import HeadlessVisualiser
from visualisation.visualiser_protocol import WandVisualiserProtocol


class WandVisualiserFactory:
    def __init__(
        self,
        logger: Logger,
        wand_visualiser_settings: WandVisualiserSettings,
    ) -> None:
        self._wand_visualiser_settings = wand_visualiser_settings
        self._logger = logger

    def create(self) -> WandVisualiserProtocol:
        if not self._wand_visualiser_settings.is_enabled:
            return HeadlessVisualiser()

        # Imported lazily so headless / CI runs don't require a Qt platform plugin.
        from visualisation.qt.qt_wand_visualiser import QtWandVisualiser

        return QtWandVisualiser(
            logger=self._logger,
            settings=self._wand_visualiser_settings,
        )
