# Conductr v3 Wand Tester

Sends wand LED and haptics commands via serial using a single eliko anchor.

## Run

```bash
uv run python tools/wand_tester/main.py
uv run python tools/wand_tester/main.py --port /dev/tty.usbmodem2101 --quiet
```

### Raspberry Pi

Anchor enumerates as `/dev/ttyACM0`. Use the stable `by-id` symlink so it survives reboots / USB reorder. Add `--dark` because LXDE has no system dark mode.

```bash
uv run python tools/wand_tester/main.py \
  --port /dev/serial/by-id/usb-Eliko_LLC_Kio_Anchor_COM_Port-if00 \
  --dark
```

Find the device path:

```bash
ls -l /dev/serial/by-id/
```

Flags: `--port`, `--baud`, `--tag` (initial wand ID), `--quiet` (suppress the PR firehose with `SPQF,R`), `--dark` (force Fusion dark palette).

## Application Window

+ Select the target `wandId` from the dropdown in top left
+ `Stop` button stops all LED and haptic sequences
+ `Send` button sends selected command to target wand

1. **LED Screen** — colour grid + Solid / Blink / Fade sections. Blink and Fade each have a **Loop** checkbox: checked = runs continuously until stopped; unchecked = runs for the section's **Duration** then auto-stops (the Duration field greys out while Loop is on).

2. **Haptic Screen** — pick an effect (fills the waveform spinboxes) and Send. A **Loop** checkbox mirrors the LED tab: unchecked fires the waveforms once; checked repeats them at the **Repeat every** interval (the interval slider shows only while Loop is on).

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
| `BLINK_PRESETS`, `FADE_PRESETS` | The five Slowest→Fastest speed levels (label + timings) for the blink/fade preset rows. Blink period is firmware-capped at 2550ms, so "Slowest" sits at that ceiling. |
| `HAPTIC_EFFECTS` | Named haptic effects (wand-themed label → waveform tuple) shown as quick-fill buttons on the Haptic tab. First group verified on-wand; rest exploratory DRV2605 ids. |
| `PERIOD_MIN_MS`, `PERIOD_MAX_MS`, `PERIOD_STEP_MS` | Bounds + step for the haptic period sliders. |
| `DEFAULT_PERIOD_MS` | Initial slider value. |
| `DEFAULT_PORT`, `DEFAULT_BAUD` | argparse defaults (macOS port). Override per-host via `--port`. |

Button styling (colours, borders, hover, selected-state outlines) lives in [`styles.py`](styles.py).

## File layout

All under `tools/wand_tester/`:

- `main.py` — entry script (sys.path tweaks + calls into `app.main`).
- `app.py` — argparse, serial open, reader thread, QApplication.
- `main_window.py` — top-level window, tag dropdown, Stop, close handler.
- `led_tab.py`, `haptic_tab.py` — the two tabs.
- `widgets.py` — reusable `ColorPicker`, `PeriodSlider`, command-button builders.
- `constants.py`, `styles.py` — as above.
