from __future__ import annotations

import asyncio

from gamevolt.logging._logger import Logger
from services.profile_service_base import ProfileServiceBase
from services.wand_presence_reporter_base import WandPresenceReporterBase
from services.wizard_session_store import WizardSessionStore
from zones.zone_manager_protocol import ZoneManagerProtocol


class WandSessionCoordinator:
    """On zone enter/exit, fetches profile + reports presence to outward services."""

    def __init__(
        self,
        logger: Logger,
        zone_manager: ZoneManagerProtocol,
        profile_service: ProfileServiceBase,
        presence_reporter: WandPresenceReporterBase,
        session_store: WizardSessionStore,
    ) -> None:
        self._logger = logger
        self._zone_manager = zone_manager
        self._profile_service = profile_service
        self._presence_reporter = presence_reporter
        self._session_store = session_store

    def start(self) -> None:
        self._zone_manager.wand_entered_zone.subscribe(self._on_wand_entered_zone)
        self._zone_manager.wand_exited_zone.subscribe(self._on_wand_exited_zone)

    def stop(self) -> None:
        self._zone_manager.wand_entered_zone.unsubscribe(self._on_wand_entered_zone)
        self._zone_manager.wand_exited_zone.unsubscribe(self._on_wand_exited_zone)
        self._session_store.clear_all()

    def _on_wand_entered_zone(self, wand_id: str, zone_id: str) -> None:
        asyncio.create_task(self._handle_entered(wand_id))

    def _on_wand_exited_zone(self, wand_id: str, zone_id: str) -> None:
        asyncio.create_task(self._handle_exited(wand_id))

    async def _handle_entered(self, wand_id: str) -> None:
        try:
            profile = await self._profile_service.get_profile(wand_id)
            self._session_store.set(profile)
            await self._presence_reporter.report_entered(wand_id)
        except Exception:
            self._logger.exception(f"WandSessionCoordinator failed handling enter for ({wand_id})")

    async def _handle_exited(self, wand_id: str) -> None:
        try:
            await self._presence_reporter.report_exited(wand_id)
        except Exception:
            self._logger.exception(f"WandSessionCoordinator failed handling exit for ({wand_id})")
        finally:
            self._session_store.clear(wand_id)
