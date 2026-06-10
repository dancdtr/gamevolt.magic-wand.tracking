from __future__ import annotations

import asyncio
import threading

from gamevolt.logging import Logger
from wand.streaming.eliko.configuration.eliko_command_sink_settings import ElikoCommandSinkSettings
from wand.streaming.eliko.eliko_command_client import ElikoCommandClient
from wand.streaming.eliko.pekio_client import Colour, PekioClient


class ElikoWandCommandSink:
    """Routes wand LED feedback over an Eliko PEKIO command channel.

    Surface (`WandCommandSink` protocol):

    - `enter_idle(wand_id)` — slow fade in `idle_colour`. Flags the wand
      idle so a subsequent pulse can restore the fade.
    - `exit_idle(wand_id)`  — `stop_led` (fade-mode hold off). Clears the
      idle flag and cancels any pending pulse restore.
    - `fade_pulse(wand_id, colour, step, duration_s)` — fade in `colour`
      at `step` for the duration. On end, restore: re-fade idle if
      flagged, else off.

    Haptic CMD1s are intentionally not exposed — see `docs/spec.md` §4.5
    for the firmware brown-out background.

    Transport-agnostic: works against either `ElikoClient` (TCP) or
    `ElikoSingleAnchorClient` (serial).

    Pulse restore is scheduled on the asyncio loop (not `threading.Timer`)
    because the underlying transports route sends through
    `asyncio.create_task`, which requires a running loop in the calling
    thread. A Timer thread has none, so a Timer-scheduled restore would
    silently swallow `RuntimeError` and the fade-back would never go out.
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
        self._pulse_handles: dict[str, asyncio.TimerHandle] = {}

    def enter_idle(self, wand_id: str) -> None:
        return
        wand_key = wand_id.upper()
        with self._lock:
            self._cancel_pulse_handle(wand_key)
            self._idle_wands.add(wand_key)
        self._apply_idle(wand_key)

    def exit_idle(self, wand_id: str) -> None:
        return
        wand_key = wand_id.upper()
        with self._lock:
            self._cancel_pulse_handle(wand_key)
            self._idle_wands.discard(wand_key)
        self._pekio.set_tag(f"0x{wand_key}")
        self._pekio.stop_led()

    def fade_pulse(
        self,
        wand_id: str,
        colour: str,
        step: int,
        duration_s: float,
    ) -> None:
        return
        wand_key = wand_id.upper()
        try:
            colour_bits = self._parse_colour(colour)
        except ValueError as exc:
            self._logger.warning(f"ElikoWandCommandSink: invalid pulse colour for wand={wand_key}: {exc}")
            return

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            self._logger.warning(
                f"ElikoWandCommandSink: no running asyncio loop for pulse on wand={wand_key}; firing fade without scheduled restore."
            )
            loop = None

        with self._lock:
            self._cancel_pulse_handle(wand_key)
            if loop is not None:
                handle = loop.call_later(duration_s, self._restore_after_pulse, wand_key)
                self._pulse_handles[wand_key] = handle

        self._pekio.set_tag(f"0x{wand_key}")
        self._pekio.fade(step, colour_bits)

    def _restore_after_pulse(self, wand_key: str) -> None:
        with self._lock:
            self._pulse_handles.pop(wand_key, None)
            is_idle = wand_key in self._idle_wands

        if is_idle:
            self._apply_idle(wand_key)
        else:
            self._pekio.set_tag(f"0x{wand_key}")
            self._pekio.stop_led()

    def _apply_idle(self, wand_key: str) -> None:
        self._pekio.set_tag(f"0x{wand_key}")
        self._pekio.fade_slow(self._idle_colour)

    def _cancel_pulse_handle(self, wand_key: str) -> None:
        handle = self._pulse_handles.pop(wand_key, None)
        if handle is not None:
            handle.cancel()

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
                raise ValueError(f"Unknown LED colour '{part}' in spec='{spec}'. Valid: {[c.name for c in Colour]}") from exc
        return result
