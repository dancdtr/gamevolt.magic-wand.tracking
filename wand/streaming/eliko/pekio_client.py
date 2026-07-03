"""PEKIO command builder for the Eliko single-anchor wand control channel.

Wraps the CMD1 / CMD0 / SPQF vocabulary verified against the firmware on
2026-06-03. Owns sequence allocation and the current target tag; delegates
the actual byte send to a `send_line` callable so the same client can run
against a serial port (dev console), a `SerialTransport` (production sink),
or a test fake.

Hex param layout (CMD1, 0xZZYYXXWW):
    Blink:  ZZ=period*10ms  YY=duty*1ms   XX=haptic*50ms  WW=LED/haptic bits
    Fade:   ZZ=step         YY=0          XX=haptic*50ms  WW|=0x40
    Hwave:  ZZ=wave1        YY=wave2      XX=wave3        WW=0x90
    WW bits: 0=R 1=G 2=B 3=W 4=haptic 6=fade 7=hwave
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from enum import IntFlag

_LED_BITS = {"R": 0x01, "G": 0x02, "B": 0x04, "W": 0x08}
_HAPTIC_BIT = 0x10
_FADE_BIT = 0x40
_HWAVE_BIT = 0x80

# Blink preset timings — tune to taste. Period must be > duty.
BLINK_FAST_PERIOD_MS = 100
BLINK_FAST_DUTY_MS = 15
BLINK_MEDIUM_PERIOD_MS = 500
BLINK_MEDIUM_DUTY_MS = 100
BLINK_SLOW_PERIOD_MS = 2550
BLINK_SLOW_DUTY_MS = 255

# Fade preset steps — lower = slower fade, higher = faster cycle.
FADE_SLOW_STEP = 2
FADE_MEDIUM_STEP = 8
FADE_FAST_STEP = 15

# Buzz preset periods (periodic haptic pulse spacing in ms).
# Encoded into XX byte as period_ms / 50, so resolution is 50ms steps.
BUZZ_FAST_PERIOD_MS = 600
BUZZ_MEDIUM_PERIOD_MS = 3000
BUZZ_SLOW_PERIOD_MS = 5000
DEFAULT_BUZZ_PERIOD_MS = BUZZ_MEDIUM_PERIOD_MS  # used when `buzz=True`

# Named haptic patterns — tuples of waveform IDs played by `hwave`/`buzz_hwave`.
# Unpack at the call site:
#   hwave(*BUZZ_PATTERN_1)
#   buzz_hwave('slow', *BUZZ_PATTERN_1)
# Hwave plays each waveform back-to-back; effective minimum repeat period is
# bounded by total playback duration of the sequence. Edit / add / rename as
# the wand's waveform library is explored.
BUZZ_PATTERN_1: tuple[int, ...] = (93, 14, 56)  # spell-cast cue (three-waveform chain)
BUZZ_PATTERN_2: tuple[int, ...] = (1,)  # single short tap
BUZZ_PATTERN_3: tuple[int, ...] = (16,)  # single bump
BUZZ_PATTERN_4: tuple[int, ...] = (82, 70)  # double bump
BUZZ_PATTERN_5: tuple[int, ...] = (1, 1, 1)  # triple tap

# `stop()` uses fade-form with this step to hold the LED-off state and
# suppress the firmware default green blink.
STOP_FADE_STEP = 255

# Delay between CMD1=0 and the fade-form re-hold inside `stop_all()`. Without
# a gap the firmware tends to either dedupe or latch its default green blink
# before the fade engages. 50ms is empirically enough for both commands to
# land separately while staying imperceptible.
STOP_ALL_CHAIN_DELAY_S = 0.05

# `hwave_oneshot` fires a hwave then schedules a fade-form clear after this
# delay so the wand's "last CMD1" cache no longer holds the hwave value —
# next `hwave_oneshot` call with the same waveform won't be deduped.
DEFAULT_HWAVE_CLEAR_DELAY_S = 0.5

# Accepted types for the `buzz` kwarg on LED methods.
Buzz = bool | int | str | None


class Colour(IntFlag):
    """LED bit flags. Combine with `|`, e.g. `Colour.RED | Colour.BLUE`."""

    OFF = 0
    RED = 0x01
    GREEN = 0x02
    BLUE = 0x04
    WHITE = 0x08
    # RGB pairs
    YELLOW = RED | GREEN
    MAGENTA = RED | BLUE
    CYAN = GREEN | BLUE
    RGB = RED | GREEN | BLUE
    PINK = RED | WHITE
    LIME = GREEN | WHITE
    SKY = BLUE | WHITE
    WARM_WHITE = RED | GREEN | WHITE
    PURPLE = RED | BLUE | WHITE
    ICE = GREEN | BLUE | WHITE
    ALL = RED | GREEN | BLUE | WHITE


def _resolve_buzz(buzz: Buzz) -> int:
    """Normalise a `buzz` kwarg into period_ms.

    Accepts:
        None / False  → 0  (no buzz)
        True          → DEFAULT_BUZZ_PERIOD_MS
        int           → literal period in ms
        'fast' / 'medium' / 'slow' → matching constant
    """
    if buzz is None or buzz is False:
        return 0
    if buzz is True:
        return DEFAULT_BUZZ_PERIOD_MS
    if isinstance(buzz, int):
        return buzz
    if isinstance(buzz, str):
        name = buzz.lower()
        presets = {
            "fast": BUZZ_FAST_PERIOD_MS,
            "medium": BUZZ_MEDIUM_PERIOD_MS,
            "slow": BUZZ_SLOW_PERIOD_MS,
        }
        if name not in presets:
            raise ValueError(f"buzz preset must be one of {list(presets)} or int (ms); got {buzz!r}")
        return presets[name]
    raise TypeError(f"buzz must be bool, int, str, or None; got {type(buzz).__name__}")


def _leds_to_bits(leds: Colour | str | int | None) -> int:
    if leds is None:
        return 0
    if isinstance(leds, Colour):
        return int(leds) & 0x0F
    if isinstance(leds, int):
        return leds & 0x0F
    bits = 0
    for ch in leds.upper():
        bits |= _LED_BITS.get(ch, 0)
    return bits


class PekioClient:
    """PEKIO command builder. State: sequence counter + current target tag."""

    def __init__(self, send_line: Callable[[str], None], tag: str = "0x1DAE") -> None:
        self._send_line = send_line
        self._tag = tag
        self._seq = 0
        self._pending_stop: threading.Timer | None = None
        self._buzz_hwave_timer: threading.Timer | None = None
        self._buzz_hwave_waveforms: tuple[int, ...] = ()
        self._buzz_hwave_period_s: float = 0.0
        # Generation counter — bumped on every buzz_hwave / buzz_hwave_stop call
        # so in-flight timer threads can detect they've been superseded and bail.
        self._buzz_hwave_gen: int = 0
        # Last CMD1 param sent. `hwave` checks this to detect when a new
        # hwave would be a firmware-deduped consecutive duplicate and
        # pre-inserts a fade-form breaker.
        self._last_cmd1_param: int | None = None
        # Alternates each time a dedupe-breaker fires so back-to-back
        # breakers don't dedupe themselves (255 vs 254 step byte).
        self._dedupe_breaker_alt: bool = False
        # `hwave_oneshot` schedules a deferred fade-form clear via this slot.
        self._hwave_clear_timer: threading.Timer | None = None

    @property
    def target_tag(self) -> str:
        return self._tag

    def set_tag(self, tag: str) -> None:
        self._tag = tag

    def _next_seq(self) -> str:
        self._seq = (self._seq + 1) % 256
        return f"{self._seq:03d}"

    def cmd1(self, param: int) -> None:
        self._cancel_pending_stop()
        self._last_cmd1_param = param & 0xFFFFFFFF
        self._send_line(f"$PEKIO,DC,{self._next_seq()},CMD1,{self._tag},0x{param & 0xFFFFFFFF:08X}")

    def cmd0(self, preset: int) -> None:
        """CMD0 preset on YY. TX preamble + data type kept at the IMU-enable values."""
        self._cancel_pending_stop()
        param = ((preset & 0xFF) << 16) | 0x0903
        self._send_line(f"$PEKIO,DC,{self._next_seq()},CMD0,{self._tag},0x{param & 0xFFFFFFFF:08X}")

    def enable_imu(self) -> None:
        """Enable IMU sampling on the current tag — CMD0 with PR data type
        (0x00000903). CMD0 is volatile on the wand, so this must be re-issued
        after any reboot to restart PR output.
        """
        self.cmd0(0)

    def _cancel_pending_stop(self) -> None:
        if self._pending_stop is not None:
            self._pending_stop.cancel()
            self._pending_stop = None

    def _schedule_stop(self, duration_s: float) -> None:
        timer = threading.Timer(duration_s, self._fire_stop)
        timer.daemon = True
        self._pending_stop = timer
        timer.start()

    def _fire_stop(self) -> None:
        self._pending_stop = None
        self.stop()

    def spqf(self, flag: str) -> None:
        """Subscribe to anchor data stream. 'P' = PR (IMU), 'R' = RR (ranging)."""
        self._send_line(f"$PEKIO,DC,{self._next_seq()},SPQF,{flag.upper()}")

    def stop_led(self) -> None:
        """Hold LEDs off without touching firmware-driven haptic state.

        Cancels any `buzz_hwave` Python-driven periodic. Then sends fade-form
        CMD1 (0xFF000040). Fade-mode is LED-only on this firmware — its bit4
        (haptic) is ignored — so any firmware blink-periodic haptic continues
        and an in-flight one-shot hwave plays out to completion.
        """
        self.buzz_hwave_stop()
        self._cancel_hwave_clear()
        self.fade(STOP_FADE_STEP, Colour.OFF)

    def stop_all(self) -> None:
        """Stop everything — cancels `buzz_hwave`, then CMD1=0 to kill firmware
        haptic, then a delayed fade-form hold (STOP_ALL_CHAIN_DELAY_S later)
        to re-establish the LED-off lock.

        Without the delay the firmware either dedupes the two CMD1s or latches
        its default green blink in the gap. The delay is short enough that any
        green flash is typically not perceived. Any new command issued during
        the gap cancels the pending fade-form (uses the same `_pending_stop`
        slot as `pulse`/`*_for` auto-stops), so calls like `solid(RED)`
        immediately after `stop_all()` work as expected.
        """
        self.buzz_hwave_stop()
        self._cancel_hwave_clear()
        self.cmd1(0)
        self._schedule_fade_hold(STOP_ALL_CHAIN_DELAY_S)

    def _schedule_fade_hold(self, delay_s: float) -> None:
        """Schedule a fade-form LED-off hold after `delay_s`. Reuses the
        `_pending_stop` slot so any subsequent command cancels it cleanly.
        Used by `stop_all` to re-engage hold after CMD1=0.
        """
        self._cancel_pending_stop()
        timer = threading.Timer(delay_s, self._fire_fade_hold)
        timer.daemon = True
        self._pending_stop = timer
        timer.start()

    def _fire_fade_hold(self) -> None:
        self._pending_stop = None
        self.fade(STOP_FADE_STEP, Colour.OFF)

    # Alias — existing callers (production sink, timed-effect auto-stops, REPL).
    def stop(self) -> None:
        """Alias for `stop_all()`."""
        self.stop_all()

    def solid(self, colour: Colour | str | int | None = None, buzz: Buzz = None) -> None:
        """Solid LEDs on. `buzz` adds periodic haptic — see `_resolve_buzz`."""
        ww = _leds_to_bits(colour)
        buzz_ms = _resolve_buzz(buzz)
        xx = (buzz_ms // 50) & 0xFF
        if buzz_ms > 0:
            ww |= _HAPTIC_BIT
        self.cmd1((xx << 8) | ww)

    def blink(
        self,
        period_ms: int,
        duty_ms: int,
        leds: Colour | str | int | None = None,
        buzz: Buzz = None,
    ) -> None:
        """Blink mode. duty_ms must be < period_ms or firmware may reject silently."""
        if duty_ms >= period_ms:
            raise ValueError(f"duty_ms ({duty_ms}) must be < period_ms ({period_ms})")
        zz = (period_ms // 10) & 0xFF
        yy = duty_ms & 0xFF
        buzz_ms = _resolve_buzz(buzz)
        xx = (buzz_ms // 50) & 0xFF
        ww = _leds_to_bits(leds)
        if buzz_ms > 0:
            ww |= _HAPTIC_BIT
        self.cmd1((zz << 24) | (yy << 16) | (xx << 8) | ww)

    def blink_fast(self, leds: Colour | str | int | None = None, buzz: Buzz = None) -> None:
        """Fast blink preset (period 100ms, duty 15ms)."""
        self.blink(BLINK_FAST_PERIOD_MS, BLINK_FAST_DUTY_MS, leds, buzz)

    def blink_medium(self, leds: Colour | str | int | None = None, buzz: Buzz = None) -> None:
        """Medium blink preset (period 500ms, duty 100ms)."""
        self.blink(BLINK_MEDIUM_PERIOD_MS, BLINK_MEDIUM_DUTY_MS, leds, buzz)

    def blink_slow(self, leds: Colour | str | int | None = None, buzz: Buzz = None) -> None:
        """Slow blink preset (period 2550ms, duty 255ms)."""
        self.blink(BLINK_SLOW_PERIOD_MS, BLINK_SLOW_DUTY_MS, leds, buzz)

    def fade(
        self,
        step: int,
        leds: Colour | str | int | None = None,
        buzz: Buzz = None,
    ) -> None:
        """Fade in/out. Lower step = slower fade, higher = faster cycle."""
        zz = step & 0xFF
        buzz_ms = _resolve_buzz(buzz)
        xx = (buzz_ms // 50) & 0xFF
        ww = _leds_to_bits(leds) | _FADE_BIT
        if buzz_ms > 0:
            ww |= _HAPTIC_BIT
        self.cmd1((zz << 24) | (xx << 8) | ww)

    def fade_slow(self, leds: Colour | str | int | None = None, buzz: Buzz = None) -> None:
        """Slow fade preset (step=FADE_SLOW_STEP)."""
        self.fade(FADE_SLOW_STEP, leds, buzz)

    def fade_medium(self, leds: Colour | str | int | None = None, buzz: Buzz = None) -> None:
        """Medium fade preset (step=FADE_MEDIUM_STEP)."""
        self.fade(FADE_MEDIUM_STEP, leds, buzz)

    def fade_fast(self, leds: Colour | str | int | None = None, buzz: Buzz = None) -> None:
        """Fast fade preset (step=FADE_FAST_STEP)."""
        self.fade(FADE_FAST_STEP, leds, buzz)

    def buzz(self, period_ms: int) -> None:
        """Haptic-only periodic vibrate. No LEDs. `period_ms` is XX*50ms granularity."""
        xx = (period_ms // 50) & 0xFF
        self.cmd1((xx << 8) | _HAPTIC_BIT)

    def buzz_fast(self) -> None:
        """Fast buzz preset (period BUZZ_FAST_PERIOD_MS)."""
        self.buzz(BUZZ_FAST_PERIOD_MS)

    def buzz_medium(self) -> None:
        """Medium buzz preset (period BUZZ_MEDIUM_PERIOD_MS)."""
        self.buzz(BUZZ_MEDIUM_PERIOD_MS)

    def buzz_slow(self) -> None:
        """Slow buzz preset (period BUZZ_SLOW_PERIOD_MS)."""
        self.buzz(BUZZ_SLOW_PERIOD_MS)

    def hwave(self, *waveforms: int) -> None:
        """One-shot haptic waveform trigger. 1-3 waveform IDs.

        Auto-inserts a fade-form breaker if the resulting CMD1 param would
        match the immediately prior one — the firmware silently ignores
        consecutive duplicate CMD1 values, so without this, repeating
        `hwave(N)` only fires the first time.
        """
        if not waveforms:
            raise ValueError("hwave requires at least one waveform id")
        if len(waveforms) > 3:
            raise ValueError("hwave supports up to 3 waveforms")
        z = waveforms[0] & 0xFF
        y = (waveforms[1] & 0xFF) if len(waveforms) > 1 else 0
        x = (waveforms[2] & 0xFF) if len(waveforms) > 2 else 0
        ww = _HWAVE_BIT | _HAPTIC_BIT
        param = (z << 24) | (y << 16) | (x << 8) | ww
        if param == self._last_cmd1_param:
            self._send_dedupe_breaker()
        self.cmd1(param)

    def _send_dedupe_breaker(self) -> None:
        """Send a fade-form CMD1 with an alternating step byte so the next
        CMD1 (typically a repeated hwave) isn't a consecutive duplicate.
        Alternation prevents back-to-back breakers from themselves deduping.
        """
        self._dedupe_breaker_alt = not self._dedupe_breaker_alt
        step = STOP_FADE_STEP if self._dedupe_breaker_alt else STOP_FADE_STEP - 1
        self.fade(step, Colour.OFF)

    def hwave_oneshot(
        self,
        *waveforms: int,
        clear_delay_s: float = DEFAULT_HWAVE_CLEAR_DELAY_S,
    ) -> None:
        """Fire `hwave(*waveforms)` then schedule a fade-form clear after
        `clear_delay_s` so the wand's "last CMD1" cache no longer holds the
        hwave value. The next `hwave_oneshot` call with the same waveform
        will fire reliably regardless of how much time has passed.

        Won't fire the clear if the user issues another command in the
        meantime — the deferred check sees `_last_cmd1_param` has moved on
        and bails, so user state (e.g. a `solid(RED)` issued between calls)
        is left undisturbed.

        Cancelled by `stop_led`, `stop_all`, `cancel_timed`. Each new
        `hwave_oneshot` cancels any prior pending clear.
        """
        self.hwave(*waveforms)
        target = self._last_cmd1_param
        self._cancel_hwave_clear()
        timer = threading.Timer(clear_delay_s, self._fire_hwave_clear, args=(target,))
        timer.daemon = True
        self._hwave_clear_timer = timer
        timer.start()

    def _cancel_hwave_clear(self) -> None:
        if self._hwave_clear_timer is not None:
            self._hwave_clear_timer.cancel()
            self._hwave_clear_timer = None

    def _fire_hwave_clear(self, expected_param: int | None) -> None:
        self._hwave_clear_timer = None
        # Only fire the clear if the hwave is still the wand's "last CMD1".
        # Otherwise the user has issued something else and we shouldn't
        # disturb whatever state they've set up.
        if self._last_cmd1_param != expected_param:
            return
        self._send_dedupe_breaker()

    def buzz_hwave(self, period: Buzz, *waveforms: int) -> None:
        """Periodic hwave — fires `hwave(*waveforms)` every `period`.

        `period` accepts the same forms as the `buzz=` kwarg:
            int (literal ms), 'fast'/'medium'/'slow' (preset), True (default).

        Cancels any prior `buzz_hwave` first. Cancelled by `buzz_hwave_stop`,
        `cancel_timed`, `stop`, `stop_led`, or `stop_all`.

        Caveat: each tick is a full-state CMD1 in hwave mode (WW=0x90, no LED
        bits) — concurrent LED state gets clobbered every cycle. Use the
        `buzz=` kwarg / `buzz_*` presets for combined LED+haptic; use
        `buzz_hwave` when you specifically need a chosen waveform repeated.
        """
        if not waveforms:
            raise ValueError("buzz_hwave requires at least one waveform id")
        period_ms = _resolve_buzz(period)
        if period_ms <= 0:
            raise ValueError(f"buzz_hwave period must be > 0; got {period_ms}")
        self.buzz_hwave_stop()
        self._buzz_hwave_gen += 1
        self._buzz_hwave_waveforms = waveforms
        self._buzz_hwave_period_s = period_ms / 1000.0
        self._fire_buzz_hwave(self._buzz_hwave_gen)

    def buzz_hwave_stop(self) -> None:
        """Cancel any running `buzz_hwave` timer. No-op if none active."""
        self._buzz_hwave_gen += 1  # invalidate any in-flight fire
        if self._buzz_hwave_timer is not None:
            self._buzz_hwave_timer.cancel()
            self._buzz_hwave_timer = None

    def _fire_buzz_hwave(self, gen: int) -> None:
        # Bail if a newer call (or a stop) has invalidated this generation.
        if gen != self._buzz_hwave_gen:
            return
        # `hwave` auto-inserts a dedupe-breaker when its param would match
        # the previous CMD1, so consecutive ticks fire reliably.
        self.hwave(*self._buzz_hwave_waveforms)
        timer = threading.Timer(self._buzz_hwave_period_s, self._fire_buzz_hwave, args=(gen,))
        timer.daemon = True
        self._buzz_hwave_timer = timer
        timer.start()

    def pulse(
        self,
        colour: Colour | str | int | None = None,
        duration_s: float = 1.0,
        buzz: Buzz = None,
    ) -> None:
        """Solid on for `duration_s`, then off. Cancels any prior timed effect."""
        self.solid(colour, buzz=buzz)
        self._schedule_stop(duration_s)

    def blink_for(
        self,
        duration_s: float,
        period_ms: int,
        duty_ms: int,
        leds: Colour | str | int | None = None,
        buzz: Buzz = None,
    ) -> None:
        """Blink for `duration_s`, then stop."""
        self.blink(period_ms, duty_ms, leds, buzz)
        self._schedule_stop(duration_s)

    def blink_fast_for(
        self,
        duration_s: float,
        leds: Colour | str | int | None = None,
        buzz: Buzz = None,
    ) -> None:
        self.blink_fast(leds, buzz)
        self._schedule_stop(duration_s)

    def blink_medium_for(
        self,
        duration_s: float,
        leds: Colour | str | int | None = None,
        buzz: Buzz = None,
    ) -> None:
        self.blink_medium(leds, buzz)
        self._schedule_stop(duration_s)

    def blink_slow_for(
        self,
        duration_s: float,
        leds: Colour | str | int | None = None,
        buzz: Buzz = None,
    ) -> None:
        self.blink_slow(leds, buzz)
        self._schedule_stop(duration_s)

    def fade_for(
        self,
        duration_s: float,
        step: int,
        leds: Colour | str | int | None = None,
        buzz: Buzz = None,
    ) -> None:
        self.fade(step, leds, buzz)
        self._schedule_stop(duration_s)

    def fade_slow_for(
        self,
        duration_s: float,
        leds: Colour | str | int | None = None,
        buzz: Buzz = None,
    ) -> None:
        self.fade_slow(leds, buzz)
        self._schedule_stop(duration_s)

    def fade_medium_for(
        self,
        duration_s: float,
        leds: Colour | str | int | None = None,
        buzz: Buzz = None,
    ) -> None:
        self.fade_medium(leds, buzz)
        self._schedule_stop(duration_s)

    def fade_fast_for(
        self,
        duration_s: float,
        leds: Colour | str | int | None = None,
        buzz: Buzz = None,
    ) -> None:
        self.fade_fast(leds, buzz)
        self._schedule_stop(duration_s)

    def cancel_timed(self) -> None:
        """Cancel any pending auto-stop (pulse/*_for), any `buzz_hwave`
        repeating timer, and any pending `hwave_oneshot` deferred clear.
        Sends no PEKIO command — just clears Python-side timers.
        """
        self._cancel_pending_stop()
        self.buzz_hwave_stop()
        self._cancel_hwave_clear()

    def raw(self, param: str | int) -> None:
        """Send arbitrary CMD1 param. Accepts int or hex string ('0xABCDEF12' or 'ABCDEF12')."""
        if isinstance(param, str):
            s = param.strip().lower().removeprefix("0x")
            val = int(s, 16)
        else:
            val = param
        self.cmd1(val)
