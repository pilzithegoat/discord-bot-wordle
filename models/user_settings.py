import json
import uuid
import bcrypt
from typing import Dict, Any
from utils.helpers import hash_password

WORDS_FILE = "words.txt"
MAX_ATTEMPTS = 6
MAX_HINTS = 3
DATA_FILE = "wordle_data.json"
CONFIG_FILE = "server_config.json"
SETTINGS_FILE = "user_settings.json"
DAILY_FILE = "daily_data.json"

class UserSettings:
    def __init__(self):
        self.settings = self.load_settings()
    
    def load_settings(self):
        try:
            with open(SETTINGS_FILE) as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def save_settings(self):
        with open(SETTINGS_FILE, "w") as f:
            json.dump(self.settings, f, indent=2)
    
    def get_settings(self, user_id: int) -> dict:
        default_settings = {
            "stats_public": True,
            "history_public": True,
            "anonymous": False,
            "anon_id": str(uuid.uuid4())[:8].upper(),
            "anon_password": None,
            "anon_games": []
        }
        user_id_str = str(user_id)
        
        if user_id_str not in self.settings:
            self.settings[user_id_str] = default_settings.copy()
            self.save_settings()
        else:
            for key in default_settings:
                if key not in self.settings[user_id_str]:
                    if key == "anon_id":
                        self.settings[user_id_str][key] = str(uuid.uuid4())[:8].upper()
                    else:
                        self.settings[user_id_str][key] = default_settings[key]
            self.save_settings()
        
        return self.settings[user_id_str].copy()
    
    def update_settings(self, user_id: int, **kwargs):
        user_id_str = str(user_id)
        self.get_settings(user_id)
        
        if 'anon_password' in kwargs and kwargs['anon_password']:
            kwargs['anon_password'] = hash_password(kwargs['anon_password'])
        
        valid_keys = ["stats_public", "history_public", "anonymous", 
                     "anon_id", "anon_password", "anon_games"]
        for key, value in kwargs.items():
            if key in valid_keys and key in self.settings[user_id_str]:
                self.settings[user_id_str][key] = value
        self.save_settings()
