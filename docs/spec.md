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

Emits per-wand IMU samples (rotation, timing). Today's single implementation is `LineBasedWandImuStream` reading WebSocket lines from the custom anchor relay. Tomorrow adds an Eliko-backed implementation. Future mock implementations (e.g. mouse-driven) are anticipated but out of spec.

### 4.2 `WandPositionStream` (inbound, new)

Emits per-wand position updates. Does not exist today — position arrives indirectly via legacy `ZoneEnteredMessage` / `ZoneExitedMessage` over UDP, from an older custom positioning system. Once `WandPositionStream` is in place, the `ZoneManager` derives zone enter/exit from raw position + polygon configuration, and the legacy zone-event ingress retires.

### 4.3 `WandCommandSink` (outbound)

Accepts internal `Message`s targeted at a specific wand:

- **Activation / deactivation** — flips wand transmit state. Activation begins the IMU stream for that wand; deactivation ends it. Replaces the older "connect/disconnect" lifecycle.
- **Haptics / vibration**, lamp colour, IMU transmit-frequency changes, etc.

Today's path is `AnchorAreaManager → WebSocketServer → anchor → wand`. To be lifted into a dedicated `WandCommandSink` protocol. Production implementation talks to Eliko; staging implementation uses the anchor-relay path; development implementation can render to a GUI or log.

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
| `AnchorAreaManager` / `WandCommandSink` | Tracking | Recognition's `WandDeviceController` | wand-command request channel |
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

### 9.3 Build

`scripts/build.sh` produces the bundled executables via the `.spec` files (`wands.spec`, `relay.spec`). `wands_app/build_info.py` (and `anchor_relay/build_info.py`) is generated at build time with version + SHA + timestamp; falls back to `"dev"` when running from source (the literal string in `build_info.py`, not the project's "development" environment label).

---

## 10. Roadmap and open questions

Tracked here so they don't get lost. Order is rough priority.

1. **Eliko binding.** Concrete API for position stream, IMU stream, and command channel. Build conforming implementations of `WandImuStream`, `WandPositionStream`, `WandCommandSink`.
2. **`WandCommandSink` protocol extraction.** Lift today's `AnchorAreaManager`-driven WebSocket path into a clean protocol; activate/deactivate semantics first.
3. **`WandPositionStream` protocol + staging implementation.** Stop faking position. Let `ZoneManager` derive zones from real positions.
4. **Anchor relay rework.** Conform to the new sensor-source protocols rather than being the implicit single source.
5. **Spell match rework.** Attempt-segmentation logic; top-N candidate payload on `SpellCastReporter`; remove tier logic from recognition.
6. **`ShowSystemReporter` split.** Separate from `SpellCastReporter`. Development implementation computes grade locally.
7. **Hub implementations.** HTTP `ProfileService`, HTTP `ZoneSpellBindingService`, MQTT `WandPresenceReporter`, MQTT `SpellCastReporter`, MQTT or HTTP `ShowSystemReporter`.
8. **Hot configuration reload.** Inbound hub→app, when needed.
9. **Mock-mouse sensor source.** Hardware-free development implementation.
10. **Zone polygon ownership.** Still local configuration today; possibly hub-owned later.
11. **Legacy positioning retirement.** Once `WandPositionStream` is live and proven.

---

## 11. Conventions

- **Naming:** full words on new types (`RecognitionApp`, not `RecogApp`). Existing abbreviations (`pkt`, `ws`, `udp`, `tx`/`rx`) stay.
- **App/main split:** every deployable has a composable `*App` class that owns lifecycle, and a `*_main` that builds dependencies and drives the loop. Mirrored across `RelayApp`, `ZoneApplication`, `TrackingApp`, `RecognitionApp`.
- **Seams are protocols.** New cross-component coupling goes behind a `Protocol`. Direct cross-app object references are limited to the seam table in §7.3.
