from __future__ import annotations

import threading

from gamevolt.logging import Logger
from gamevolt.messaging.message import Message
from messaging.messages.wand_led_message import WandLedMessage
from messaging.messages.wand_led_pulse_message import WandLedPulseMessage
from wand.streaming.eliko.configuration.eliko_command_sink_settings import ElikoCommandSinkSettings
from wand.streaming.eliko.eliko_command_client import ElikoCommandClient
from wand.streaming.eliko.pekio_client import Colour, PekioClient


class ElikoWandCommandSink:
    """Routes wand commands over an Eliko PEKIO command channel.

    Translates internal `Message` types into PEKIO CMD1 sequences via
    `PekioClient`:

    - `WandLedMessage(enabled=True)`  → slow fade in `idle_colour`. Marks the
      wand as "in idle" so a pulse can restore the fade when it ends.
    - `WandLedMessage(enabled=False)` → `stop_led` (fade-mode off). Clears
      the idle flag and cancels any pending pulse restore.
    - `WandLedPulseMessage`           → blink for `duration_s` in the
      message's colour, then restore: re-fade `idle_colour` if the wand is
      still flagged idle, else `stop_led`.

    Haptic messages (TX-enable, periodic buzz, hwave) are intentionally
    not handled — see `docs/spec.md` for the firmware brown-out issue that
    forced this surface to LED-only.

    Transport-agnostic: works against either `ElikoClient` (TCP) or
    `ElikoSingleAnchorClient` (serial).
    """

    def __init__(self, logger: Logger, client: ElikoCommandClient, settings: ElikoCommandSinkSettings) -> None:
        self._logger = logger
        self._client = client
        self._settings = settings
        self._idle_colour = self._parse_colour(settings.idle_colour)
        # PekioClient drives PEKIO command construction; we re-tag per call.
        self._pekio = PekioClient(send_line=client.send_command)

        self._lock = threading.RLock()
        self._idle_wands: set[str] = set()
        self._pulse_timers: dict[str, threading.Timer] = {}

    def send_to_wand(self, wand_id: str, message: Message) -> None:
        self._dispatch(wand_id, message)

    def broadcast_to_wand(self, wand_id: str, message: Message) -> None:
        # Eliko routes commands by tag id internally; broadcast = send.
        self._dispatch(wand_id, message)

    def _dispatch(self, wand_id: str, message: Message) -> None:
        wand_key = wand_id.upper()

        if isinstance(message, WandLedMessage):
            if message.enabled:
                self._enter_idle(wand_key)
            else:
                self._exit_idle(wand_key)
            return

        if isinstance(message, WandLedPulseMessage):
            self._start_pulse(wand_key, message)
            return

        self._logger.debug(
            f"ElikoWandCommandSink: no Eliko mapping for {type(message).__name__} (wand={wand_id}); ignoring."
        )

    def _enter_idle(self, wand_key: str) -> None:
        with self._lock:
            self._cancel_pulse_timer(wand_key)
            self._idle_wands.add(wand_key)
        self._apply_idle(wand_key)

    def _exit_idle(self, wand_key: str) -> None:
        with self._lock:
            self._cancel_pulse_timer(wand_key)
            self._idle_wands.discard(wand_key)
        self._pekio.set_tag(f"0x{wand_key}")
        self._pekio.stop_led()

    def _start_pulse(self, wand_key: str, message: WandLedPulseMessage) -> None:
        try:
            colour = self._parse_colour(message.colour)
        except ValueError as exc:
            self._logger.warning(f"ElikoWandCommandSink: invalid pulse colour for wand={wand_key}: {exc}")
            return

        with self._lock:
            self._cancel_pulse_timer(wand_key)
            timer = threading.Timer(message.duration_s, self._restore_after_pulse, args=(wand_key,))
            timer.daemon = True
            self._pulse_timers[wand_key] = timer

        self._pekio.set_tag(f"0x{wand_key}")
        self._pekio.blink(message.period_ms, message.duty_ms, colour)
        timer.start()

    def _restore_after_pulse(self, wand_key: str) -> None:
        with self._lock:
            self._pulse_timers.pop(wand_key, None)
            is_idle = wand_key in self._idle_wands

        if is_idle:
            self._apply_idle(wand_key)
        else:
            self._pekio.set_tag(f"0x{wand_key}")
            self._pekio.stop_led()

    def _apply_idle(self, wand_key: str) -> None:
        self._pekio.set_tag(f"0x{wand_key}")
        self._pekio.fade_slow(self._idle_colour)

    def _cancel_pulse_timer(self, wand_key: str) -> None:
        timer = self._pulse_timers.pop(wand_key, None)
        if timer is not None:
            timer.cancel()

    @staticmethod
    def _parse_colour(spec: str) -> Colour:
        result = Colour.OFF
        for part in spec.split("|"):
            name = part.strip().upper()
            if not name:
                continue
            try:
                result |= Colour[name]
            except KeyError as exc:
                raise ValueError(
                    f"Unknown LED colour '{part}' in spec='{spec}'. "
                    f"Valid: {[c.name for c in Colour]}"
                ) from exc
        return result
