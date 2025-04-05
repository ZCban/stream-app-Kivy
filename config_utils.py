import json
import os

CONFIG_FILE = "config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

def save_config(new_data):
    config = load_config()
    config.update(new_data)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)
