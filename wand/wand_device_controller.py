from gamevolt.logging._logger import Logger
from spells.spell_cast_quality import SpellCastQuality
from wand.configuration.wand_device_controller_settings import WandDeviceControllerSettings
from wand.wand_command_sink import WandCommandSink


class WandDeviceController:
    """Outbound LED feedback for tracked wands.

    Haptic cues are disabled while the wand-firmware brown-out under
    concurrent UWB + motor load is unresolved (see `docs/spec.md` §4.5).
    All feedback is rendered as LED states by the command sink.
    """

    def __init__(self, logger: Logger, settings: WandDeviceControllerSettings, command_sink: WandCommandSink) -> None:
        self._command_sink = command_sink
        self._settings = settings
        self._logger = logger

    def activate_wand(self, wand_id: str) -> None:
        self._logger.debug(f"Activating wand ({wand_id})...")
        self._command_sink.enter_idle(wand_id)

    def deactivate_wand(self, wand_id: str) -> None:
        self._logger.verbose(f"Deactivating wand ({wand_id})...")
        self._command_sink.exit_idle(wand_id)

    def play_spell_cast_cue(self, wand_id: str, quality: SpellCastQuality) -> None:
        handler = {
            SpellCastQuality.RUDIMENTARY: self.play_rudimentary_spell_cast_cue,
            SpellCastQuality.SKILLED: self.play_skilled_spell_cast_cue,
            SpellCastQuality.EXPERIENCED: self.play_experienced_spell_cast_cue,
            SpellCastQuality.MASTERED: self.play_mastered_spell_cast_cue,
        }[quality]
        handler(wand_id)

    def play_rudimentary_spell_cast_cue(self, wand_id: str) -> None:
        self._fade_pulse(wand_id, self._settings.rudimentary_spell_cast_pulse_duration_s)

    def play_skilled_spell_cast_cue(self, wand_id: str) -> None:
        self._fade_pulse(wand_id, self._settings.skilled_spell_cast_pulse_duration_s)

    def play_experienced_spell_cast_cue(self, wand_id: str) -> None:
        self._fade_pulse(wand_id, self._settings.experienced_spell_cast_pulse_duration_s)

    def play_mastered_spell_cast_cue(self, wand_id: str) -> None:
        self._fade_pulse(wand_id, self._settings.mastered_spell_cast_pulse_duration_s)

    def _fade_pulse(self, wand_id: str, duration_s: float) -> None:
        self._logger.verbose(f"Playing wand ({wand_id}) spell-cast LED fade pulse for {duration_s}s...")
        self._command_sink.fade_pulse(
            wand_id=wand_id,
            colour=self._settings.spell_cast_pulse_colour,
            step=self._settings.spell_cast_pulse_step,
            duration_s=duration_s,
        )
