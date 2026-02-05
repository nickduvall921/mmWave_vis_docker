# **Inovelli mmWave Visualizer (Standalone Docker)**

**Live 2D presence tracking and interference zone configuration for Inovelli Smart Switches in Zigbee2MQTT.**

## **Overview**

This is the standalone Docker version of the Inovelli mmWave Visualizer. It decodes Zigbee2MQTT payloads to visualize real-time tracking data and allows you to configure detection, interference, and stay zones via a web UI. This version is ideal for users running Zigbee2MQTT in Docker or on a separate machine from Home Assistant.

## **✨ Features**

* **📡 Live 2D Radar Tracking:** See up to 3 simultaneous targets moving in real-time with historical comet tails.  
* **📏 Dynamic Zone Configuration:** Visually define your detection room limits (Width, Depth, and Height).  
* **🚫 Interference Management:** View, Auto-Config, and Clear interference zones directly from the UI to filter out moving fans, vents, and curtains.  
* **🔄 Live Sensor Data:** Streams Global Occupancy and Illuminance states via MQTT.  
* **🧱 Multi-Zone Support:** Configure up to 4 areas per zone type (Requires recent Inovelli Firmware & Z2M version).  
* **✨ Vibe:** AI assisted in the design of this app.

## **🚀 Installation (Via Docker Compose)**

1. **Create a docker-compose.yml file:**

services:  
  mmwave-visualizer:  
    image: ghcr.io/nickduvall921/mmwave\_vis\_docker:main  
    container\_name: mmwave\_vis  
    ports:  
      \- "5000:5000"  
    environment:  
      \- MQTT\_BROKER=192.168.1.50  \# \<--- Change to your MQTT Broker IP  
      \- MQTT\_PORT=1883  
      \- MQTT\_USERNAME=your\_user   \# \<--- Optional  
      \- MQTT\_PASSWORD=your\_pass   \# \<--- Optional  
      \- Z2M\_BASE\_TOPIC=zigbee2mqtt  
    restart: unless-stopped

2. **Run the container:**

docker-compose up \-d

3. **Open your browser:** Navigate to http://\<your-ip\>:5000.

## **⚙️ Configuration Variables**

| **Environment Variable** | **Description** | **Default** |

| MQTT\_BROKER | IP address or hostname of your MQTT Broker | localhost |

| MQTT\_PORT | The port your broker uses | 1883 |

| MQTT\_USERNAME | Your MQTT username | "" |

| MQTT\_PASSWORD | Your MQTT password | "" |

| Z2M\_BASE\_TOPIC | The base topic configured in Zigbee2MQTT | zigbee2mqtt |

## **🎚️ Configuration of Inovelli Switches**

To ensure the visualizer can receive tracking data:

1. **Bind the Cluster:** Go to the switch's device page in Z2M \-\> **Bind** tab.  
2. Bind manuSpecificInovelliMMWave from Source endpoint 1 to your coordinator.  
3. **Enable Reporting:** In the **Exposes** tab, enable MmWaveTargetInfoReport.  
   * *Note: It is recommended to disable this when not in use to reduce Zigbee network traffic.*

## **🚀 Usage Guide**

1. **Select Switch:** Use the top-left dropdown to select your device. It will populate as soon as the switch checks in via MQTT.  
2. **Edit Zones:**  
   * Open the **Zone Editor** sidebar.  
   * Select a Target Zone (e.g., "Detection Area 1").  
   * Click **Draw / Edit**.  
   * Drag the box on the map or type exact coordinates (including Height/Z-axis) in the sidebar.  
   * Click **Apply Changes** to save to the switch.  
3. **Map Settings:** Use Visualizer Settings to hide specific zones, toggle labels, or adjust the map boundaries.  

## **⚠️ Requirements**

* [Zigbee2MQTT V2.8.0 or higher](https://www.zigbee2mqtt.io/).  
* At least one Inovelli mmWave Smart Switch.

## **License**

GNU General Public License v3.0