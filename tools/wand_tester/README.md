# Conductr v3 Wand Tester

Sends wand LED and haptics commands via serial using a single eliko anchor.

## Run

```bash
uv run python tools/wand_tester/main.py
uv run python tools/wand_tester/main.py --port /dev/tty.usbmodem2101 --quiet
```

Flags: `--port`, `--baud`, `--tag` (initial wand ID), `--quiet` (suppress the PR firehose with `SPQF,R`).

## Application Window

+ Select the target `wandId` from the dropdown in top left
+ `Stop All` button stops all LED and haptic sequences
+ `Send` button sends selected command to target wand

1. **LED Screen** — colour grid + Solid / Blink / Fade / Timed sections. The orange "Stop LED" button in the bottom right keeps any firmware-driven haptic running.

2. **Haptic Screen** — three modes:
  - **One-shot** — fire selected waveforms once
  - **Sequence** — repeating loop of the waveforms at the slider period
  - **Alarm** — firmware-default periodic vibration at the slider period (_custom haptics interfer with the LED in this current wand firmware_)

3. **LED + Haptic** — firmware-clean LED and haptics combo (LED and haptics options are limited here)

## Editing defaults

Most knobs live in [`constants.py`](constants.py):

| Constant | What it controls |
|---|---|
| `WAND_TAGS` | List of wand IDs shown in the dropdown. |
| `COLOR_OPTIONS` | Order + swatch colours of the 4×4 colour grid. |
| `DEFAULT_COLOR` | Initially-selected colour (must match a `name` in `COLOR_OPTIONS`). |
| `DEFAULT_BLINK_PERIOD_MS`, `DEFAULT_BLINK_DUTY_MS` | Initial values in the custom-blink spinboxes. |
| `DEFAULT_FADE_STEP` | Initial value in the custom-fade spinbox. |
| `DEFAULT_BLINK_FOR_DURATION_S`, `DEFAULT_FADE_FOR_DURATION_S` | Initial durations in the LED tab's Timed section. |
| `HAPTIC_PATTERNS` | Preset waveform tuples shown as quick-fill buttons on the Haptic tab. |
| `PERIOD_MIN_MS`, `PERIOD_MAX_MS`, `PERIOD_STEP_MS` | Bounds + step for the haptic period sliders. |
| `DEFAULT_PERIOD_MS` | Initial slider value. |
| `DEFAULT_PORT`, `DEFAULT_BAUD` | argparse defaults. |

Button styling (colours, borders, hover, selected-state outlines) lives in [`styles.py`](styles.py).

## File layout

All under `tools/wand_tester/`:

- `main.py` — entry script (sys.path tweaks + calls into `app.main`).
- `app.py` — argparse, serial open, reader thread, QApplication.
- `main_window.py` — top-level window, tag dropdown, Stop All, close handler.
- `led_tab.py`, `haptic_tab.py`, `led_haptic_tab.py` — the three tabs.
- `widgets.py` — reusable `ColorPicker`, `PeriodSlider`, command-button builders.
- `constants.py`, `styles.py` — as above.
