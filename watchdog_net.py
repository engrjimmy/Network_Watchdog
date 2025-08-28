from flask import Flask, Response, jsonify, render_template
import subprocess
import threading
import time
import os
from datetime import datetime
import logging
import yaml
import sys

# Initialize Flask app
app = Flask(__name__)

# Configuration
CONFIG_DIR = "config"
CONFIG_FILE = "ip_config_watchdog.yml"
config_path = os.path.join(CONFIG_DIR, CONFIG_FILE)

# Load configuration
def load_config():
    try:
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        print(f"Error: Configuration file '{config_path}' not found.")
        print(f"Please create a configuration file at '{config_path}'")
        print(f"See the README.md for configuration format and examples.")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error parsing configuration file: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error loading configuration: {e}")
        sys.exit(1)

# Load configuration
config = load_config()

# Setup logging
LOG_DIR = config["logging"]["directory"]
os.makedirs(LOG_DIR, exist_ok=True)

def get_log_filename():
    now = datetime.now()
    return now.strftime(config["logging"]["filename_format"])

# Get devices from config
devices = config["devices"]
device_groups = config.get("device_groups", {})

# Initialize status data
status_data = {
    name: {"reachable": False, "latency_ms": None} for name in devices
}

def ping_device(ip):
    """Ping once and return (reachable: bool, latency_ms: float or None)"""
    try:
        ping_timeout = config["monitoring"]["ping_timeout"]
        ping_count = config["monitoring"]["ping_count"]
        
        output = subprocess.check_output(
            ["ping", "-c", str(ping_count), "-W", str(ping_timeout), ip],
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        # Parse output for time=xxx ms
        for line in output.splitlines():
            if "time=" in line:
                time_ms = line.split("time=")[1].split()[0]
                return True, float(time_ms)
        return True, None  # reachable but no time parsed?
    except subprocess.CalledProcessError:
        return False, None

def update_status_loop():
    while True:
        start = time.time()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_file_path = os.path.join(LOG_DIR, get_log_filename())

        with open(log_file_path, "a") as log_file:
            for name, ip in devices.items():
                reachable, latency = ping_device(ip)
                status_data[name]["reachable"] = reachable
                status_data[name]["latency_ms"] = latency

                status_text = f"[{now_str}] {name} ({ip}) - {'Reachable' if reachable else 'Unreachable'}"
                if latency:
                    status_text += f", Latency: {latency:.2f} ms"

                log_file.write(status_text + "\n")

        # Sleep for the configured interval, but account for processing time
        ping_interval = config["monitoring"]["ping_interval"]
        time.sleep(max(0, ping_interval - (time.time() - start)))

def ping_stream(ip):
    proc = subprocess.Popen(
        ["ping", ip],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
    )
    for line in iter(proc.stdout.readline, ''):
        yield f"data: {line.strip()}\n\n"
        time.sleep(1)  # throttle slightly

@app.route("/")
def index():
    return render_template("index.html", devices=devices, device_groups=device_groups)

@app.route("/status")
def status():
    return jsonify(status_data)

@app.route("/ping_stream/<device_name>")
def ping_stream_route(device_name):
    ip = devices.get(device_name)
    if not ip:
        return "Invalid device name", 404
    return Response(ping_stream(ip), mimetype='text/event-stream')

@app.route("/config")
def get_config():
    """Return the current configuration (excluding sensitive data)"""
    # Create a copy of the config to avoid modifying the original
    safe_config = dict(config)
    
    # You could remove sensitive data here if needed
    # For example: del safe_config["some_sensitive_key"]
    
    return jsonify(safe_config)

if __name__ == "__main__":
    # Print startup information
    print("\n" + "="*50)
    print("Network Watchdog Starting")
    print("="*50)
    print(f"Monitoring {len(devices)} devices")
    print(f"Log directory: {LOG_DIR}")
    print(f"Server running at http://{config['server']['host']}:{config['server']['port']}")
    print("="*50 + "\n")
    
    # Start the monitoring thread
    threading.Thread(target=update_status_loop, daemon=True).start()
    
    # Start the Flask server
    app.run(
        host=config["server"]["host"], 
        port=config["server"]["port"], 
        debug=config["server"]["debug"],
        threaded=True
    )
