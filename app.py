"""
Inovelli mmWave Visualizer Backend (Standalone Docker Version)
Provides a real-time MQTT-to-WebSocket bridge.
Handles device discovery, Zigbee byte array decoding, and two-way configuration.
"""

import json
import os
import traceback
import time
import threading 
from flask import Flask, render_template, request
from flask_socketio import SocketIO
import paho.mqtt.client as mqtt
import logging

# Suppress the Werkzeug development server warning
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# --- STANDALONE CONFIGURATION VIA ENVIRONMENT VARIABLES ---
# These replace the Home Assistant /data/options.json configuration
MQTT_BROKER = os.getenv('MQTT_BROKER', 'localhost')
MQTT_PORT = int(os.getenv('MQTT_PORT', 1883))
MQTT_USERNAME = os.getenv('MQTT_USERNAME', '')
MQTT_PASSWORD = os.getenv('MQTT_PASSWORD', '')
MQTT_BASE_TOPIC = os.getenv('Z2M_BASE_TOPIC', 'zigbee2mqtt')

# TLS/SSL Configuration
MQTT_USE_TLS = os.getenv('MQTT_USE_TLS', 'false').lower() == 'true'
MQTT_TLS_INSECURE = os.getenv('MQTT_TLS_INSECURE', 'false').lower() == 'true'  # Skip certificate verification

app = Flask(__name__)
# Standard SocketIO init for Docker environment
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

current_topic = None
device_list = {} 

def on_connect(client, userdata, flags, rc):
    print(f"Connected to MQTT Broker with code {rc}", flush=True)
    client.subscribe(f"{MQTT_BASE_TOPIC}/#")

def on_message(client, userdata, msg):
    global device_list
    try:
        topic = msg.topic
        payload_str = msg.payload.decode().strip()
        
        if not payload_str:
            return
            
        try:
            payload = json.loads(payload_str)
        except json.JSONDecodeError:
            return

        # --- DEVICE DISCOVERY ---
        if topic.startswith(MQTT_BASE_TOPIC):
            if "mmWaveVersion" in payload:
                parts = topic.split('/')
                if len(parts) >= 2:
                    friendly_name = parts[1]
                    
                    if friendly_name not in device_list:
                        print(f"Discovered Inovelli mmWave Switch: {friendly_name}", flush=True)
                        device_list[friendly_name] = {
                            'friendly_name': friendly_name, 
                            'topic': f"{MQTT_BASE_TOPIC}/{friendly_name}", 
                            'interference_zones': [],
                            'detection_zones': [],
                            'stay_zones': [],
                            'zone_config': {"x_min": -400, "x_max": 400, "y_min": 0, "y_max": 600},
                            'last_update': 0,
                            'last_seen': time.time()
                        }
                        socketio.emit('device_list', [d for d in device_list.values()])
                    else:
                        device_list[friendly_name]['last_seen'] = time.time()

        # --- CURRENT DEVICE PROCESSING ---
        fname = next((name for name, data in device_list.items() if topic.startswith(data['topic'])), None)
        if not fname: return
        
        device_topic = device_list[fname]['topic']

        # --- PROCESS RAW BYTES (ZCL Cluster 0xFC32) ---
        # Decodes the raw sensor packets for real-time tracking
        is_raw_packet = payload.get("0") == 29 and payload.get("1") == 47 and payload.get("2") == 18

        if is_raw_packet:
            cmd_id = payload.get("4")
            
            # 0x01: Target Info Reporting (Movement Data)
            if cmd_id == 1:
                current_time = time.time()
                if (current_time - device_list[fname].get('last_update', 0)) >= 0.1:
                    device_list[fname]['last_update'] = current_time
                    seq_num = payload.get("3")
                    num_targets = payload.get("5", 0)
                    targets = []
                    offset = 6

                    for _ in range(num_targets):
                        if str(offset+8) not in payload: break
                        
                        def parse_bytes(idx):
                            try:
                                low = int(payload.get(str(idx)) or 0)
                                high = int(payload.get(str(idx+1)) or 0)
                                return int.from_bytes([low, high], byteorder='little', signed=True)
                            except:
                                return 0

                        targets.append({
                            "id": int(payload.get(str(offset+8)) or 0),
                            "x": parse_bytes(offset),
                            "y": parse_bytes(offset+2),
                            "z": parse_bytes(offset+4),
                            "dop": parse_bytes(offset+6)
                        })
                        offset += 9
                    
                    socketio.emit('new_data', {'topic': device_topic, 'payload': {"seq": seq_num, "targets": targets}})

            # 0x02 (Interference), 0x03 (Detection), 0x04 (Stay) Areas
            elif cmd_id in [2, 3, 4]:
                try:
                    zones = []
                    offset = 6  
                    num_zones = payload.get("5", 0) 
                    
                    for _ in range(num_zones):
                        if str(offset+11) not in payload: break
                        
                        def parse_bytes(idx):
                            low = int(payload.get(str(idx)) or 0)
                            high = int(payload.get(str(idx+1)) or 0)
                            return int.from_bytes([low, high], byteorder='little', signed=True)

                        x_min = parse_bytes(offset)
                        x_max = parse_bytes(offset+2)
                        y_min = parse_bytes(offset+4)
                        y_max = parse_bytes(offset+6)
                        z_min = parse_bytes(offset+8)
                        z_max = parse_bytes(offset+10)
                        
                        if (x_max != 0 or x_min != 0 or y_max != 0 or y_min != 0):
                            zones.append({
                                "x_min": x_min, "x_max": x_max, 
                                "y_min": y_min, "y_max": y_max,
                                "z_min": z_min, "z_max": z_max
                            })
                        offset += 12
                    
                    if cmd_id == 2:
                        device_list[fname]['interference_zones'] = zones
                        socketio.emit('interference_zones', {'topic': device_topic, 'payload': zones})
                    elif cmd_id == 3:
                        device_list[fname]['detection_zones'] = zones
                        socketio.emit('detection_zones', {'topic': device_topic, 'payload': zones})
                    elif cmd_id == 4:
                        device_list[fname]['stay_zones'] = zones
                        socketio.emit('stay_zones', {'topic': device_topic, 'payload': zones})
                except Exception as parse_error:
                    print(f"Error parsing zone packet: {parse_error}", flush=True)
        
        # --- STANDARD STATE UPDATE ---
        config_payload = {k: v for k, v in payload.items() if not k.isdigit()}
        if config_payload:
            socketio.emit('device_config', {'topic': device_topic, 'payload': config_payload})

    except Exception as e:
        print(f"Error processing message: {e}", flush=True)
        traceback.print_exc()

# --- MQTT CLIENT SETUP ---
mqtt_client = mqtt.Client()

# Configure authentication
if MQTT_USERNAME and MQTT_PASSWORD:
    mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

# Configure TLS/SSL
if MQTT_USE_TLS:
    import ssl
    print(f"Configuring TLS/SSL for MQTT connection", flush=True)

    try:
        # Use system default certificates
        if MQTT_TLS_INSECURE:
            mqtt_client.tls_set(cert_reqs=ssl.CERT_NONE)
            mqtt_client.tls_insecure_set(True)
            print(f"WARNING: TLS certificate verification is DISABLED", flush=True)
        else:
            mqtt_client.tls_set()
            print(f"Using system default certificates", flush=True)

        print(f"TLS/SSL configuration successful", flush=True)
    except Exception as tls_error:
        print(f"TLS Configuration Error: {tls_error}", flush=True)
        traceback.print_exc()

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

try:
    print(f"Connecting to MQTT broker at {MQTT_BROKER}:{MQTT_PORT} (TLS: {MQTT_USE_TLS})", flush=True)
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_client.loop_start()
except Exception as e:
    print(f"MQTT Connection Failed: {e}", flush=True)
    traceback.print_exc()

# --- WEBSOCKET HANDLERS ---
@socketio.on('request_devices')
def handle_request_devices():
    socketio.emit('device_list', [d for d in device_list.values()])

@socketio.on('change_device')
def handle_change_device(new_topic):
    global current_topic
    current_topic = new_topic
    device_data = next((data for data in device_list.values() if data['topic'] == new_topic), None)
    if device_data:
        for zone_type in ['zone_config', 'interference_zones', 'detection_zones', 'stay_zones']:
            if zone_type in device_data:
                socketio.emit(zone_type, {'topic': new_topic, 'payload': device_data[zone_type]})

@socketio.on('update_parameter')
def handle_update_parameter(data):
    if not current_topic: return
    param = data.get('param')
    value = data.get('value')
    if isinstance(value, str) and value.lstrip('-').isnumeric():
        value = int(value)
    mqtt_client.publish(f"{current_topic}/set", json.dumps({param: value}))

@socketio.on('force_sync')
def handle_force_sync():
    if not current_topic: return
    # Standard Z2M attribute refresh
    payload = {"mmWaveVersion": "", "occupancy": "", "illuminance": ""}
    mqtt_client.publish(f"{current_topic}/get", json.dumps(payload))
    # Query specific mmWave areas
    mqtt_client.publish(f"{current_topic}/set", json.dumps({"mmwave_control_commands": {"controlID": "query_areas"}}))

@socketio.on('send_command')
def handle_command(cmd_action):
    if not current_topic: return
    action_map = {0: "reset_mmwave_module", 1: "set_interference", 2: "query_areas", 3: "clear_interference", 4: "reset_detection_area", 5: "clear_stay_areas"}
    cmd_string = action_map.get(int(cmd_action))
    if cmd_string:
        mqtt_client.publish(f"{current_topic}/set", json.dumps({"mmwave_control_commands": {"controlID": cmd_string}}))

@app.route('/')
def index():
    # Standing alone, ingress_path is set to empty string
    return render_template('index.html', ingress_path='')

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)