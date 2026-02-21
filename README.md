 Inovelli mmWave Visualizer — Standalone Docker

**Live 2D presence tracking and interference zone configuration for Inovelli mmWave Smart Switches in Zigbee2MQTT.**

## Overview

This is the standalone Docker version of the Inovelli mmWave Visualizer. It decodes Zigbee2MQTT payloads to visualize real-time tracking data and allows you to configure detection, interference, and stay zones via a web UI. Ideal for users running Zigbee2MQTT in Docker or on a separate machine from Home Assistant.

> If you're running Home Assistant, consider the [HA Add-on version](https://github.com/nickduvall921/mmwave_vis) instead — it integrates directly with the HA supervisor and requires no separate Docker setup. The Addon version is also updated before the docker version.

## **✨ Features**

- **📡 Live 2D Radar Tracking** — See up to 3 simultaneous targets in real-time with historical comet tails.
- **📏 Dynamic Zone Configuration** — Visually define detection room limits (Width, Depth, and Height).
- **🚫 Interference Management** — View, Auto-Config, and Clear interference zones to filter out fans, vents, and curtains.
- **🔄 Live Sensor Data** — Streams Global Occupancy and Illuminance states via MQTT.
- **🧱 Multi-Zone Support** — Configure up to 4 areas per zone type (requires recent Inovelli firmware & Z2M ≥ 2.8.0).
- **🔒 TLS/SSL Support** — Connect to brokers with TLS enabled, including support for custom CA certificates.
- **⚙ Persistent Configuration** — Save broker settings via the in-app config panel. No need to edit `docker-compose.yml` for every change.
- **✨ Vibe:** AI assisted in the design of this app.



## 🚀 Installation

### 1. Create a `docker-compose.yml`

```yaml
services:
  mmwave-visualizer:
    image: ghcr.io/nickduvall921/mmwave_vis_docker:main
    container_name: mmwave_vis
    ports:
      - "5000:5000"
    volumes:
      - ./mmwave_data:/data   # Persistent config storage
    environment:
      - MQTT_BROKER=192.168.1.XX   # Your MQTT broker IP
      - MQTT_PORT=1883
      - MQTT_USERNAME=your_user    # Optional
      - MQTT_PASSWORD=your_password # Optional
      - Z2M_BASE_TOPIC=zigbee2mqtt
    restart: unless-stopped
```

### 2. Start the container

```bash
docker-compose up -d
```

### 3. Open the UI

Navigate to `http://<your-ip>:5000` in your browser.

---

## ⚙️ Configuration

Configuration can be set two ways. The **in-app config panel** (click **⚙ Config** in the header) is the easiest — it saves settings to `/data/config.json` which persists across container restarts. Alternatively, use **environment variables** in your `docker-compose.yml`. The config file takes priority over ENV vars if both are present.

### All Options

| ENV Variable | Config File Key | Description | Default |
|---|---|---|---|
| `MQTT_BROKER` | `mqtt_broker` | IP or hostname of your MQTT broker | `localhost` |
| `MQTT_PORT` | `mqtt_port` | Broker port | `1883` |
| `MQTT_USERNAME` | `mqtt_username` | MQTT username | `""` |
| `MQTT_PASSWORD` | `mqtt_password` | MQTT password | `""` |
| `Z2M_BASE_TOPIC` | `mqtt_base_topic` | Zigbee2MQTT base topic | `zigbee2mqtt` |
| `MQTT_USE_TLS` | `mqtt_use_tls` | Enable TLS/SSL | `false` |
| `MQTT_TLS_INSECURE` | `mqtt_tls_insecure` | Skip certificate verification ⚠️ | `false` |
| `MQTT_TLS_CA_CERT` | `mqtt_tls_ca_cert` | Path to custom CA certificate file | `""` |

### TLS/SSL

To connect to a TLS-enabled broker (e.g. on port 8883):

```yaml
environment:
  - MQTT_BROKER=your-broker
  - MQTT_PORT=8883
  - MQTT_USE_TLS=true
```

If your broker uses a **self-signed certificate**, mount your CA cert and reference it:

```yaml
volumes:
  - ./mmwave_data:/data
  - ./ca.crt:/data/ca.crt   # Mount your CA cert

environment:
  - MQTT_USE_TLS=true
  - MQTT_TLS_CA_CERT=/data/ca.crt
```

> ⚠️ **`MQTT_TLS_INSECURE=true` disables all certificate verification.** Only use this on trusted local networks where you cannot provide a CA cert — it defeats the purpose of TLS.

---

## 🎚️ Inovelli Switch Setup

Before the visualizer can receive tracking data you need to configure the switch in Zigbee2MQTT:

1. Go to the switch's device page in Z2M → **Bind** tab.
2. In the Clusters dropdown, select `manuSpecificInovelliMMWave` and bind it from **Source endpoint 1** to your coordinator.
3. Go to the **Exposes** tab and enable **MmWaveTargetInfoReport**.

> 💡 Disable `MmWaveTargetInfoReport` when you don't need live tracking — it floods the Zigbee network whenever a target is detected.

---

## 🗺️ Usage Guide

1. **Select your switch** from the top-left dropdown. It populates as soon as the switch checks in via MQTT.
2. **Edit zones** using the Zone Editor sidebar:
   - Select a Target Zone (e.g. "Detection Area 1").
   - Click **Draw / Edit** — a draggable box appears on the radar map.
   - Drag the box or type exact coordinates (X/Y/Z) in the sidebar inputs.
   - Click **Apply Changes** to save to the switch.
   - Use **Force Sync** to reload current state from the switch if anything looks off.
3. **Adjust the map** via Visualizer Settings — hide zones, toggle labels, show Z (height) values, or resize the radar boundary.
4. **Auto-Config interference** — clear the room, turn on the interfering object (fan, vent, etc.), and click **Auto-Config Interference**. A red zone should appear if successful.

### Zone Types

| Zone | Colour | Purpose |
|---|---|---|
| Detection Area | Blue (Area 1) / Green (Areas 2–4) | Active sensor boundary. Motion outside this box is ignored entirely. |
| Interference Area | Red | Exclusion zone. Motion inside is discarded — use for fans, vents, curtains. |
| Stay Area | Orange | High-sensitivity zone for stationary presence (sofa, bed, desk). Keeps lights on even when barely moving. |

---

## Understanding Limitations

- **Radar persistence** — The switch does not send an "all clear" when motion stops. The last tracked object stays on the map indefinitely. Use the Occupancy status or packet age indicator to determine if the area is actually clear.
- **Network glitches** — On a slow Zigbee network, a zone edit may occasionally not reach the switch, causing the drawn zone to disappear. Use **Force Sync** to verify and retry if needed.
- **Known issue** — Stay areas invert width on apply. Simply reapply to fix. This appears to be a Z2M or firmware issue as it also occurs when configuring zones manually in Z2M.

---

## ⚠️ Requirements

- [Zigbee2MQTT v2.8.0 or higher](https://www.zigbee2mqtt.io/) (ZHA is not supported)
- At least one Inovelli mmWave Smart Switch
- Docker with Compose

---

## 🐛 Bugs & Contributing

Please open a GitHub issue if you run into problems. PRs are welcome — PR's might not be directly merged depending on the changes as I am often quite ahead of the github codebase.

---

## License

GNU General Public License v3.0