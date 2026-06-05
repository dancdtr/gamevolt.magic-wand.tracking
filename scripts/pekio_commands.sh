===== SOLIDS =====

solid(RED)
solid(GREEN)
solid(BLUE)
solid(WHITE)
solid(YELLOW)
solid(MAGENTA)
solid(CYAN)
solid(RGB)
solid(PINK)
solid(LIME)
solid(SKY)
solid(WARM_WHITE)
solid(PURPLE)
solid(ICE)
solid(ALL)

===== BLINK_FAST =====

blink_fast(RED)
blink_fast(GREEN)
blink_fast(BLUE)
blink_fast(WHITE)
blink_fast(YELLOW)
blink_fast(MAGENTA)
blink_fast(CYAN)
blink_fast(RGB)
blink_fast(PINK)
blink_fast(LIME)
blink_fast(SKY)
blink_fast(WARM_WHITE)
blink_fast(PURPLE)
blink_fast(ICE)
blink_fast(ALL)

===== BLINK_MEDIUM =====

blink_medium(RED)
blink_medium(GREEN)
blink_medium(BLUE)
blink_medium(WHITE)
blink_medium(YELLOW)
blink_medium(MAGENTA)
blink_medium(CYAN)
blink_medium(RGB)
blink_medium(PINK)
blink_medium(LIME)
blink_medium(SKY)
blink_medium(WARM_WHITE)
blink_medium(PURPLE)
blink_medium(ICE)
blink_medium(ALL)

===== BLINK_SLOW =====

blink_slow(RED)
blink_slow(GREEN)
blink_slow(BLUE)
blink_slow(WHITE)
blink_slow(YELLOW)
blink_slow(MAGENTA)
blink_slow(CYAN)
blink_slow(RGB)
blink_slow(PINK)
blink_slow(LIME)
blink_slow(SKY)
blink_slow(WARM_WHITE)
blink_slow(PURPLE)
blink_slow(ICE)
blink_slow(ALL)

===== FADE =====

fade(2, RED)
fade(1, GREEN)
fade(1, BLUE)
fade(1, WHITE)
fade(1, YELLOW)
fade(1, MAGENTA)
fade(1, CYAN)
fade(1, RGB)
fade(1, PINK)
fade(1, LIME)
fade(1, SKY)
fade(1, WARM_WHITE)
fade(1, PURPLE)
fade(1, ICE)
fade(1, ALL)

===== FADE_SLOW =====

fade_slow(RED)
fade_slow(GREEN)
fade_slow(BLUE)
fade_slow(WHITE)
fade_slow(YELLOW)
fade_slow(MAGENTA)
fade_slow(CYAN)
fade_slow(RGB)
fade_slow(PINK)
fade_slow(LIME)
fade_slow(SKY)
fade_slow(WARM_WHITE)
fade_slow(PURPLE)
fade_slow(ICE)
fade_slow(ALL)

===== FADE_MEDIUM =====

fade_medium(RED)
fade_medium(GREEN)
fade_medium(BLUE)
fade_medium(WHITE)
fade_medium(YELLOW)
fade_medium(MAGENTA)
fade_medium(CYAN)
fade_medium(RGB)
fade_medium(PINK)
fade_medium(LIME)
fade_medium(SKY)
fade_medium(WARM_WHITE)
fade_medium(PURPLE)
fade_medium(ICE)
fade_medium(ALL)

===== FADE_FAST =====

fade_fast(RED)
fade_fast(GREEN)
fade_fast(BLUE)
fade_fast(WHITE)
fade_fast(YELLOW)
fade_fast(MAGENTA)
fade_fast(CYAN)
fade_fast(RGB)
fade_fast(PINK)
fade_fast(LIME)
fade_fast(SKY)
fade_fast(WARM_WHITE)
fade_fast(PURPLE)
fade_fast(ICE)
fade_fast(ALL)

===== STOP / OFF =====

# LED off (held), haptic untouched. Fade-form alone (0xFF000040).
stop_led()

# Stop everything — CMD1=0 (kills haptic), then a fade-form re-hold ~50ms
# later (the gap stops the firmware deduping/latching). Any command issued
# in the gap cancels the pending fade-form.
stop_all()

# Alias for stop_all.
stop()

# Cancels a pending auto-stop from a pulse/*_for call. Doesn't send anything.
cancel_timed()

===== CUSTOM BLINK / FADE =====

# Custom timings. duty_ms must be < period_ms.
blink(2000, 100, BLUE)              # 100ms on / 1900ms off — sparse heartbeat
blink(500, 250, GREEN)              # 50% duty square wave
blink(1000, 900, RED)               # almost solid with brief gap

# Custom fade step: lower = slower triangle wave, higher = faster cycle.
fade(1, RED)                        # slowest fade
fade(10, GREEN)                     # medium-slow
fade(50, BLUE)                      # fast cycle
fade(OFF)
===== COMBINE COLOURS ON THE FLY =====

# Any Color | Color works — make your own combos without naming them.
solid(RED | BLUE)                   # magenta-ish
solid(RED | GREEN | WHITE)          # warm tint
blink_fast(GREEN | WHITE)           # lime fast-blink

===== HAPTICS =====

# One-shot vibrations via hwave (1-3 waveform IDs). Doesn't change LED state.
hwave(16)                           # single waveform
hwave(82, 70)                       # chain two
hwave(93, 14, 56)                   # chain three (the spell-cast cue)

# Periodic vibration alongside any LED command — pass `buzz=` kwarg.
# Accepts: 'fast'/'medium'/'slow' (preset), int (literal period_ms), True (default), None.
solid(RED, buzz='fast')
solid(RED, buzz=True)               # default period (BUZZ_MEDIUM)
solid(RED, buzz=400)                # custom period in ms
blink_fast(BLUE, buzz='slow')
fade_slow(GREEN, buzz='medium')

# Haptic-only periodic vibration (no LED).
buzz_fast()
buzz_medium()
buzz_slow()
buzz(400)                           # custom period

# Periodic hwave — pick a specific waveform and repeat it at an interval.
# Python-side timer (not firmware periodic), so each tick is a full hwave
# CMD1 (WW=0x90, no LED bits). Concurrent LED state gets clobbered every cycle.
# Minimum effective period is bounded by waveform playback duration — too-fast
# triggers arriving mid-wave get dropped by the haptic driver.
buzz_hwave('fast', 16)              # waveform 16 every BUZZ_FAST_PERIOD_MS
buzz_hwave('slow', 93, 14, 56)      # multi-waveform chain every BUZZ_SLOW_PERIOD_MS
buzz_hwave(300, 82)                 # custom period 300ms, waveform 82
buzz_hwave_stop()                   # cancel the repeating timer
# Also cancelled by: stop(), stop_led(), stop_all(), cancel_timed()

# Named patterns — tuples of waveform IDs. Unpack with `*` when calling.
# Defined at top of pekio_client.py; rename/edit there as you find good ones.
hwave(*BUZZ_PATTERN_1)              # one-shot spell-cast cue (93, 14, 56)
hwave(*BUZZ_PATTERN_2)              # single short tap (1)
buzz_hwave('slow', *BUZZ_PATTERN_1) # repeating spell-cast cue
buzz_hwave(200, *BUZZ_PATTERN_2)    # rapid tap, repeats reliably (short waveform)

# Re-playable one-shot — fires hwave then schedules a fade-form clear ~500ms
# later so the wand's "last CMD1" cache no longer holds the hwave value.
# Without this, calling hwave(*BUZZ_PATTERN_2) twice (even minutes apart)
# only fires the first time because of firmware consecutive-CMD1 dedupe.
hwave_oneshot(*BUZZ_PATTERN_1)      # plays now + auto-clears, ready to call again
hwave_oneshot(16)
hwave_oneshot(*BUZZ_PATTERN_2, clear_delay_s=1.0)   # custom clear delay
# The clear is skipped if you issue another command before it fires, so you
# can interleave with LED commands without state being clobbered.

===== TIMED (auto-stops after duration_s) =====

# Solid for N seconds then off.
pulse(BLUE, 2.0)
pulse(RED, 1.5, buzz='fast')

# Blink for N seconds then off.
blink_for(2.0, 500, 100, BLUE)      # custom timing
blink_fast_for(2.0, BLUE)
blink_medium_for(3.0, GREEN, buzz='slow')
blink_slow_for(5.0, RED)

# Fade for N seconds then off.
fade_for(3.0, 5, MAGENTA)           # custom step
fade_slow_for(3.0, GREEN)
fade_medium_for(3.0, MAGENTA)
fade_fast_for(2.0, WHITE)

===== RAW / LOW-LEVEL CMD1 =====

# Arbitrary 32-bit CMD1 param. Useful for one-off doc patterns.
raw('0x0A0F0002')                   # doc-verified "fast blinking green"
raw('0xFFFF0001')                   # doc-verified "slow blinking red"
raw('0x10000090')                   # doc-verified hwave waveform 16
cmd1(0x0A0F0002)                    # same as raw(), takes int

===== CMD0 PRESETS =====

# Built-in "scene" presets — flicker off again because firmware default reasserts
# (no fade-hold trick available for presets). Useful for sanity-check.
cmd0(1)                             # leds off, haptic off
cmd0(2)                             # red 25%
cmd0(3)                             # green 25%
cmd0(4)                             # blue 25%
cmd0(5)                             # white 25%
cmd0(6)                             # red + green 25%
cmd0(7)                             # red + blue 25%
cmd0(8)                             # green + blue 25%

===== ANCHOR STREAM SUBSCRIPTION =====

spqf('R')                           # subscribe to RR (ranging) — quiets the PR firehose
spqf('P')                           # subscribe back to PR (IMU samples)

===== TARGET TAG =====

# Default target tag is set on console startup (--tag flag, default 0x1DAE).
# Switch mid-session for multi-wand testing.
tag('0x1DAE')
tag('0x1DC6')