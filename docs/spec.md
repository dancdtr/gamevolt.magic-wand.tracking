# Magic Wand Tracking — System Specification

**Status:** living document. High-level architecture as of 2026-05-22.
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
                              │   (or, today, anchor relays + custom positioning)
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
- **Data plane (outbound):** wand command channel (haptics, lamps, activation, TX-frequency).
- **Control plane:** sync lookups and async events to/from the hub.

---

## 3. Deployable units

| Unit | Status | Role |
|------|--------|------|
| `wands_app/` | active | Main runtime. Hosts `TrackingApp` + `RecognitionApp` in one process. |
| `anchor_relay/` | staging | Custom UWB relay built while Eliko's product was in development. Will be reworked to conform to the new sensor-source protocols; one of multiple sensor-source implementations going forward. |
| Eliko RTLS | external (planned) | Production sensor source. Provides position stream, IMU stream, and wand-command channel. |
| Hub | external (planned) | Single venue-local instance. Source of truth for profiles, zone-spell bindings, scoring. Republishes events upstream and to show system. Always-on; if it's down, the experience is down. |
| Show system | external | Lights, sound, effects. In production, fed by the hub. In development, fed directly via UDP from a development implementation of `ShowSystemReporter`. |
| Cloud | external | Out of scope for this app. Hub's concern. |

---

## 4. Data plane protocols

Three protocols cover all sensor I/O. Each is implementation-agnostic; multiple implementations can coexist and production may share a transport beneath them.

### 4.1 `WandImuStream` (inbound)

Emits per-wand IMU samples (rotation, timing). Two implementations live in tree, selected by the top-level `system_type` flag in `appsettings.yml` (see §9.2):

- `LineBasedWandImuStream` — reads WebSocket lines from the custom anchor relay. Used by `system_type: anchor_relay` and `anchor_relay_live`.
- `ElikoWandImuStream` — consumes lines from a shared `ElikoClient` (TCP to Eliko RTLS Server, default port 25025) filtered to `PR_Q` (per-tag quaternion bursts), and emits one `AssembledPacket` per line (10 samples each). The wand's body-frame forward axis is +Y; each sample's forward vector is `q · (0,1,0)`, Q15-encoded into the existing `data_str` format so `WandClient` consumes both sources identically. Tag IDs are normalised to bare upper hex (e.g. `0x001D6C` → `001D6C`). Per-sample dt is fixed by IMU hardware and configured (not derived from packet timestamps). Used by `system_type: eliko_rtls`.
- `ElikoSingleAnchorWandImuStream` — consumes raw `PR` lines from an `ElikoSingleAnchorClient` (USB-serial to a single anchor, no RTLS server). Each PR sample is a 6-byte SFLP word packing three IEEE-754 half-floats `(x, y, z)` of a unit quaternion; `w` is recovered as `sqrt(1 − x² − y² − z²)` per the STM `sflp2q` algorithm. Forward Q15 encoding (via the shared `quat_forward_encoder`) and `AssembledPacket` shape are identical to the RTLS path. On `start_async`, the client sends `$PEKIO,DC,001,CMD0,0x<TAG>,0x00000903` per tracked tag (enable IMU) + `$PEKIO,DC,001,SPQF,P` (subscribe to PR). Used by `system_type: eliko_single_anchor`.

`ElikoClient` (TCP) and `ElikoSingleAnchorClient` (serial) both satisfy the `ElikoCommandClient` protocol, so the IMU stream and `ElikoWandCommandSink` share a single transport per deployment. Each stream owns its client's lifecycle (`start_async` on the client when the stream starts).

Eliko's `COORD_Z` position feed is intentionally not consumed here; position will land via the planned `WandPositionStream` (§4.2). Future mock implementations (e.g. mouse-driven) are anticipated but out of spec.

### 4.2 `WandPositionStream` (inbound, new)

Emits per-wand position updates. Does not exist today — position arrives indirectly via legacy `ZoneEnteredMessage` / `ZoneExitedMessage` over UDP, from an older custom positioning system. Once `WandPositionStream` is in place, the `ZoneManager` derives zone enter/exit from raw position + polygon configuration, and the legacy zone-event ingress retires.

### 4.3 `WandCommandSink` (outbound)

Accepts internal `Message`s targeted at a specific wand:

- **Activation / deactivation** — flips wand transmit state. Activation begins the IMU stream for that wand; deactivation ends it. Replaces the older "connect/disconnect" lifecycle.
- **Haptics / vibration**, lamp colour, IMU transmit-frequency changes, etc.

Surface:

```python
class WandCommandSink(Protocol):
    def send_to_wand(self, wand_id: str, message: Message) -> None: ...
    def broadcast_to_wand(self, wand_id: str, message: Message) -> None: ...
```

Two implementations live in tree, selected by `system_type`:

- `AnchorAreaManager` (anchor relay) — owns the zone↔anchor lookup and routes via the relay's `WebSocketServer`. Used by `anchor_relay` and `anchor_relay_live`.
- `ElikoWandCommandSink` (Eliko, both RTLS and single-anchor) — transport-agnostic; targets the `ElikoCommandClient` protocol so it can sit on either `ElikoClient` (TCP) or `ElikoSingleAnchorClient` (serial). Today only maps `WandLedMessage(enabled=True)` → `SET_TAG_LEDH`; other message types log-and-noop until Eliko exposes equivalents.

`WandDeviceController` depends on `WandCommandSink` (protocol), not on a specific implementation.

### 4.4 Notes

- Position and IMU stay as separate protocols even where production shares transport. Operator tools may want one without the other (e.g. a "show me where every wand is" viewer).
- `WandCommandSink` stays separate from the inbound streams. Decoupling input from output keeps mock/debug implementations simple and avoids cross-coupling unrelated transports.

---

## 5. Control plane protocols

Recognition and tracking depend on per-service protocols. No `HubClient` facade exists in code — "hub" is the name of the deployment pattern where a set of implementations happen to route over HTTP/MQTT to the real hub. In development, the same protocols are satisfied by local implementations.

### 5.1 Sync lookups (would be HTTP in production)

| Protocol | Purpose | Today |
|----------|---------|-------|
| `ProfileService` | wand_id → wizard profile | `LocalProfileService` |
| `ZoneSpellBindingService` *(planned)* | which spell(s) are active in a given zone | not yet — spells are bound in `ZoneFactory` configuration |

The spell **library** (definitions of each spell) stays local in `spells/`. The hub only owns which spell is active where.

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

Match grading and recognition floors live in the **hub**, not in recognition. Recognition is a signal processor; it does not decide what counts as "good enough" or which show response level to play.

### 6.1 Recognition's job

- Segment wand motion into **attempts** (e.g. pause → gesture segments → pause).
- For each attempt, score against every candidate spell that might be active.
- Emit one `SpellCastReporter` event per attempt, carrying the full top-N candidates with raw accuracy scores.

No tier labels, no threshold filtering, no decision to fire or not fire a show response.

### 6.2 Hub's job

- Pick the intended spell from the candidate list (considers zone binding, player profile, expected spell).
- Decide tier — failed attempt, recognised-weak, recognised-strong, or more — using configurable thresholds.
- Trigger `ShowSystemReporter` to play the matching response level.
- Record for metrics; future feature uses metrics to simplify the model for struggling players in real time.

### 6.3 Reporter split

`SpellCastReporter` and `ShowSystemReporter` are separate protocols. Same data may flow through both, but the consumers differ:

- `SpellCastReporter`: raw candidates + scores. Multiple sinks (UDP, file, hub-MQTT) typical.
- `ShowSystemReporter`: graded outcome. Development implementation computes the grade locally (so recognition still sees no show-system concept); production implementation is a thin wrapper that the hub drives.

### 6.4 Code rework implied

- Current `spell_response_type.py` and any threshold logic inside `SpellMatcher` move out of recognition.
- `SpellCastReporter` event payload becomes top-N candidates rather than single-match.
- New attempt-segmentation logic to define attempt boundaries.

Tracked as roadmap items, not part of this spec's structural change.

---

## 7. wands_app internal architecture

`WandsApp` is split (logical, single-process) into two cooperating apps composed by `WandsSystemBuilder`.

### 7.1 `TrackingApp` — "where is the wand"

Owns:

- `WebSocketServer` (relay ingress, while custom relays exist)
- `WandImuStream` (sensor source lifecycle)
- `ZoneApplication` / `ZoneManager`
- `AnchorAreaManager`
- `WandSessionCoordinator` (binds wand_id → wizard session on presence enter)

### 7.2 `RecognitionApp` — "what is the wand doing"

Owns:

- `WandServer` (subscribes to sensor stream packets)
- `TrackedWandManager` (per-wand motion processors, gesture history, spell matchers)
- `WandDeviceController` (sends wand commands)
- `WandSpellCueController`, `SpellCastPresentationController`
- `WandVisualiser`

### 7.3 Seams between Tracking and Recognition

Each seam is treated as a future network boundary; swapping the implementation to a remote transport is the only change needed for a process split.

| Seam | Owner | Consumer | Future remote form |
|------|-------|----------|--------------------|
| `WandImuStream` | Tracking | Recognition's `WandServer` | `NetworkWandSensorStream` (WebSocket client) |
| `WandPositionStream` *(planned)* | Tracking | Recognition (if needed) | network stream |
| `WandCommandSink` (today: `AnchorAreaManager`) | Tracking | Recognition's `WandDeviceController` | wand-command request channel |
| `ZoneManager` events | Tracking | Recognition's `TrackedWandManager` | presence channel (MQTT, per hub plan) |
| `WizardSessionStore` | shared | both | session lookup service |

Don't add new cross-app coupling that isn't on this list without flagging it.

---

## 8. Module map

| Path | Purpose |
|------|---------|
| `wands_app/` | Entry point, app composition, settings, `TrackingApp`, `RecognitionApp`, `WandsSystem`, `WandsSystemBuilder`. |
| `anchor_relay/` | Custom UWB relay binary (staging). Reads serial, ships lines over WebSocket to wands_app. |
| `wand/` | Wand-side primitives: `WandServer`, `TrackedWandManager`, `WandClient`, sensor stream (`streaming/`), packet parsing (`data/`), interpreters, device controller. |
| `motion/` | Motion processing, gesture history, kinematics. |
| `spells/` | Spell library, definitions, matcher, accuracy scoring, cue + presentation controllers. |
| `zones/` | Zone manager, polygons, zone application, mock controls, visualisation. |
| `anchor_area/` | Anchor-area mapping (zone-id → anchor-id) and message routing. |
| `services/` | Profile, presence reporter, spell-cast reporter, session store, session coordinator. (These are the proto-hub implementations.) |
| `messaging/` | Internal message types and transports (UDP TX/RX, message handlers). |
| `show_system/` | Show-system controller and outbound message types. |
| `display/` | Image libraries, visual assets handling. |
| `visualisation/` | Wand visualiser, trail rendering, colour registry. |
| `wizards/` | Wizard name/profile primitives. |
| `gamevolt/` | Shared infra: logging, events, web sockets, messaging plumbing, IO utils. |
| `scripts/` | Build, install, workflow shell scripts and development helpers. |

---

## 9. Entry points and configuration

### 9.1 Processes

- **`wands_app/main.py`** — loads `appsettings.yml` + env overlay, builds `WandsSystem`, starts both apps, runs the update loop.
- **`anchor_relay/main.py`** — loads relay settings, builds `RelayApp`, runs until killed. One per physical anchor in staging.

### 9.2 Settings

Two-layer YAML: `appsettings.yml` (bundled defaults) + `appsettings.env.yml` (per-environment overrides at install path). Loaded via `gamevolt.io.utils.bundled_path` / `install_path`. Both wands_app and anchor_relay follow the same convention.

`wands_app` settings consolidate the deployment shape behind two top-level fields:

- `system_type` — one of `eliko_rtls`, `eliko_single_anchor`, `anchor_relay`, `anchor_relay_live`. Drives `WandImuStream`, `WandCommandSink`, and `ZoneApplication` selection in `WandsSystemBuilder`. There is no separate `is_dev` flag and no `imu_stream.mode` knob.
- `tracked_wand_ids` — single list of wand IDs. Doubles as the `WandServer` allowlist (empty list = allow all) and the per-id tracker spawn list in `TrackedWandManager`. Adding a wand is a one-line edit.

The `imu_stream` block carries `header_ttl_s` (used by the line-based stream) and an optional `eliko` sub-block with `connection`, `parsing`, and `command_sink` sections; the sub-block is consumed only when `system_type: eliko_rtls`.

### 9.3 Build

Python environment is managed by `uv`. Dependencies live in `pyproject.toml`; `uv.lock` pins the resolved set. Local setup:

```bash
uv sync               # creates .venv/ and installs runtime deps
uv sync --group dev   # adds dev tooling (pyinstaller, pytest, ruff, etc.)
uv run python -m wands_app.main
```

`scripts/build.sh` produces bundled executables via `uv run pyinstaller` against the `.spec` files (`wands.spec`, `relay.spec`). `wands_app/build_info.py` (and `anchor_relay/build_info.py`) is generated at build time with version + SHA + timestamp; falls back to `"dev"` when running from source (the literal string in `build_info.py`, not the project's "development" environment label).

The Docker build (`Dockerfile.dev`) still uses micromamba and `environment.yml`-style assumptions — it has not yet been migrated and will fail until reworked.

---

## 10. Roadmap and open questions

Tracked here so they don't get lost. Order is rough priority.

1. **Eliko binding.** Concrete API for position stream, IMU stream, and command channel. `WandImuStream` Eliko impls landed: `ElikoWandImuStream` (PR_Q over TCP via RTLS server, +Y forward) and `ElikoSingleAnchorWandImuStream` (raw PR over USB-serial direct to a single anchor; client-side SFLP→quat decode). `WandCommandSink` Eliko impl landed (`ElikoWandCommandSink`, transport-agnostic via `ElikoCommandClient` protocol; currently `WandLedMessage` → `SET_TAG_LEDH` only; TX-enable and haptics still log-and-noop pending Eliko equivalents). Still to do: `WandPositionStream` (Eliko `COORD_Z`). Open question for single-anchor path: reconnect behaviour — init commands are sent once on start; serial reconnects currently do not re-fire them (would need a `connected` event on `SerialTransport`).
2. **Split `AnchorAreaManager` further.** It currently implements `WandCommandSink` *and* owns anchor-area↔zone presence forwarding. Once a second `WandCommandSink` impl is needed (Eliko, mock), pull the command-routing concern out into its own class so AAM goes back to being just zone↔anchor mapping.
3. **`WandPositionStream` protocol + staging implementation.** Stop faking position. Let `ZoneManager` derive zones from real positions.
4. **Anchor relay rework.** Conform to the new sensor-source protocols rather than being the implicit single source.
5. **Spell match rework.** Attempt-segmentation logic; top-N candidate payload on `SpellCastReporter`; remove tier logic from recognition.
6. **`ShowSystemReporter` split.** Separate from `SpellCastReporter`. Development implementation computes grade locally.
7. **Hub implementations.** HTTP `ProfileService`, HTTP `ZoneSpellBindingService`, MQTT `WandPresenceReporter`, MQTT `SpellCastReporter`, MQTT or HTTP `ShowSystemReporter`.
8. **Hot configuration reload.** Inbound hub→app, when needed.
9. **Mock-mouse sensor source.** Hardware-free development implementation.
10. **Zone polygon ownership.** Still local configuration today; possibly hub-owned later.
11. **Legacy positioning retirement.** Once `WandPositionStream` is live and proven.
12. **Migrate `Dockerfile.dev` to uv.** Local dev is on uv as of 2026-05-22; Docker still uses micromamba + the removed `environment.yml` and needs rewriting before container builds work again.

---

## 11. Conventions

- **Naming:** full words on new types (`RecognitionApp`, not `RecogApp`). Existing abbreviations (`pkt`, `ws`, `udp`, `tx`/`rx`) stay.
- **App/main split:** every deployable has a composable `*App` class that owns lifecycle, and a `*_main` that builds dependencies and drives the loop. Mirrored across `RelayApp`, `ZoneApplication`, `TrackingApp`, `RecognitionApp`.
- **Seams are protocols.** New cross-component coupling goes behind a `Protocol`. Direct cross-app object references are limited to the seam table in §7.3.
