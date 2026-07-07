# Magic Wand Tracking — System Specification

**Status:** living document. High-level architecture as of 2026-06-09.
**Audience:** project owner (future-self), reference when context fades.

---

## 1. Purpose

This repo hosts the runtime that turns UWB-tracked magic wands into in-venue spell-cast experiences. It ingests sensor data, decides where wands are and what they're doing, and pushes results to downstream systems (show effects, metrics, player profiles) via a central hub.

Two themes drive the architecture:

- **Decouple data plane from control plane.** Sensor firehose flows peer-to-peer from edge sources into recognition. The hub is reserved for control: profile lookups, presence and spell-cast events, configuration. Routing the firehose through the hub would create a single point of failure and a god-object bottleneck.
- **Protocol-shaped seams.** Every cross-boundary interaction sits behind a `Protocol`. Today most implementations are in-process or use legacy transports. Tomorrow they swap to Eliko RTLS, HTTP-to-hub, MQTT, etc. The code consuming them does not change.

---

## 2. System overview

```
                ┌───────────────────────────┐
                │  Eliko RTLS (production)  │
                │  - wand position stream   │
                │  - wand IMU stream        │
                │  - wand command channel   │
                └─────────────┬─────────────┘
                              ▼
                  ┌──────────────────────┐
                  │     wands_app        │
                  │  ┌────────────────┐  │
                  │  │  TrackingApp   │  │       ┌────────┐
                  │  │  (where)       │──┼──────▶│  Hub   │──▶ show system
                  │  └────────────────┘  │       │        │──▶ cloud / metrics
                  │  ┌────────────────┐  │       └────────┘
                  │  │ RecognitionApp │──┼──────▶ (HTTP sync + MQTT events)
                  │  │  (what)        │  │
                  │  └────────────────┘  │
                  └──────────────────────┘
```

Three planes:

- **Data plane (inbound):** position + IMU streams from the sensor source.
- **Data plane (outbound):** wand command channel (LED feedback, activation, TX-frequency). Haptic cues disabled — see [§4.5](#45-haptic-disabled).
- **Control plane:** sync lookups and async events to/from the hub.

---

## 3. Deployable units

| Unit | Status | Role |
|------|--------|------|
| `wands_app/` | active | Main runtime. Hosts `TrackingApp` + `RecognitionApp` in one process. |
| Eliko RTLS | external (planned) | Production sensor source. Provides position stream, IMU stream, and wand-command channel. |
| Hub | external (planned) | Single venue-local instance. Source of truth for profiles, zone-spell bindings, scoring. Republishes events upstream and to show system. Always-on; if it's down, the experience is down. |
| Show system | external | Lights, sound, effects. In production, fed by the hub. In development, fed directly via UDP from `ShowSystemController`, which routes each cast to the destinations (configured under `show_system_controller.destinations`) that subscribe to the spell. Set `enabled: false` to build a `NoOpShowSystem`. Spells listed under no destination warn when they fire. |
| Cloud | external | Out of scope for this app. Hub's concern. |

---

## 4. Data plane protocols

Three protocols cover all sensor I/O. Each is implementation-agnostic; multiple implementations can coexist and production may share a transport beneath them.

### 4.1 `WandImuStream` (inbound)

Emits per-wand IMU samples (rotation, timing). Two implementations live in tree; selection is driven by the `system_type` flag in `appsettings.yml` (see §9.2), and each value also pins the deployment shape (production vs mock):

- `ElikoWandImuStream` — consumes lines from a shared `ElikoClient` (TCP to Eliko RTLS Server, default port 25025) filtered to `PR_Q` (per-tag quaternion bursts), and emits one `AssembledPacket` per line (10 samples each). The wand's body-frame forward axis is +Y; each sample's forward vector is `q · (0,1,0)`, Q15-encoded into the existing `data_str` format so `WandClient` consumes both sources identically. Tag IDs are normalised to bare upper hex (e.g. `0x001D6C` → `001D6C`). Per-sample dt is fixed by IMU hardware and configured (not derived from packet timestamps). Used by `system_type: eliko_rtls` (= production).
- `ElikoSingleAnchorWandImuStream` — consumes raw `PR` lines from an `ElikoSingleAnchorClient` (USB-serial to a single anchor, no RTLS server). Each PR sample is a 6-byte SFLP word packing three IEEE-754 half-floats `(x, y, z)` of a unit quaternion; `w` is recovered as `sqrt(1 − x² − y² − z²)` per the STM `sflp2q` algorithm. Forward Q15 encoding (via the shared `quat_forward_encoder`) and `AssembledPacket` shape are identical to the RTLS path. On `start_async`, the client sends `$PEKIO,DC,001,CMD0,0x<TAG>,0x0000<CC>03` per tracked tag (enable IMU) + `$PEKIO,DC,001,SPQF,P` (subscribe to PR). `<CC>` is the UWB Tx/Rx preamble code (`imu_stream.eliko_single_anchor.tx_rx_code`, range 9-12, default 9), which must match the anchor's `SETC`-configured code; it occupies the CMD0 `XX` byte (`WW=0x03` = PR data type). Because the SFLP encoding drops `w`, its recovery is ill-conditioned near `w ≈ 0` (wand ~180° from its IMU-init attitude): half-float quantisation bounces the recovered `w` by ~0.03–0.05 per sample, swinging the forward vector several degrees (visible trail jitter). A per-tag `SflpQuatStabiliser` corrects this at decode time — hemisphere-aligns consecutive quats, EMA-smooths the sign-continuous `w`, and blends the correction in only inside the ill-conditioned zone (passthrough elsewhere, so no added latency at normal orientations). Used by `system_type: eliko_single_anchor` (= mock / dev environment).

Both Eliko streams inherit from `ElikoWandImuStreamBase` (`wand/streaming/eliko/`), which owns client lifecycle, prefix-based line filtering, forward-vector Q15 encoding, and `AssembledPacket` assembly. Subclasses declare line prefix, sample-field offset, header layout, and per-sample quat decode (PR_Q text vs PR SFLP word). New Eliko-format sources (mock, alternate hardware) add a subclass + a line source; they do not re-implement the parsing.

The inbound line seam is the `WandLineSource` protocol (`wand/streaming/wand_line_source.py`): `line_received` event + `start_async`/`stop_async`. Both Eliko clients satisfy it structurally. The outbound command seam for the Eliko family is the parallel `ElikoCommandClient` protocol (`send_command`). The IMU stream consumes the line source, `ElikoWandCommandSink` the command client, so per-deployment one client object serves both directions. Each stream owns its client's lifecycle (`start_async` on the client when the stream starts).

Eliko's `COORD_Z` position feed is intentionally not consumed here; position will land via the planned `WandPositionStream` (§4.2). Future mock implementations (e.g. mouse-driven, stub at `wand/streaming/mouse/`) are anticipated but out of spec.

### 4.2 `WandPositionStream` (inbound, new)

Emits per-wand position updates. Does not exist today — production zone enter/exit arrives via UDP `ZoneEnteredMessage` / `ZoneExitedMessage` from an external positioning service. Once `WandPositionStream` is in place, the `ZoneManager` derives zone enter/exit from raw position + polygon configuration, and the UDP zone-event ingress retires.

#### Zone presence surface

`ZoneManagerProtocol` is the single seam between presence input (UDP today, position stream tomorrow) and consumers (`TrackedWandManager`, `WandSessionCoordinator`, and optionally `ZonePresentationController` in mock):

```python
class ZoneManagerProtocol(ABC):
    @property
    def wand_entered_zone(self) -> Event[Callable[[str, str], None]]: ...  # (wand_id, zone_id)
    @property
    def wand_exited_zone(self) -> Event[Callable[[str, str], None]]: ...   # (wand_id, zone_id)
    async def start_async(self) -> None: ...
    async def stop_async(self) -> None: ...
    def get_zone(self, zone_id: str) -> Zone: ...                # spell_types lookup
    def zones_containing_wand(self, wand_id: str) -> list[str]:  # routing lookup
```

Events carry ids only — no `Zone` object in the payload. Consumers that need zone metadata call `get_zone(id)` when they need it. `zones_containing_wand` returns a list so a wand can sit in overlapping zones (production may; mock won't).

Two implementations:

- `ActiveWandZoneManager` (production, used by `eliko_rtls`) — `wand_entered_zone` / `wand_exited_zone` are driven by a single UDP `ActiveWandChanged` event from the RTLS system (`{wand_id, state, zone_id, zone_name, txrx}`, port 5006 / `zones.udp_receiver`). The RTLS system decides which wand is the active caster in a zone; `state` carries enter (`ACTIVE`) vs exit (`INACTIVE`), keyed on `zone_id`. Incoming `wand_id` arrives `0x`-prefixed and is normalised to bare upper hex to match internal ids. Shared zone bookkeeping (zones map, dedup via `Zone.wand_ids`, enter/exit events) lives in `ZoneManagerBase`.
- `ZoneManager` (generic UDP, not currently wired) — same base, driven by the older `ZoneEnteredMessage` / `ZoneExitedMessage` enter/exit pair. Retained for an alternate positioning source; superseded on the RTLS path by `ActiveWandChanged`.
- `MockZoneManager` (mock, used by `eliko_single_anchor`) — loads the same `ZonesSettings.zones` list as production. Exposes `set_current_zone(zone_id | None)`; calling it swaps every tracked wand out of the prior zone and into the new one in one shot, firing the events in order. Zone selection happens inside the unified Qt window via `QtZoneControls`, fed by two window event streams: `key_pressed` (Up/Down cycles, digit keys 0-9 plus a short multi-digit window address `ZoneSettings.key`) and `zone_selected` (a top-bar dropdown whose options read `Z001 - SPELL1, SPELL2`). All three input paths route through `set_current_zone`; the dropdown stays in sync because `show_zone` (driven by the manager's enter/exit events) sets the combo index regardless of which input caused the change. No synthetic on-the-fly zones.

`ZoneApplication` bundles the manager with **optional** dev-only UI: `ZonePresentationController` (binds manager enter/exit events to `ZoneVisualiserProtocol.show_zone`) + zone controls. In mock the visualiser is the **shared unified Qt window** (the same object that is the wand visualiser — see §7.2), so spell targets, the wand trail, and the cast snapshot all live in one window. Production (`eliko_rtls`) passes both as `None` — no window in staging/prod; downstream consumers (lamps, show system, wand LEDs) convey state.

`ZoneSettings.zones` is the single source of truth for what spells exist in the system. Each zone declares `id`, `key` (int shortcut), and a `spells` list; an "all spells" dev config is a one-zone-per-spell list.

### 4.3 `WandCommandSink` (outbound)

Accepts internal `Message`s targeted at a specific wand:

- **Activation / deactivation** — flips wand transmit state. Activation begins the IMU stream for that wand; deactivation ends it. Replaces the older "connect/disconnect" lifecycle. TX state is held on the wand and does not survive a radio drop / power cycle / OTA stall. `TrackedWandManager._on_wand_connected` re-activates a reconnecting wand if `ZoneManager.zones_containing_wand` is non-empty and resets the wand's forward interpreter so the integration restarts from the current orientation. In the Eliko binding, activation maps to `WandCommandSink.enter_idle(wand_id)` — there is no separate TX-enable command on the wire today.
- **LED feedback** — typed methods on `WandCommandSink`: `enter_idle(wand_id)` (steady fade in the configured idle colour), `exit_idle(wand_id)` (LED off), and `pulse(wand_id, colour, period_ms, duty_ms, duration_s)` for time-bounded blink cues (e.g. spell-cast). The sink owns the per-wand idle state and restores it when a pulse ends, so a zone-exit during a pulse correctly leaves the LED off rather than fading back on.
- **Haptics / vibration**, lamp colour, IMU transmit-frequency changes, etc.

Surface:

```python
class WandCommandSink(Protocol):
    def send_to_wand(self, wand_id: str, message: Message) -> None: ...
    def broadcast_to_wand(self, wand_id: str, message: Message) -> None: ...
```

Implementations in tree:

- `NullWandCommandSink` (used by `eliko_rtls`) — no-op. On the RTLS path the RTLS system owns wand IMU + LED/command state, so the app stays read-only on the wand and issues no commands. `WandDeviceController` is still constructed against it; the calls simply no-op.
- `ElikoWandCommandSink` (Eliko single-anchor; also valid for RTLS if the app ever drives the wand) — transport-agnostic; targets the `ElikoCommandClient` protocol so it can sit on either `ElikoClient` (TCP) or `ElikoSingleAnchorClient` (serial). Delegates PEKIO command building to `PekioClient`. `enter_idle(wand_id)` → `client.fade_slow(idle_colour)` and flags the wand idle so a subsequent pulse can restore the fade. `exit_idle(wand_id)` → `client.stop_led()` (fade-mode hold off) and cancels any pending pulse restore. `pulse(wand_id, colour, period_ms, duty_ms, duration_s)` → `client.blink(period_ms, duty_ms, colour)`, with an asyncio-loop-scheduled restore at `duration_s`: re-fade idle if still flagged, else `stop_led`. Pulse restore is scheduled on the asyncio loop (not `threading.Timer`) because the transports route sends through `asyncio.create_task`, which silently raises in a non-loop thread. Haptic is intentionally not on the sink surface — see [§4.5](#45-haptic-disabled). The `SET_TAG_LEDH` and `HWAVE,ON,...` convenience headers are RTLS-server sugar — single-anchor firmware only honours the raw `$PEKIO,DC,<seq>,CMD<n>,...` form. Firmware quirk: a plain `CMD1=0` does **not** hold the LED off — the firmware re-asserts a default green-blink indicator on top of it. `PekioClient.stop_led()` uses fade-mode (`0xFF000040`, step=255, no LED bits) instead, which holds the state machine and suppresses the default. Verified 2026-06-03.

`WandDeviceController` depends on `WandCommandSink` (protocol), not on a specific implementation.

### 4.4 Notes

- Position and IMU stay as separate protocols even where production shares transport. Operator tools may want one without the other (e.g. a "show me where every wand is" viewer).
- `WandCommandSink` stays separate from the inbound streams. Decoupling input from output keeps mock/debug implementations simple and avoids cross-coupling unrelated transports.

### 4.5 Haptic disabled

Haptic cues are not sent on the current wand hardware. Reproduced 2026-06-10: any `CMD1` with the haptic bit set (`WW` bit 4) — whether HWAVE one-shot or periodic-buzz — reboots the wand when concurrent UWB activity (PR streaming or 10 Hz ranging) is in flight. Confirmed externally with a reset-pin probe: rail sags below the brown-out threshold during motor inrush. Root cause is hardware (battery internal resistance + motor current draw + UWB TX coincidence); the firmware vendor has no software fix. Mitigations planned outside the app — proper battery housing, decoupling cap on the motor rail, or 2× AAAA in series for headroom.

App-side surface follows: `WandDeviceController.play_spell_cast_cue` calls `WandCommandSink.pulse` only; there is no haptic method on the sink. The old `WandHapticMessage` / `WandHapticSequenceMessage` / `WandTxMessage` types and the `AnchorCommandBridge` that consumed them were dropped — the in-process call path is enough for everything we feed the wand today, so internal cues no longer travel via the `Message` envelope.

Reboots still happen in the wild (battery wiggle, OTA stall, anything that drops the rail below the reset threshold), so the app self-heals. `WandRebootDetector` subscribes to the anchor's line stream alongside the IMU parser, watches for `$PEKIO,PP,<seq>,0x<tag>,VERS,<value>` — the 5×-repeated boot banner — and fires `wand_rebooted(tag)` once per reboot (per-tag 2s dedup window). The single-anchor binding wires that event to `ElikoSingleAnchorClient.enable_imu(tag)`, which re-issues the per-tag `CMD0` IMU-enable (with the configured `tx_rx_code` preamble) to restart IMU sampling — but **only for tags in `tracked_wand_ids`**; reboots of untracked wands (e.g. ones another system commands) are ignored so the two systems don't fight over IMU state. The wand resumes PR within a tick, the registry's next `get_or_create` minted a new `WandClient` whose `wand_connected` event drives `TrackedWandManager._on_wand_connected` — which resets the wand's forward interpreter and re-activates the LED idle state if it's still in a zone. No human intervention; recovery is <1s. Detector lifecycle is owned by `TrackingApp.start_async` / `stop_async`. RTLS path doesn't wire a detector yet — the RTLS server is presumed to manage per-tag IMU state itself.

All of the above is gated by `imu_stream.eliko_single_anchor.manage_imu` (default `True`). Set it `False` and the app issues **no** IMU-enable traffic at all — no init `CMD0`s, and the reboot detector is not wired (the client only subscribes + listens). Use this for the hybrid setup where the RTLS network owns wand IMU state (e.g. a wand is forced IMU-on by sitting inside an Eliko zone), so the single-anchor app and the RTLS system stop conflicting over enable/disable.

### 4.6 Battery telemetry (single-anchor)

Battery brown-out is the dominant wand failure mode (see [§4.5](#45-haptic-disabled) and the 2026-07-06 reboot-loop incident), so the single-anchor path can poll wand battery voltage. `WandBatteryMonitor` (gated by `imu_stream.eliko_single_anchor.battery_monitor.enabled`, default `False`; independent of `manage_imu`) sends `ElikoSingleAnchorClient.poll_battery(tag)` — `$PEKIO,DC,<seq>,GDHR,0x<tag>,timeout_ms=<n>` — per tracked tag every `poll_interval_s` (default 60s), plus an immediate `poll_wand` on every `WandServer.wand_connected` so reboots/battery swaps produce a fresh reading at once. Each poll is an anchor OTA command (one `STORED` ack + one delivery notice per poll). The voltage comes back in millivolts in either of two shapes, both parsed: `$PEKIO,AC,123,0x<tag>,GDHR,voltages,0x<mv>,OTA` (poll response; `123` is a hardcoded OTA-response sequence — Eliko protocol limitation) or `$PEKIO,PP,<seq>,0x<tag>,GDHR,0x<mv>` (the tag's unsolicited GDHR/VERS/GLEC report set). The monitor fires `battery_updated(tag, millivolts, percent)`; percent is a rough linear map between `empty_millivolts`/`full_millivolts` (defaults 1100/1550 for the AAAA alkaline cell) — a dying-cell alarm, not a fuel gauge. The builder routes the event to the visualiser's `set_wand_battery` no-op-default hook; the Qt single-wand view shows a colour-coded readout in the window status bar (updates are stashed and applied on the Qt thread in `update()`, since the event fires on the serial receive thread). The builder also subscribes `WandBatteryLog.record`, which appends each reading to a daily CSV (`battery_YYYYMMDD.csv`, columns timestamp/tag/millivolts/percent) under `battery_monitor.log_directory` (default `./diagnostics/battery`, git-ignored) for plotting discharge over time. Monitor lifecycle is owned by `TrackingApp.start_async` / `stop_async`. RTLS path: not wired — the RTLS server exposes `GET_BATTERIES` (mV + percent, pushed ~15 min) for when that binding needs it.

---

## 5. Control plane protocols

Recognition and tracking depend on per-service protocols. No `HubClient` facade exists in code — "hub" is the name of the deployment pattern where a set of implementations happen to route over HTTP/MQTT to the real hub. In development, the same protocols are satisfied by local implementations.

### 5.1 Sync lookups (would be HTTP in production)

| Protocol | Purpose | Today |
|----------|---------|-------|
| `ProfileService` | wand_id → wizard profile | `LocalProfileService` |
| `ZoneSpellBindingService` *(planned)* | which spell(s) are active in a given zone | not yet — spells are bound in `ZoneFactory` configuration |

The spell **library** (definitions of each spell) stays local in `spells/`. The hub only owns which spell is active where.

`ProfileService.get_profile(wand_id)` is the future single hub call that feeds the scorer: it
should return wizard name, **XP bonus** (lifelong unique-spell count), **accessibility / kids
settings** (threshold-scale + gate relaxation — see §6.2), and house. Today `Profile` carries
only name; XP/streak live in the in-process scorer stubs and the scorer's accessibility levers
are unbuilt. When the hub call lands, those move behind this protocol.

### 5.2 Async events (would be MQTT in production)

| Protocol | Purpose | Today |
|----------|---------|-------|
| `WandPresenceReporter` | wand enter/exit per zone (nested: outer area + inner hotspot) | `LocalWandPresenceReporter` |
| `SpellCastReporter` | per-attempt: full candidate list (top-N spells + raw accuracy scores) | `LocalSpellCastReporter` |
| `ShowSystemReporter` | graded show-response trigger | folded into `LocalSpellCastReporter` + `ShowSystemController` today; to be split |

Both async reporters support composite fan-out — multiple implementations can be active at once (e.g. UDP + file logger + MQTT-to-hub).

### 5.3 Inbound from hub

Out of scope for v1. No admin commands, no game-state pushes, no wand activation from cloud. Hot configuration reload is on the long-term roadmap.

### 5.4 Failure semantics

Hub down ⇒ experience down. The app makes no attempt to degrade gracefully — there is nothing meaningful to do with wands if the show and profile systems can't be reached. Log and idle.

---

## 6. Spell matching and reporting

Recognition turns wand motion into a recognised spell + quality. The legacy step-group
matcher (`SpellMatcher` / `SpellDefinition` / 8-way `DirectionQuantizer` / `SegmentBuilder`)
was **removed** and replaced by a **$1 unistroke recogniser** plus a decoupled scorer.

### 6.1 The $1 pipeline

1. **Point path.** The forward interpreter's per-sample `(x_delta, y_delta)` are integrated
   into a 2D path (the same stream the trail renders). A stream discontinuity — sample
   timestamps jumping past `max_sample_gap_ms` (dropped packets) or backwards (wand reboot
   rewinding the tick clock) — restarts delta tracking instead of integrating the orientation
   jump into one giant delta, so outages no longer draw straight-line artefacts.
2. **Windowing** (`motion/stroke/StrokeWindower`, config `input.wand.stroke_window`). A stroke
   opens on `MOVING` and closes on a *sustained* still phase (`HOLDING` / `STOPPED`). A transient
   `PAUSED` (corner / mid-spell hesitation) is left to ride, so a multi-segment glyph arrives as
   one stroke — but it also emits a **provisional snapshot** (`stroke_paused`) of the still-open
   stroke for the cast assembler (2a). The phase tiers (`min_paused_duration` <
   `min_holding_duration`) encode transient-vs-deliberate. An open stroke is capped to its
   trailing `max_open_duration_s` so a wand that wanders without settling can't grow it unbounded.
2a. **Cast assembly** (`wand/CastAssembler`, config `input.wand.cast_assembly`). The phase
   tracker can't tell a *long corner pause* from *end of spell* at the moment stillness begins, so
   segment boundaries are provisional and **recognition arbitrates**. A segment closing at
   `HOLDING` is buffered and evaluated — alone and as **suffix joins** with recent segments
   (`max_join_segments`, `max_segment_age_s`): a gate-passing match **commits immediately**; a
   weak one is held, so when motion resumes the next segment joins it and an over-long corner
   pause no longer splits a glyph. A `PAUSED` provisional can commit **early** past the stricter
   `soft_commit_accuracy` bar (no settle confirms intent there), covering players who never
   sufficiently stop after casting; the open stroke is then aborted so its points aren't re-emitted.
   `STOPPED` (a true settle — which also resets the path origin, hence it flushes the buffer first)
   resolves anything unrecognised as a **single deferred miscast**, unless a commit landed within
   `post_commit_suppression_s` (trailing wand-lowering motion is dropped silently — no fail streak,
   no reject flash). Scoring gates are never loosened: only segmentation is forgiving. Setting
   `enabled: False` restores the legacy behaviour (every closed stroke is a final, immediate attempt).
2b. **Lead-in trim** (`motion/stroke/lead_in_trimmer`, config `input.wand.lead_in_trim`). People
   move in a straight line from their rest/centre orientation to where the glyph starts; that
   approach run pollutes matching + the template overlay. The trimmer finds the first *sharp
   corner* (a per-step turning spike on the resampled path) and cuts everything before it —
   a smoothly-curving glyph has no sharp corner so nothing is trimmed, and a `min_trim_fraction`
   guard ignores corners right at the start. Rather than commit to the trim, recognition runs on
   **both** the raw stroke and the trimmed variant (each a full `Stroke` — points + times +
   recomputed path length) and keeps whichever scores higher (`_recognise_best_variant`). This
   removes the trade-off: a glyph that genuinely begins with a straight run matches better
   untrimmed and wins; a real approach-into-glyph matches better trimmed. The winning variant
   feeds scoring, the candidate list, and the snapshot overlay. The **live trail is not trimmed**
   (it shows raw motion).
3. **Recognition** (`spells/matching/dollar_one/DollarOneRecognizer`). Resample (N=64) →
   normalise (centroid + **uniform** scale, **no rotation** — wand gestures are orientation-
   meaningful). Score = **product of four terms**: a positional term (mean point-distance), a
   **direction term** (mean heading agreement, sampled over an N/8 stride so per-sample jitter
   is suppressed but loop-vs-line survives), a **coverage term** (mean nearest-candidate
   distance per template point — template legs the trace never visits drag it down), and a
   **shortfall term** (candidate normalised arc-length vs template's, capped at 1 — only
   under-drawing is punished, jitter overshoot is free). Positional distance alone is too
   forgiving — a straight swipe scores ~0.6 against a looped glyph; the direction factor
   collapses such shape-mismatches. Coverage x shortfall collapse **partial traces** — drawing
   just one leg of a multi-leg glyph (e.g. only the Z diagonal) scored ~0.28 on two terms but
   ~0.08 on four, while wobbly-but-complete traces stay high. Direction is preserved (so $1,
   not $P/$Q). Candidates are restricted to the
   **zone-active spell set** (`set_spell_targets`); scoring all 38 would cross-match.
4. **Templates** are authored as **layered SVGs** (`spells/templates/spell_template_<spell>.svg`,
   name after the `spell_template_` prefix = `SpellType` name lowercased). Layers by `id`:
   `gesture_path` (the true **centreline** open path — sampled by arc length, y-flipped, fed to
   $1), `gesture_visual` (the prettied UI stroke, may use a width profile / be a filled outline —
   never sampled), `origin` (a marker at the canonical cast **start**), `end_arrow` (a marker at
   the cast **end**), `mid_arrows` (UI-only direction art), `bg` (editor-only backdrop). Splitting
   `gesture_path` from `gesture_visual` matters because a width-profiled/filled visual exports as
   an *outline* (down one edge, back the other) — a there-and-back $1 can't match; the centreline
   carries the clean geometry. The loader (`svg_template_loader`) **validates** each template and
   **raises** if `origin`/`end_arrow` are missing or `gesture_path` isn't a single `<path>` (a
   broken template degrades casting — fail loud; exclude a spell knowingly via zone mapping). It
   orients sampled points to start nearest `origin` and end nearest `end_arrow`, so a reversed
   export self-corrects, and warns on malformed geometry (zero length, multiple subpaths, markers
   inconsistent with endpoints). The same SVG is the **single source of truth for the UI target
   image** too: `spell_svg_renderer` renders `gesture_visual` + `mid_arrows` + `origin` +
   `end_arrow` (hiding `gesture_path` + `bg`; ink forced black, white background) to a QPixmap at
   any resolution. The old per-spell PNGs + `SpellImageProvider` are **retired**. Add a spell =
   drop in one layered SVG.

5. **Lore** (`spells/spell_info.py` + `spells/data/spell_info.yml`). Static reference copy per
   spell — `display_name`, `nickname`, `description`, `classification`, `difficulty`,
   `pronunciation`, `notable_uses`, `source` — kept out of appsettings (bulky, never changes, no runtime
   behaviour). Keyed by `SpellType` value (same key as the templates). `load_spell_info()` builds a
   `dict[SpellType, SpellInfo]`; unlike the template loader it **degrades gracefully** (missing
   file/spell/field → blank fields + title-cased `display_name` fallback) because lore is UX-only
   and never gates a cast. The YAML is **auto-extracted** from the Spells Primer PDF — **both**
   sections (spells *with* known incantations → nickname + pronunciation; spells *without* →
   descriptive title, no pronunciation). All **228** spells are keyed 1:1 to the gesture templates,
   so `SpellType` ≡ template set ≡ lore keys (all lower-case, underscores only — the Primer's
   hyphenated names are normalised). A lore key with no matching enum member would be a typo —
   logged at debug, never fatal. Shown in the single-wand snapshot pane. Parsing lives in-repo;
   `gamevolt.io` stays a generic YAML loader.

6. **Selection** (`spells/spell_selection.py` + `spells/data/spell_selection.yml`). Hand-curated set
   of spells that ship in the theme-park experience. Kept **apart** from the PDF-extracted lore so a
   re-run of the extractor cannot clobber it. `load_included_spells()` returns a
   `frozenset[SpellType]`; keyed by `SpellType` value like lore/templates. Product-only and
   degrades gracefully like lore — inclusion never gates a cast (the recognizer still matches every
   template); missing file → empty set, unknown key → debug log. Absent key ⇒ not included.

7. **Gesture difficulty** (`spells/spell_difficulty.py`). *Computed* 1–10 rating of how hard a spell
   is to cast — distinct from the lore `difficulty` string (Primer flavour text). Blends two inputs
   the player feels: (a) **shape** of the `gesture_path` centreline — total turning, length/bbox
   density, sharp-corner count, from arc-length samples — and (b) **pass thresholds** from
   `spell_scoring` — `min_match_accuracy` (match tightness to register) + the `MASTERED` quality
   threshold. Normalisation is **absolute** (fixed catalogue-calibrated bounds, not percentile) so a
   rating never drifts when a *different* template is edited. Weights live in `DifficultyWeights`
   (shape 0.65 / threshold 0.35). Product-only and fail-soft like lore: an unsampleable template
   (`gesture_path` still a polyline, svgpathtools blow-up) degrades to a threshold-only rating rather
   than raising. Not persisted — computed on demand. Catalogue spread ≈ 2.2–7.3 at default tuning.

### 6.2 Scoring (`spells/scoring/` + `spells/settings/`)

Decoupled from recognition. `gates → base + bonuses → total → SpellCastQuality`. All config is
`SpellScoringSettings` (SettingsBase) in **appsettings.yml** under `spell_scoring`: **global
bonus magnitudes** (`bonuses`) + a per-spell `default` tuning + a list of per-spell `overrides`
(each a partial `tuning` keyed by `SpellType`, inheriting omitted fields from `default` then code
defaults). `SpellScoringSettings.spell_settings(label)` resolves the merged runtime `SpellSettings`
the scorer consumes. `overrides` is a *list* (SettingsBase passes `dict` fields through as raw values
and won't construct them into nested settings, so a `dict[str, tuning]` map can't work); `tuning.thresholds`
is a plain `dict[str, int]` (tier name → score), which the loosened SettingsBase does support.

- **Gates** (per-spell, boolean veto / false-positive filter): `min_match_accuracy`,
  `min/max_duration` (a long glyph legitimately takes longer), `min_path_length` ($1 is
  scale-blind, so absolute size lives here). A gate fail = rejected.
- **Bonuses** (additive points; total can exceed 100): base (`accuracy×100×difficulty_weight`,
  difficulty per-spell), XP (unique spells cast, lifelong per wand), cadence (speed-uniformity),
  tempo (per-spell ideal duration band). Magnitudes (xp/cadence/tempo max) are global.
- **Pity / streak** bonus: +N per prior consecutive fail, applied only to a gate-passing cast
  that fell short of the spell's **lowest** tier, clamped to that tier. Resets on any success.
- **Quality tiers** are per-spell (`quality_thresholds`) — not every spell needs all four;
  when a spell specifies tiers they replace the default set wholesale.

The scorer is the **local dev stand-in** for hub-side grading: XP / streak / quality need
profile + history, so they lift to the hub later (see §5.1). Kept cleanly separable (no
recognition coupling) for that move.

### 6.3 Reporting

`TrackedWand` emits a `SpellCast` (wand_id, spell_type, `CastScore`) only for a recognised
cast. `LocalSpellCastReporter` (hub stand-in) no longer grades — it plays the show with the
quality the scorer already decided, and returns it. `SpellCastReporter` / `ShowSystemReporter`
split per §6 remains the target; `ShowSystemReporter` not yet separated.

### 6.4 Still open

- Ambiguity margin (reject when top-1 ≈ top-2 within the active set).
- Top-N candidate payload on `SpellCastReporter`; `ShowSystemReporter` split.
- Persistence of per-wand XP/streak (in-memory today; lost on restart).

---

## 7. wands_app internal architecture

`WandsApp` is split (logical, single-process) into two cooperating apps composed by `WandsSystemBuilder`.

### 7.1 `TrackingApp` — "where is the wand"

Owns:

- `WandImuStream` (sensor source lifecycle)
- `ZoneApplication` / `ZoneManager`
- `WandSessionCoordinator` (binds wand_id → wizard session on presence enter)

### 7.2 `RecognitionApp` — "what is the wand doing"

Owns:

- `WandServer` (subscribes to sensor stream packets)
- `TrackedWandManager` (per-wand motion phase, stroke windowing, $1 recogniser + scorer)
- `WandDeviceController` (sends wand commands)
- `WandSpellCueController`
- `SessionRecorder` (`recording/`) — captures a recording session to disk, armed by the visualiser's **Record Session** toggle (the `record_session_changed(active, name)` event off `WandVisualiserProtocol`, fired by the `QtWandVisualiser` record button once a wizard name is entered). While armed it writes `<session_recorder.output_dir>/<timestamp>_<name>/` containing `casts.jsonl` (one line per cast the snapshot would show — recognised casts **plus** rejected ones clearing the noise gate, i.e. the same `passed_gates or match_accuracy >= snapshot.min_match_accuracy` test as `QtWandVisualiser`; carries spell, quality/`REJECTED`, `recognized`/`gate_failures`, full `CastScore`, and raw/normalised/template stroke points — filtered from `cast_attempted`), `raw.jsonl` (every `wand_rotation_updated` sample, for later analysis / trail rebuild), `session.json` (metadata + counts + a `metrics` block: success rate, longest combo, total points, quality counts, spell variety (distinct attempted / recognised out of total spells loaded, e.g. 11/30), favourite/signature/trickiest spell, and standout casts (highest-scoring, best raw match, fastest, flashiest, closest miss) plus a per-spell rollup — computed over the recorded casts at record-off), and `images/NNN_SPELL_QUALITY.png` (a snapshot PNG per cast). Image rendering is delegated through the `CastImageRenderer` protocol so the recorder stays GUI-free; the only impl, `QtCastImageRenderer`, reuses `SnapshotWidget` and is wired only when the Qt visualiser is enabled (headless runs still record casts + points, just no images).
- Wand visualiser (`WandVisualiserProtocol`) — the concrete window is chosen by `system_type` in `WandsSystemBuilder`. **`eliko_rtls` → `QtMultiWandVisualiser`** (multi-wand RTLS view): every active wand's live trail overlaid on **one shared canvas**, colour-keyed by id (palette in `multi_wand_visualiser.palette`, assigned to `tracked_wand_ids` in order), with a corner **legend** (swatch · id · zone · spell targets · last cast). Trails are pointing-direction deltas integrated from a per-wand origin — there's no shared floor position in the IMU stream, so colour is what separates them. A wand's trail clears on its per-stroke settle (`wand_forward_reset`) and the wand is removed entirely (trail + legend row) on `wand_exited_zone`. Zone presence is wired into the visualiser from the zone manager by the builder via the no-op `wand_entered_zone` / `wand_exited_zone` protocol hooks. **`eliko_single_anchor` (mock/dev) → `QtWandVisualiser`** — a **single-wand** Qt (PySide6) window pinned to `wand_visualiser.wand_id` in appsettings. Either window is replaced by `HeadlessVisualiser` when its `is_enabled` is false. The single-wand window is **16:9** (1600×900) with three panes left→right: **left pane** (a `QStackedWidget` that swaps by zone spell-count) | **live rolling trail** | **frozen snapshot** of the last qualifying cast attempt (shape-vs-template overlay + full scoring breakdown — scoring only; lore moved left). The left pane shows the **`SpellInfoCard`** (Primer-style, dark-theme) when the active zone holds **exactly one** spell — title · classification·difficulty·pronunciation · nickname · description · gesture art (light-ink SVG) · notable uses · source, plus a computed **CAST DIFFICULTY x/10** meter (`spell_difficulty`, distinct from the lore difficulty string) — and falls back to the tiled **spell targets** view (each tile rendered from the layered SVG via `spell_svg_renderer`, no PNGs) for a **multi-spell** (or empty) zone. Difficulty ratings are precomputed per spell at build from each template + its resolved `spell_scoring` thresholds (`min_match_accuracy` + `MASTERED`). Driven cooperatively via `processEvents()` in `update()` — no separate Qt mainloop. Fed by three `TrackedWandManager` events: `wand_rotation_updated` (trail), `wand_forward_reset` (trail reset), and `cast_attempted` (snapshot + target flash). `cast_attempted` carries a `CastAttempt` (full `CastScore` + stroke points + $1-normalised candidate + matched template points) and fires for **every** scored stroke — recognised or rejected — unlike `spell_cast` which fires only for recognised casts. On each attempt the matched spell's target tile flashes its quality colour (reject-red / rudimentary-yellow / skilled-light-blue / experienced-green / mastered-light-purple); the snapshot only swaps when an attempt clears `snapshot.min_match_accuracy` (or passes gates), so noise flicks don't clobber the last real attempt. Changing zone (`show_zone`) clears the snapshot — the previous cast result is stale. In **mock** this same window object also serves as the zone visualiser (`show_zone`) and hosts `QtZoneControls` (see §6), so one window does everything; the old separate tkinter spell-target window + `SpellCastPresentationController` are gone.

### 7.3 Seams between Tracking and Recognition

Each seam is treated as a future network boundary; swapping the implementation to a remote transport is the only change needed for a process split.

| Seam | Owner | Consumer | Future remote form |
|------|-------|----------|--------------------|
| `WandImuStream` | Tracking | Recognition's `WandServer` | `NetworkWandSensorStream` (WebSocket client) |
| `WandPositionStream` *(planned)* | Tracking | Recognition (if needed) | network stream |
| `WandCommandSink` (today: `ElikoWandCommandSink`) | constructed in `WandsSystemBuilder` | Recognition's `WandDeviceController` | wand-command request channel |
| `ZoneManagerProtocol` events (`wand_entered_zone`, `wand_exited_zone`) | Tracking | Recognition's `TrackedWandManager` | presence channel (MQTT, per hub plan) |
| `WizardSessionStore` | shared | both | session lookup service |

Don't add new cross-app coupling that isn't on this list without flagging it.

---

## 8. Module map

| Path | Purpose |
|------|---------|
| `wands_app/` | Entry point, app composition, settings, `TrackingApp`, `RecognitionApp`, `WandsSystem`, `WandsSystemBuilder`. |
| `wand/` | Wand-side primitives: `WandServer`, `TrackedWandManager`, `WandClient`, `CastAssembler` (segment buffer + recognition-gated commit), sensor stream (`streaming/`), interpreters, device controller. |
| `motion/` | Motion phase tracking (`MotionProcessor`, `MotionPhaseTracker`) + stroke windowing (`stroke/StrokeWindower`) + lead-in trimming (`stroke/lead_in_trimmer`). |
| `spells/` | $1 recogniser (`matching/dollar_one/`, incl. `svg_template_loader`), layered SVG templates (`templates/` — `gesture_path`/`gesture_visual`/`origin`/`end_arrow`/`mid_arrows`/`bg` layers), scorer (`scoring/`), per-spell settings (`settings/`), static lore (`spell_info.py` + `data/spell_info.yml`), park selection (`spell_selection.py` + `data/spell_selection.yml`), computed gesture difficulty (`spell_difficulty.py`), `SpellCast`, cue + presentation controllers. |
| `zones/` | Zone manager, zone application, mock controls, visualisation. |
| `services/` | Profile, presence reporter, spell-cast reporter, session store, session coordinator. (These are the proto-hub implementations.) |
| `recording/` | `SessionRecorder` + `CastImageRenderer` protocol + settings. Writes per-session dirs (recognised casts, raw rotation stream, snapshot images) driven by the visualiser's record toggle. |
| `messaging/` | Internal message types and transports (UDP TX/RX, message handlers). |
| `show_system/` | Show-system controller and outbound message types. |
| `visualisation/` | Two Qt windows behind `WandVisualiserProtocol`: single-wand dev window (`qt/`: window, spell targets, live trail, snapshot panel, zone controls) + multi-wand RTLS window (`qt/qt_multi_wand_visualiser`, `multi_wand_trail_widget`, `wand_legend_widget`). Shared comet/Catmull-Rom drawing in `qt/trail_render`. Plus quality colours, `spell_svg_renderer` (SVG→QPixmap target art), `HeadlessVisualiser`. |
| `wizards/` | Wizard name/profile primitives. |
| `gamevolt/` | Shared infra: logging, events, web sockets, messaging plumbing, IO utils. |
| `scripts/` | Build, install, workflow shell scripts and development helpers. |

---

## 9. Entry points and configuration

### 9.1 Processes

- **`wands_app/main.py`** — loads `appsettings.yml` + env overlay, builds `WandsSystem`, starts both apps, runs the update loop.

### 9.2 Settings

Two-layer YAML: `appsettings.yml` (bundled defaults) + `appsettings.env.yml` (per-environment overrides at install path). Loaded via `gamevolt.io.utils.bundled_path` / `install_path`.

`wands_app` settings consolidate the deployment shape behind two top-level fields:

- `system_type` — one of `eliko_rtls` or `eliko_single_anchor`. Drives `WandImuStream`, `WandCommandSink`, and `ZoneApplication` selection in `WandsSystemBuilder`. The pairing is **hardcoded**: `eliko_rtls` = production (`ZoneManager` driven by external UDP positioning, no UI controls; the **multi-wand** `QtMultiWandVisualiser` shows all active wands' trails when `multi_wand_visualiser.is_enabled`); `eliko_single_anchor` = mock / dev (`MockZoneManager` driven by `QtZoneControls` inside the unified Qt window, which also shows spell targets + wand trail + cast snapshot).
- `tracked_wand_ids` — single list of wand IDs. Doubles as the `WandServer` allowlist (empty list = allow all) and the per-id tracker spawn list in `TrackedWandManager`. Adding a wand is a one-line edit.

The `imu_stream` block carries one or both of the `eliko` / `eliko_single_anchor` sub-blocks. Each sub-block is consumed only when its matching `system_type` is selected.

### 9.3 Build

Python environment is managed by `uv`. Dependencies live in `pyproject.toml`; `uv.lock` pins the resolved set. Local setup:

```bash
uv sync               # creates .venv/ and installs runtime deps
uv sync --group dev   # adds dev tooling (pyinstaller, pytest, ruff, etc.)
uv run python -m wands_app.main
```

`scripts/build.sh` produces a bundled executable via `uv run pyinstaller` against `wands.spec`. `wands_app/build_info.py` is generated at build time with version + SHA + timestamp; falls back to `"dev"` when running from source.

Container builds are not currently supported — `Dockerfile.dev` was removed with the cdtr-rtls retirement and needs a fresh uv-based image design.

---

## 10. Roadmap and open questions

Tracked here so they don't get lost. Order is rough priority.

1. **Eliko binding.** Concrete API for position stream, IMU stream, and command channel. `WandImuStream` Eliko impls landed: `ElikoWandImuStream` (PR_Q over TCP via RTLS server, +Y forward) and `ElikoSingleAnchorWandImuStream` (raw PR over USB-serial direct to a single anchor; client-side SFLP→quat decode). `WandCommandSink` Eliko impl landed (`ElikoWandCommandSink`, transport-agnostic via `ElikoCommandClient` protocol; delegates command building to `PekioClient`; typed methods `enter_idle` / `exit_idle` / `pulse`; haptic not on surface — see [§4.5](#45-haptic-disabled)). Wand-reboot recovery landed on the single-anchor path (`WandRebootDetector` watches for `PP,VERS` boot banners and re-issues per-tag `CMD0` to restart IMU sampling). Still to do: `WandPositionStream` (Eliko `COORD_Z`). Open question for the single-anchor path: serial-transport reconnect behaviour — init commands are sent once on start; serial reconnects currently do not re-fire them (would need a `connected` event on `SerialTransport`). Wand-reboot recovery does not extend to RTLS yet — RTLS server is presumed to manage per-tag IMU state itself.
2. **`WandPositionStream` protocol + staging implementation.** Stop faking position. Let `ZoneManager` derive zones from real positions; retire the UDP `ZoneEnteredMessage` / `ZoneExitedMessage` ingress.
3. **Spell match rework.** Largely landed — legacy step-group matcher replaced by the $1 unistroke pipeline + decoupled scorer with per-spell settings (`spell_scoring` in appsettings.yml, `SpellScoringSettings`); see §6. Remaining: ambiguity margin (top-1≈top-2 reject), top-N candidate payload on `SpellCastReporter`, per-wand XP/streak persistence.
4. **`ShowSystemReporter` split.** Separate from `SpellCastReporter`. Development implementation computes grade locally.
5. **Hub implementations.** HTTP `ProfileService`, HTTP `ZoneSpellBindingService`, MQTT `WandPresenceReporter`, MQTT `SpellCastReporter`, MQTT or HTTP `ShowSystemReporter`.
6. **Hot configuration reload.** Inbound hub→app, when needed.
7. **Mock-mouse sensor source.** Hardware-free development implementation (stub at `wand/streaming/mouse/`).
8. **Zone polygon ownership.** Still local configuration today; possibly hub-owned later.
9. **Container build story.** Fresh `Dockerfile` keyed to `uv` once cross-build to ARM is needed again.
10. **Orphan cleanup in `gamevolt/serial/`.** `serial_receiver.py` lost its last consumer when `LineBasedWandImuStream` was retired; untangling needs `SerialTransport`'s `LineReceiverProtocol` base reworked.

---

## 11. Conventions

- **Naming:** full words on new types (`RecognitionApp`, not `RecogApp`). Existing abbreviations (`pkt`, `ws`, `udp`, `tx`/`rx`) stay.
- **App/main split:** every deployable has a composable `*App` class that owns lifecycle, and a `*_main` that builds dependencies and drives the loop. Mirrored across `ZoneApplication`, `TrackingApp`, `RecognitionApp`.
- **Seams are protocols.** New cross-component coupling goes behind a `Protocol`. Direct cross-app object references are limited to the seam table in §7.3.
