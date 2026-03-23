import asyncio
from collections.abc import Callable

from anchor_area.anchor_area_manager import AnchorAreaManager
from gamevolt.logging._logger import Logger
from messaging.messages.wand_haptic_sequence_message import WandHapticSequenceMessage
from messaging.messages.wand_led_message import WandLedMessage
from messaging.messages.wand_tx_message import WandTxMessage
from wand.configuration.wand_device_controller_settings import WandDeviceControllerSettings


class WandDeviceController:
    def __init__(self, logger: Logger, settings: WandDeviceControllerSettings, anchor_area_manager: AnchorAreaManager) -> None:
        self._anchor_area_manager = anchor_area_manager
        self._settings = settings
        self._logger = logger

    def blast_wand_active(self, wand_id: str) -> None:
        self._anchor_area_manager.blast_message_to_wand(wand_id, WandTxMessage(wand_id, True, sequence_id=0))

    def blast_wand_inactive(self, wand_id: str) -> None:
        self._anchor_area_manager.blast_message_to_wand(wand_id, WandTxMessage(wand_id, False, sequence_id=0))

    def set_wand_active(self, wand_id: str) -> None:
        self._logger.debug(f"Setting wand ({wand_id}) active..")
        self._set_wand_tx(wand_id, True)

        self._delay(
            self._settings.command_broadcast_interval, lambda: self._play_haptic_sequence(wand_id, self._settings.wand_chosen_haptic_cues)
        )

    def set_wand_inactive(self, wand_id: str) -> None:
        if not self._settings.disable_wand_tx:
            return

        self._logger.debug(f"Setting wand ({wand_id}) setting inactive...")
        self._set_wand_tx(wand_id, False)

    def play_spell_cast_cue(self, wand_id: str, has_sufficient_level: bool) -> None:
        self._logger.debug(f"Playing wand ({wand_id}) {'successful cast' if has_sufficient_level else 'under cast'} haptic sequence...")
        cues = self._settings.spell_under_cast_haptic_cues if has_sufficient_level else self._settings.spell_under_cast_haptic_cues
        self._play_haptic_sequence(wand_id, cues)

    def _set_wand_tx(self, wand_id: str, enabled: bool) -> None:
        self._logger.verbose(f"{'Enabling' if enabled else 'Disabling'} wand ({wand_id}) TX...")
        self._anchor_area_manager.relay_message_to_wand(wand_id, WandTxMessage(wand_id, enabled, sequence_id=0))

    def _set_wand_led(self, wand_id: str, enabled: bool) -> None:
        self._logger.verbose(f"{'Enabling' if enabled else 'Disabling'} wand ({wand_id}) LED...")
        self._anchor_area_manager.relay_message_to_wand(wand_id, WandLedMessage(wand_id, enabled=enabled, sequence_id=0))

    def _play_haptic_sequence(self, wand_id: str, pattern_ids: list[int]) -> None:
        def clamp_pattern_id(pattern_id: int) -> int:
            return max(1, min(127, pattern_id))

        clamped_ids = [clamp_pattern_id(pattern_id) for pattern_id in pattern_ids[:8]]

        self._logger.verbose(f"Playing wand ({wand_id}) haptic sequence {clamped_ids}...")
        self._anchor_area_manager.relay_message_to_wand(wand_id, WandHapticSequenceMessage(wand_id, pattern_ids=clamped_ids))

    def _delay(self, delay: float, func: Callable) -> None:
        asyncio.create_task(self._run_delayed(delay, func))

    async def _run_delayed(self, delay: float, func: Callable) -> None:
        loop = asyncio.get_running_loop()

        def wrapped() -> None:
            try:
                func()
            except Exception:
                self._logger.exception(f"Delayed action failed for '{func.__name__}'")

        loop.call_later(delay, wrapped)
