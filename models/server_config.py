import json
from typing import Optional, List, Dict, Any

WORDS_FILE = "words.txt"
MAX_ATTEMPTS = 6
MAX_HINTS = 3
DATA_FILE = "wordle_data.json"
CONFIG_FILE = "server_config.json"
SETTINGS_FILE = "user_settings.json"
DAILY_FILE = "daily_data.json"

class ServerConfig:
    def __init__(self):
        self.config = self.load_config()
    
    def load_config(self):
        try:
            with open(CONFIG_FILE) as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def save_config(self):
        with open(CONFIG_FILE, "w") as f:
            json.dump(self.config, f, indent=2)
    
    def set_wordle_channel(self, guild_id: int, channel_id: int):
        self.config[str(guild_id)] = channel_id
        self.save_config()
    
    def get_wordle_channel(self, guild_id: int) -> Optional[int]:
        return self.config.get(str(guild_id))