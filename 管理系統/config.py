import json
import os

CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config.json')

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "db_user": "postgres",
        "db_password": "",
        "db_host": "localhost",
        "db_port": "5432",
        "db_name": "stock_db"
    }

def save_config(config_data):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=4)
        
def get_db_uri():
    c = load_config()
    return f"postgresql://{c['db_user']}:{c['db_password']}@{c['db_host']}:{c['db_port']}/{c['db_name']}"
