from gamevolt.logging._logger import Logger
from messaging.messages.wand_led_message import WandLedMessage
from messaging.messages.wand_led_pulse_message import WandLedPulseMessage
from wand.configuration.wand_device_controller_settings import WandDeviceControllerSettings
from wand.wand_command_sink import WandCommandSink


class WandDeviceController:
    """Outbound LED feedback for tracked wands.

    Haptic cues are disabled while the wand-firmware brown-out under
    concurrent UWB + motor load is unresolved (see `docs/spec.md`). All
    feedback is rendered as LED states by the command sink.
    """

    def __init__(self, logger: Logger, settings: WandDeviceControllerSettings, command_sink: WandCommandSink) -> None:
        self._command_sink = command_sink
        self._settings = settings
        self._logger = logger

    def activate_wand(self, wand_id: str) -> None:
        self._logger.debug(f"Activating wand ({wand_id})...")
        self._command_sink.send_to_wand(wand_id, WandLedMessage(wand_id, enabled=True, sequence_id=0))

    def deactivate_wand(self, wand_id: str) -> None:
        self._logger.verbose(f"Deactivating wand ({wand_id})...")
        self._command_sink.send_to_wand(wand_id, WandLedMessage(wand_id, enabled=False, sequence_id=0))

    def play_spell_cast_cue(self, wand_id: str, has_sufficient_level: bool) -> None:
        self._logger.verbose(f"Playing wand ({wand_id}) spell-cast LED pulse...")
        self._command_sink.send_to_wand(
            wand_id,
            WandLedPulseMessage(
                tag_id=wand_id,
                colour=self._settings.spell_cast_pulse_colour,
                period_ms=self._settings.spell_cast_pulse_period_ms,
                duty_ms=self._settings.spell_cast_pulse_duty_ms,
                duration_s=self._settings.spell_cast_pulse_duration_s,
            ),
        )
