# Changelog (Docker Version)

## [2.1.0]

### Ported from HA Addon v2.1.0
- **Multi-user / per-session device tracking:** Each browser tab now tracks its own selected device independently. Previously all clients shared a single `current_topic` global, causing cross-talk.
- **Thread safety:** Device list now protected with locks to prevent `dictionary changed size during iteration` crashes when MQTT messages arrive during cleanup.
- **Crash on non-dict MQTT payloads:** Fixed `TypeError: argument of type 'int' is not iterable` caused by Z2M publishing bare integers to parameter confirmation topics.
- **Byte parsing:** `parse_signed_16` moved to module level to prevent fragile closure behavior inside loops.
- **Zone editing: non-target zones no longer draggable.** Shapes are only interactive when "Draw / Edit" is active for a specific zone.
- **Zone editing: zones locked outside edit mode.** Prevents accidental drags.
- Wrapped all Plotly chart calls in try/catch to prevent UI crashes if chart element is unavailable.

### Added
- **Connection status indicators:** Live Server and MQTT status dots in the status bar (green/red/pulsing).
- **Reconnection banner:** Banner appears on WebSocket disconnect and auto-dismisses on reconnect. MQTT disconnections also surfaced.
- **Command error feedback:** Toast notifications appear when a command fails (no device selected, MQTT down, invalid parameter).
- **Parameter validation:** All settings sent to the switch validated against a whitelist before publishing. Invalid values are rejected with an error toast.
- **Accurate FOV overlay:** Radar grid now shows the real HLK-LD2450 field of view — solid cone for rated ±60° (120°), dashed cone for observed ±75° (150° extended range). Range arcs at 1m intervals up to 6m with labels.
- **Non-target zone context during editing:** When editing a zone, other zones remain visible (dimmed) as scatter traces for spatial reference.
- **Auto-Scale / Reset Scale buttons** in Visualizer Settings.
- **Persistent configuration:** Settings can be saved to `/data/config.json` via the new **⚙ Config** button in the header. ENV variables remain supported as a fallback. Requires the `/data` volume to be mounted (see `docker-compose.yml`).
- **`/api/config` GET/POST endpoints** for reading and writing the persistent config file.
- **Stale device cleanup thread** to remove devices not seen for over 1 hour.
- Full `force_sync` that queries both standard Z2M attributes and mmWave area state from the switch.
- `command_ack` / `command_error` WebSocket events for frontend feedback.
- Legacy Area 1 fallback: automatically maps composite `mmwave_detection_areas:area1` writes to top-level `mmWaveWidth/Depth/HeightMin/Max` params for older firmware.

### Changed
- Bumped Plotly to `3.3.1` (from `2.35.2`).
- Default radar map X scale widened from ±450 cm to ±600 cm to accommodate the full extended FOV cone.
- `requirements.txt`: removed `eventlet` (unused; `threading` async_mode is used).
- `docker-compose.yml`: added `volumes` entry documenting the `/data` persistent config mount.
- Table rows now built as a single `innerHTML` assignment instead of `+=` concatenation.
- On WebSocket reconnect, frontend automatically re-subscribes to the previously selected device.

## [2.0.2]
- Initial public release.